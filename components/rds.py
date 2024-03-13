import pulumi
import pulumi_aws as aws
import pulumi_aws_native as aws_native
import sys
import os

from components import vpc

# Python needs to link parent folder path to access modules in parent directory
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import vars

# Create the Aurora Serverless v2 cluster using the AWS-native provider which uses the AWS Cloud Control API
aurora_cluster = aws_native.rds.DbCluster("aurora_cluster",
                                          engine="aurora-postgresql",
                                          database_name=vars.db_name,
                                          master_username=vars.db_master_username,
                                          master_user_password=vars.db_master_password,
                                          availability_zones=[aws_availiability_zone_a, aws_availiability_zone_b],
                                          db_subnet_group_name=vpc.group.name,
                                          vpc_security_group_ids=[vpc.security_group_db.id],
                                          # ServerlessV2 configuration specifying min and max capacity
                                          serverless_v2_scaling_configuration={
                                              "min_capacity": 0.5, # Aurora Serverless v2 allows for more granularity in capacity settings
                                              "max_capacity": 64  # Adjust the max capacity based on your needs
                                          })

# Export the cluster endpoint to allow connections to the database
pulumi.export("cluster_endpoint", aurora_cluster.endpoint)
