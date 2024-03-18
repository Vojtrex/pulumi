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

# Create the Aurora Serverless v2 cluster 
aurora_cluster = aws.rds.Cluster("aurora_cluster",
                                 cluster_identifier=vars.cluster_name,
                                 engine="aurora-postgresql",
                                 engine_mode='provisioned',
                                 engine_version="13.6",
                                 database_name=vars.db_name,
                                 master_username=vars.db_master_username,
                                 master_password=vars.db_master_password,
                                 storage_encrypted=True,
                                 vpc_security_group_ids=[vpc.security_group_db.id],
                                 serverlessv2_scaling_configuration=aws.rds.ClusterServerlessv2ScalingConfigurationArgs(
                                     min_capacity=0.5,
                                     max_capacity=1,
                                 ))

aurora_cluster_instance = aws.rds.ClusterInstance("aurora_cluster_instance",
                                                  cluster_identifier=aurora_cluster.id,
                                                  instance_class="db.serverless",
                                                  engine=aurora_cluster.engine,
                                                  engine_version=aurora_cluster.engine_version
                                                  )

# Export the cluster endpoint to allow connections to the database
pulumi.export("cluster_endpoint", aurora_cluster.endpoint)
