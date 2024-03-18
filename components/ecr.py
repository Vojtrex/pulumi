import json
import pulumi
import pulumi_aws as aws
import sys
import os

# Python needs to link parent folder path to access modules in parent directory
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import vars

# Create an AWS ECR Repository to store Docker images
repo = aws.ecr.Repository(
    vars.service_name,
    name=vars.repository_name,
    image_tag_mutability="MUTABLE"
)

# Output the repository URL
pulumi.export('repositoryUrl', repo.repository_url)
pulumi.export('repositoryName', repo.name)

# Define an IAM policy to control access to the ECR repository.
ecr_policy = {
    "Version": "2008-10-17",
    "Statement": [
        {
            "Sid": "AllowPushPull",
            "Effect": "Allow",
            "Principal": "*",  # or alternatively { "AWS": ["arn:aws:iam::awsAccountIdGoesHere:root"] }
            "Action": [
                "ecr:BatchCheckLayerAvailability",
                "ecr:BatchGetImage",
                "ecr:CompleteLayerUpload",
                "ecr:GetDownloadUrlForLayer",
                "ecr:InitiateLayerUpload",
                "ecr:PutImage",
                "ecr:UploadLayerPart"
            ]
        }
    ]
}

policy = aws.ecr.RepositoryPolicy("policy",
                                  repository=vars.repository_name,
                                  policy=pulumi.Output.from_input(ecr_policy).apply(lambda x: pulumi.Output.secret(x)),
                                  opts=pulumi.ResourceOptions(depends_on=[repo]),
                                  )

# The registry ID and repository URL are output by the program so they can be consumed by CI/CD pipelines.
pulumi.export('registryId', repo.registry_id)
