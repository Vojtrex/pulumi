# ----------------------------------------------------- #
#                                                       #
#                  GLOBAL VARIABLES                     #
#                                                       #
# ----------------------------------------------------- #
project_name = "pulumi_infrastructure"
aws_id = '598479110370'
aws_user = 'pulumi'
aws_zone = 'eu-central-1'
aws_availiability_zone_a = f'{aws_zone}a'
aws_availiability_zone_b = f'{aws_zone}b'

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

db_name = f'{service_name}-db'
db_master_username = 'postgres'
db_master_password = '1234'

# ----------------------------------------------------- #
#                                                       #
#                                                       #
#                                                       #
# ----------------------------------------------------- #