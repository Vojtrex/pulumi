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

# Create a load balancer to listen for HTTP traffic on port 80.
alb = aws.lb.LoadBalancer('app-lb',
                          security_groups=[vpc.group.id],
                          subnets=[vpc.default_subnet_1.id, vpc.default_subnet_2.id],
                          )

atg = aws.lb.TargetGroup('app-tg',
                         port=80,
                         protocol='HTTP',
                         target_type='ip',
                         vpc_id=vpc.default_vpc.id,
                         )

wl = aws.lb.Listener('web',
                     load_balancer_arn=alb.arn,
                     port=80,
                     default_actions=[aws.lb.ListenerDefaultActionArgs(
                         type='forward',
                         target_group_arn=atg.arn,
                     )],
                     )

pulumi.export('url', alb.dns_name)
