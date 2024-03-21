import json
import pulumi
import pulumi_aws as aws
import sys
import os

from components import vpc

# Python needs to link parent folder path to access modules in parent directory
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import vars

# ----------------------------------------------------- #
#                                                       #
#                          ECR                          #
#                                                       #
# ----------------------------------------------------- #

# Create an AWS ECR Repository to store Docker images
ecr_repository = aws.ecr.Repository(
    f"{vars.audiosystem_service_name}_ecr_repository",
    name=vars.audiosystem_repository_name,
    image_tag_mutability="MUTABLE"
)

# Output the repository URL
pulumi.export(f"{vars.audiosystem_service_name}_repositoryUrl", ecr_repository.repository_url)
pulumi.export(f"{vars.audiosystem_service_name}_repositoryName", ecr_repository.name)

# Define an IAM policy to control access to the ECR repository.
ecr_policy_json = {
    "Version": "2008-10-17",
    "Statement": [
        {
            "Sid": "AllowPushPull",
            "Effect": "Allow",
            "Principal": "*",  # or alternatively { "AWS": ["arn:aws:iam::awsAccountIdGoesHere:root"] }
            "Action": [
                "ecr:GetAuthorizationToken",
                "ecr:BatchCheckLayerAvailability",
                "ecr:BatchGetImage",
                "ecr:CompleteLayerUpload",
                "ecr:GetDownloadUrlForLayer",
                "ecr:InitiateLayerUpload",
                "ecr:PutImage",
                "ecr:UploadLayerPart"
            ]
        }
    ]
}

ecr_policy = aws.ecr.RepositoryPolicy(f"{vars.audiosystem_service_name}_ecr_policy",
                                      repository=vars.audiosystem_repository_name,
                                      policy=pulumi.Output.from_input(ecr_policy_json).apply(
                                          lambda x: pulumi.Output.secret(x)),
                                      opts=pulumi.ResourceOptions(depends_on=[ecr_repository]),
                                      )

# The registry ID and repository URL are output by the program so they can be consumed by CI/CD pipelines.
pulumi.export(f"{vars.audiosystem_service_name}_registryId", ecr_repository.registry_id)

# ----------------------------------------------------- #
#                                                       #
#                     Loadbalancer                      #
#                                                       #
# ----------------------------------------------------- #

# Create a load balancer to listen for HTTP traffic on port 80.
loadbalancer = aws.lb.LoadBalancer(f"{vars.audiosystem_service_name}_loadbalancer",
                                   name=f"{vars.audiosystem_service_name}-loadbalancer",
                                   security_groups=[vpc.security_group_allow_all_traffic.id],
                                   subnets=[vpc.default_subnet_1.id, vpc.default_subnet_2.id, vpc.default_subnet_3.id],
                                   )

# Loadbalancer Target Group
target_group = aws.lb.TargetGroup(f"{vars.audiosystem_service_name}_target_group",
                                  name=f"{vars.audiosystem_service_name}-target-group",
                                  port=80,
                                  protocol='HTTP',
                                  target_type='ip',
                                  vpc_id=vpc.default_vpc.id,
                                  health_check={
                                      'path': '/',
                                      'port': 80,
                                      'protocol': 'HTTP',
                                      'healthy_threshold': 2,
                                      'unhealthy_threshold': 8,
                                      'timeout': 5,
                                      'interval': 30,

                                  }
                                  )

# HTTP listener
listener = aws.lb.Listener(f"{vars.audiosystem_service_name}_listener",
                           load_balancer_arn=loadbalancer.arn,
                           port=80,
                           default_actions=[aws.lb.ListenerDefaultActionArgs(
                               type='forward',
                               target_group_arn=target_group.arn,

                           )],
                           )

# Redirect action
listener_rule_redirect_to_https = aws.lb.ListenerRule(
    f"{vars.audiosystem_service_name}_listener_rule_redirect_to_https",
    listener_arn=listener.arn,
    actions=[aws.lb.ListenerRuleActionArgs(
        type="redirect",
        redirect=aws.lb.ListenerRuleActionRedirectArgs(
            port="443",
            protocol="HTTPS",
            status_code="HTTP_301",
        ),
    )],
    conditions=[aws.lb.ListenerRuleConditionArgs(
        path_pattern=aws.lb.ListenerRuleConditionPathPatternArgs(
            values=["/*"]  # Match all paths
        ),
    )],
    priority=100
)

# Fixed-response action
listener_rule_health_check = aws.lb.ListenerRule(f"{vars.audiosystem_service_name}_listener_rule_health_check",
                                                 listener_arn=listener.arn,
                                                 actions=[aws.lb.ListenerRuleActionArgs(
                                                     type="fixed-response",
                                                     fixed_response=aws.lb.ListenerRuleActionFixedResponseArgs(
                                                         content_type="text/plain",
                                                         message_body="HEALTHY",
                                                         status_code="200",
                                                     ),
                                                 )],
                                                 conditions=[aws.lb.ListenerRuleConditionArgs(
                                                     query_strings=[
                                                         aws.lb.ListenerRuleConditionQueryStringArgs(
                                                             key="health",
                                                             value="check",
                                                         ),
                                                         aws.lb.ListenerRuleConditionQueryStringArgs(
                                                             value="bar",
                                                         ),
                                                     ],
                                                 )])

pulumi.export(f"{vars.audiosystem_service_name}_url", loadbalancer.dns_name)

# ----------------------------------------------------- #
#                                                       #
#                           ECS                         #
#                                                       #
# ----------------------------------------------------- #


# Create an ECS cluster to run a container-based service.
ecs_cluster = aws.ecs.Cluster(f"{vars.audiosystem_service_name}_ecs_cluster")

# Create an IAM role that can be used by our service's task.
iam_role_ecs_task_exec_role = aws.iam.Role(f"{vars.audiosystem_service_name}_iam_role_ecs_task_exec_role",
                                           assume_role_policy=json.dumps({
                                               'Version': '2008-10-17',
                                               'Statement': [{
                                                   'Sid': '',
                                                   'Effect': 'Allow',
                                                   'Principal': {
                                                       'Service': 'ecs-tasks.amazonaws.com'
                                                   },
                                                   'Action': 'sts:AssumeRole',
                                               }]
                                           }),
                                           )

default_task_execution_policy = aws.iam.Policy("defaultTaskExecutionPolicy",
                                               description="Default Fargate Task Execution Policy",
                                               policy="""{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogStream",
                    "logs:CreateLogGroup",
                    "logs:PutLogEvents",
                    "ecs:ListTasks",
                    "ecs:DescribeTasks",
                    "ecs:StartTask",
                    "ecs:StopTask",
                    "ecr:GetAuthorizationToken"
                ],
                "Resource": "*"
            }
        ]
    }"""
                                               )

# Attach the policy to the ECS task execution role
ecr_policy_attachment = aws.iam.RolePolicyAttachment("ecrPolicyAttachment",
                                                     policy_arn=default_task_execution_policy.arn,
                                                     role=iam_role_ecs_task_exec_role.name
                                                     )

# Define the container definitions with the ECR image URI
container_definitions = pulumi.Output.all(ecr_repository.repository_url).apply(lambda args: json.dumps([{
    'name': vars.audiosystem_container_name,
    'image': f"{args[0]}:latest",
    'cpu': 1024,
    'memory': 2048,
    'essential': True,
    'portMappings': [{
        'containerPort': vars.audiosystem_container_port,
        'hostPort': vars.audiosystem_container_port,
        'protocol': 'tcp'
    }],
    "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:80/ || exit 1"],
        "interval": 20,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 10
    }
}]))

# Spin up a load balanced service running our container image.
task_definition = aws.ecs.TaskDefinition(f"{vars.audiosystem_service_name}_task_definition",
                                         family=vars.audiosystem_service_name,
                                         cpu='1024',
                                         memory='2048',
                                         network_mode='awsvpc',
                                         requires_compatibilities=['FARGATE'],
                                         execution_role_arn=iam_role_ecs_task_exec_role.arn,
                                         container_definitions=container_definitions,
                                         )
# Create an ECS service
ecs_service = aws.ecs.Service(f"{vars.audiosystem_service_name}_ecs_service",
                              cluster=ecs_cluster.arn,
                              desired_count=1,
                              launch_type='FARGATE',
                              task_definition=task_definition.arn,
                              network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
                                  assign_public_ip=True,
                                  subnets=[vpc.default_subnet_1.id, vpc.default_subnet_2.id, vpc.default_subnet_3.id],
                                  security_groups=[vpc.security_group_allow_all_traffic.id],
                              ),
                              load_balancers=[aws.ecs.ServiceLoadBalancerArgs(
                                  target_group_arn=target_group.arn,
                                  container_name=vars.audiosystem_container_name,
                                  container_port=vars.audiosystem_container_port,
                              )],
                              opts=pulumi.ResourceOptions(depends_on=[listener]),
                              )

# ----------------------------------------------------- #
#                                                       #
#                       S3 Bucket                       #
#                                                       #
# ----------------------------------------------------- #

# Create an AWS S3 Bucket with a custom identifier
s3_bucket = aws.s3.Bucket(f"{vars.audiosystem_service_name}_s3_bucket",
                          bucket=vars.audiosystem_bucket_id)

# Create a VPC Endpoint for S3, this will route traffic within AWS Network
s3_endpoint = aws.ec2.VpcEndpoint(f"{vars.audiosystem_service_name}_s3_endpoint",
                                  vpc_id=vpc.default_vpc.id,
                                  service_name=f'com.amazonaws.{vars.aws_zone}.s3',
                                  route_table_ids=[aws.ec2.get_route_table(vpc_id=vpc.default_vpc.id).id])

# Create a Security Group that allows unlimited access only from the subnet
s3_security_group = aws.ec2.SecurityGroup(f"{vars.audiosystem_service_name}_s3_security_group",
                                          description="Allow unlimited access to S3 from within the subnet",
                                          vpc_id=vpc.default_vpc.id,
                                          ingress=[aws.ec2.SecurityGroupIngressArgs(
                                              protocol="-1",
                                              from_port=0,
                                              to_port=0,
                                              cidr_blocks=[vpc.default_subnet_1.cidr_block,
                                                           vpc.default_subnet_2.cidr_block,
                                                           vpc.default_subnet_3.cidr_block,
                                                           ]
                                          )])


# Create a resource policy for the S3 bucket to enforce the restriction so that only the VPC endpoint can access it
def internal_policy_for_bucket(bucket_name):
    return pulumi.Output.json_dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Deny",
            "Principal": "*",
            "Action": [
                "s3:*"
            ],
            "Resource": [
                pulumi.Output.format("arn:aws:s3:::{0}/*", bucket_name),
            ],
            "Condition": {
                "StringNotEquals": {
                    "aws:sourceVpce": "{s3_endpoint.id}"
                }
            }
        }]
    })


# Attaching the policy to the bucket
s3_bucket_policy = aws.s3.BucketPolicy(f"{vars.audiosystem_service_name}_s3_bucket_policy",
                                       bucket=s3_bucket.id,
                                       policy=internal_policy_for_bucket(s3_bucket.id))

# Export the URL of the bucket and the name of the security group
pulumi.export("s3_bucket_endpoint", pulumi.Output.concat("https://", bucket.bucket, ".s3.amazonaws.com")
pulumi.export("s3_security_group_name", s3_security_group.name)
