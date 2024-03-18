import pulumi
import pulumi_aws as aws
import json
import sys
import os

from components import vpc
from components import loadbalancer


# Python needs to link parent folder path to access modules in parent directory
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import vars

# Create an ECS cluster to run a container-based service.
cluster = aws.ecs.Cluster('cluster')

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
                                         family=vars.service_name,
                                         cpu='1024',
                                         memory='2048',
                                         network_mode='awsvpc',
                                         requires_compatibilities=['FARGATE'],
                                         execution_role_arn=role.arn,
                                         container_definitions=json.dumps([{
                                             'name': vars.container_name,
                                             'image': vars.image_name,
                                             'cpu': 1024,
                                             'memory': 2048,
                                             'essential': True,
                                             'portMappings': [{
                                                 'containerPort': vars.container_port,
                                                 'hostPort': vars.container_port,
                                                 'protocol': 'tcp'
                                             }]
                                         }])
                                         )

service = aws.ecs.Service('app-svc',
                          cluster=cluster.arn,
                          desired_count=1,
                          launch_type='FARGATE',
                          task_definition=task_definition.arn,
                          network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
                              assign_public_ip=True,
                              subnets=[vpc.default_subnet_1.id, vpc.default_subnet_2.id],
                              security_groups=[vpc.group.id],
                          ),
                          load_balancers=[aws.ecs.ServiceLoadBalancerArgs(
                              target_group_arn=loadbalancer.atg.arn,
                              container_name=vars.container_name,
                              container_port=vars.container_port,
                          )],
                          opts=pulumi.ResourceOptions(depends_on=[loadbalancer.wl]),
                          )

