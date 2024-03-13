import pulumi
import pulumi_aws as aws
import sys
import os

import vpc

# Python needs to link parent folder path to access modules in parent directory
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import vars

# Create an AWS S3 Bucket with a custom identifier
s3_bucket = aws.s3.Bucket(vars.bucket_id,
                          bucket=vars.bucket_id)

# Create a VPC Endpoint for S3, this will route traffic within AWS Network
s3_endpoint = aws.ec2.VpcEndpoint("s3Endpoint",
                                  vpc_id=vpc.default_vpc.id,
                                  service_name=f'com.amazonaws.{vars.aws_zone}.s3',
                                  route_table_ids=[aws.ec2.get_route_table(vpc_id=vpc.default_vpc.id).id],
                                  subnet_ids=[vpc.default_vpc_subnets.ids])

# Create a Security Group that allows unlimited access only from the subnet
s3_security_group = aws.ec2.SecurityGroup("s3SecurityGroup",
                                          description="Allow unlimited access to S3 from within the subnet",
                                          vpc_id=vpc.default_vpc.id,
                                          ingress=[aws.ec2.SecurityGroupIngressArgs(
                                              protocol="-1",
                                              from_port=0,
                                              to_port=0,
                                              cidr_blocks=[aws.ec2.get_subnet(subnet_id=vpc.default_vpc_subnets.ids).cidr_block]
                                          )])

# Create a resource policy for the S3 bucket to enforce the restriction so that only the VPC endpoint can access it
s3_bucket_policy = aws.s3.BucketPolicy("s3BucketPolicy",
                                       bucket=s3_bucket.id,
                                       policy=s3_bucket.arn.apply(lambda arn: f"""
                                       {{
                                         "Version": "2012-10-17",
                                         "Statement": [
                                           {{
                                             "Effect": "Deny",
                                             "Principal": "*",
                                             "Action": "s3:*",
                                             "Resource": [
                                                "{arn}/*",
                                                "{arn}"
                                             ],
                                             "Condition": {{
                                                "StringNotEquals": {{
                                                    "aws:sourceVpce": "{s3_endpoint.id}"
                                                }}
                                             }}
                                           }}
                                         ]
                                       }}
                                       """))

# Export the URL of the bucket and the name of the security group
pulumi.export("bucket_url", s3_bucket.website_endpoint)
pulumi.export("security_group_name", s3_security_group.name)
