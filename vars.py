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
#                       DJANGO                          #
#                                                       #
# ----------------------------------------------------- #
service_name = 'django'
repository_name = service_name
container_name = service_name
container_port = 80
image_name = service_name

cluster_name = f'{service_name}-cluster'
db_name = f'{service_name}-db'
db_master_username = 'postgres'
db_master_password = '1234'

bucket_id = f'{service_name}-bucket-unique-name'

# ----------------------------------------------------- #
#                                                       #
#                                                       #
#                                                       #
# ----------------------------------------------------- #