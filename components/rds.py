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
aurora_cluster = aws.rds.Cluster(f"{vars.database_cluster_name}_aurora_cluster",
                                 cluster_identifier=vars.database_cluster_name,
                                 engine="aurora-postgresql",
                                 engine_mode='provisioned',
                                 engine_version="16.1",
                                 database_name=vars.database_name,
                                 master_username=vars.database_master_username,
                                 master_password=vars.database_master_password,
                                 storage_encrypted=True,
                                 vpc_security_group_ids=[vpc.security_group_db.id],
                                 skip_final_snapshot=True,
                                 serverlessv2_scaling_configuration=aws.rds.ClusterServerlessv2ScalingConfigurationArgs(
                                     min_capacity=0.5,
                                     max_capacity=1,
                                 ))

# Create a Aurora Cluster Instance
aurora_cluster_instance = aws.rds.ClusterInstance(f"{vars.database_cluster_name}_aurora_cluster_instance",
                                                  cluster_identifier=aurora_cluster.id,
                                                  instance_class="db.serverless",
                                                  engine=aurora_cluster.engine,
                                                  engine_version=aurora_cluster.engine_version,
                                                  publicly_accessible=True,
                                                  )

# Export the cluster endpoint to allow connections to the database
pulumi.export(f"{vars.database_cluster_name}_cluster_endpoint", aurora_cluster.endpoint)
