import pulumi
import pulumi_aws as aws
import sys
import os

# Python needs to link parent folder path to access modules in parent directory
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import vars

# Read back the default VPC and public subnets, which we will use.
default_vpc = aws.ec2.get_vpc(default=True)

# Get a list of all availability zones in the region
availability_zones = aws.get_availability_zones()

# Create two subnets in separate availability zones
default_subnet_1 = aws.ec2.Subnet("defaultSubnet1",
                                  vpc_id=default_vpc.id,
                                  cidr_block="10.0.1.0/24",
                                  availability_zone=availability_zones.names[0]) # First availability zone

default_subnet_2 = aws.ec2.Subnet("defaultSubnet2",
                                  vpc_id=default_vpc.id,
                                  cidr_block="10.0.2.0/24",
                                  availability_zone=availability_zones.names[1]) # Second availability zone

# Export the IDs of the created subnets
pulumi.export('default_subnet_1_id', default_subnet_1.id)
pulumi.export('default_subnet_2_id', default_subnet_2.id)

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

# Create a security group to control access to the database
security_group_db = aws.ec2.SecurityGroup("aurora_security_group",
                                          vpc_id=default_vpc.id,
                                          description="Allow access to Aurora Serverless v2",
                                          ingress=[{
                                              "protocol": "tcp",
                                              "from_port": 5432,  # PostgreSQL port
                                              "to_port": 5432,
                                              "cidr_blocks": ["0.0.0.0/0"],
                                          }])
