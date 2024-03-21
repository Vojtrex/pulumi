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

# Get all subnets in the default VPC
subnets = aws.ec2.get_subnets(filters=[{"name": "vpc-id", "values": [default_vpc.id]}])

# Retrieve the existing subnet information for the first three subnets
default_subnet_1 = aws.ec2.Subnet.get("default_subnet_1", subnets.ids[0])
default_subnet_2 = aws.ec2.Subnet.get("default_subnet_2", subnets.ids[1])
default_subnet_3 = aws.ec2.Subnet.get("default_subnet_3", subnets.ids[2])

# Get a list of all availability zones in the region
availability_zones = aws.get_availability_zones()
pulumi.export('availability_zones', availability_zones.names)

# Export the IDs of the default subnets
pulumi.export('default_subnet_1_id', default_subnet_1.id)
pulumi.export('default_subnet_2_id', default_subnet_2.id)
pulumi.export('default_subnet_3_id', default_subnet_3.id)

# Create a SecurityGroup that permits HTTP ingress and unrestricted egress.
security_group_allow_all_traffic = aws.ec2.SecurityGroup('vpc_security_group_allow_all_traffic',
                                                         vpc_id=default_vpc.id,
                                                         description='Enable HTTP and HTTPS access',
                                                         ingress=[aws.ec2.SecurityGroupIngressArgs(
                                                             protocol='tcp',
                                                             from_port=80,
                                                             to_port=80,
                                                             cidr_blocks=['0.0.0.0/0'],
                                                         ),
                                                             aws.ec2.SecurityGroupIngressArgs(
                                                                 protocol='tcp',
                                                                 from_port=443,
                                                                 to_port=443,
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
