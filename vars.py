# ----------------------------------------------------- #
#                                                       #
#                  GLOBAL VARIABLES                     #
#                                                       #
# ----------------------------------------------------- #
project_name = "pulumi_infrastructure"
aws_id = '598479110370'
aws_user = 'pulumi'
aws_zone = 'eu-central-1'

# ----------------------------------------------------- #
#                                                       #
#                        DATABASE                       #
#                                                       #
# ----------------------------------------------------- #

database_name = "aurora"
database_cluster_name = f'{database_name}-cluster'
database_master_username = 'postgres'
database_master_password = '12345678'
database_port = 5432

# ----------------------------------------------------- #
#                                                       #
#                       AUDIOSYSTEM                     #
#                                                       #
# ----------------------------------------------------- #
audiosystem_service_name = 'audiosystem'
audiosystem_repository_name = audiosystem_service_name
audiosystem_container_name = audiosystem_service_name
audiosystem_container_port = 80
audiosystem_image_name = audiosystem_service_name

audiosystem_cluster_name = f'{audiosystem_service_name}-cluster'
audiosystem_db_name = f'{audiosystem_service_name}'
audiosystem_db_master_username = 'postgres'
audiosystem_db_master_password = '12345678'

audiosystem_bucket_id = f'{audiosystem_service_name}-bucket-unique-name'

# ----------------------------------------------------- #
#                                                       #
#                         EDNA                          #
#                                                       #
# ----------------------------------------------------- #
edna_service_name = 'edna'
edna_repository_name = edna_service_name
edna_container_name = edna_service_name
edna_container_port = 80
edna_image_name = edna_service_name

edna_cluster_name = f'{edna_service_name}-cluster'
edna_db_name = f'{edna_service_name}'
edna_db_master_username = 'postgres'
edna_db_master_password = '12345678'

edna_bucket_id = f'{edna_service_name}-bucket-unique-name'


# ----------------------------------------------------- #
#                                                       #
#                                                       #
#                                                       #
# ----------------------------------------------------- #
