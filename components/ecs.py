from pulumi import export, ResourceOptions
import json
import pulumi
import pulumi_aws as aws

# Create an AWS ECR Repository to store Docker images
repo = aws.ecr.Repository("django")

# Output the repository URL
pulumi.export('repositoryUrl', repo.repository_url)


# Define an IAM policy to control access to the ECR repository.
def repository_policy(repo_url):
    return {
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "AllowPushPull",
            "Effect": "Allow",
            "Principal": "*",  # Specify the ARN of the IAM entity here
            "Action": [
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage",
                "ecr:BatchCheckLayerAvailability",
                "ecr:PutImage",
                "ecr:InitiateLayerUpload",
                "ecr:UploadLayerPart",
                "ecr:CompleteLayerUpload",
            ],
            "Resource": repo_url
        }]
    }


policy = aws.ecr.RepositoryPolicy("policy",
                                  repository=repo.name,
                                  policy=repo.repository_url.apply(
                                      lambda url: pulumi.Output.from_input(repository_policy(url)).apply(
                                          lambda policy: json.dumps(policy)))
                                  )

# The registry ID and repository URL are output by the program so they can be consumed by CI/CD pipelines.
pulumi.export('registryId', repo.registry_id)


# Create an ECS cluster to run a container-based service.
cluster = aws.ecs.Cluster('cluster')

# Read back the default VPC and public subnets, which we will use.
default_vpc = aws.ec2.get_vpc(default=True)
default_vpc_subnets = aws.ec2.get_subnets(
    filters = [
        aws.ec2.GetSubnetsFilterArgs(
            name='vpc-id',
            values=[default_vpc.id],
        ),
    ],
)

# Create a SecurityGroup that permits HTTP ingress and unrestricted egress.
group = aws.ec2.SecurityGroup('web-secgrp',
                              vpc_id=default_vpc.id,
                              description='Enable HTTP access',
                              ingress=[aws.ec2.SecurityGroupIngressArgs(
                                  protocol='tcp',
                                  from_port=80,
                                  to_port=80,
                                  cidr_blocks=['0.0.0.0/0'],
                              )],
                              egress=[aws.ec2.SecurityGroupEgressArgs(
                                  protocol='-1',
                                  from_port=0,
                                  to_port=0,
                                  cidr_blocks=['0.0.0.0/0'],
                              )],
                              )

# Create a load balancer to listen for HTTP traffic on port 80.
alb = aws.lb.LoadBalancer('app-lb',
                          security_groups=[group.id],
                          subnets=default_vpc_subnets.ids,
                          )

atg = aws.lb.TargetGroup('app-tg',
                         port=80,
                         protocol='HTTP',
                         target_type='ip',
                         vpc_id=default_vpc.id,
                         )

wl = aws.lb.Listener('web',
                     load_balancer_arn=alb.arn,
                     port=80,
                     default_actions=[aws.lb.ListenerDefaultActionArgs(
                         type='forward',
                         target_group_arn=atg.arn,
                     )],
                     )

# Create an IAM role that can be used by our service's task.
role = aws.iam.Role('task-exec-role',
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

rpa = aws.iam.RolePolicyAttachment('task-exec-policy',
                                   role=role.name,
                                   policy_arn='arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy',
                                   )



# Spin up a load balanced service running our container image.
task_definition = aws.ecs.TaskDefinition('app-task',
                                         family='fargate-task-definition',
                                         cpu='256',
                                         memory='512',
                                         network_mode='awsvpc',
                                         requires_compatibilities=['FARGATE'],
                                         execution_role_arn=role.arn,
                                         container_definitions=json.dumps([{
                                             'name': 'django_test',
                                             'image': f'{repo.name}:latest',
                                             'portMappings': [{
                                                 'containerPort': 80,
                                                 'hostPort': 80,
                                                 'protocol': 'tcp'
                                             }]
                                         }])
                                         )

service = aws.ecs.Service('app-svc',
                          cluster=cluster.arn,
                          desired_count=3,
                          launch_type='FARGATE',
                          task_definition=task_definition.arn,
                          network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
                              assign_public_ip=True,
                              subnets=default_vpc_subnets.ids,
                              security_groups=[group.id],
                          ),
                          load_balancers=[aws.ecs.ServiceLoadBalancerArgs(
                              target_group_arn=atg.arn,
                              container_name='my-app',
                              container_port=80,
                          )],
                          opts=ResourceOptions(depends_on=[wl]),
                          )

export('url', alb.dns_name)