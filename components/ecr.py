import json
import pulumi
import pulumi_aws as aws

# Create an AWS ECR Repository to store Docker images
repo = aws.ecr.Repository("django")

# Output the repository URL
pulumi.export('repositoryUrl', repo.repository_url)


# Define an IAM policy to control access to the ECR repository.
def repository_policy(repo_url):
    return {
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "AllowPushPull",
            "Effect": "Allow",
            "Principal": "*",  # Specify the ARN of the IAM entity here
            "Action": [
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage",
                "ecr:BatchCheckLayerAvailability",
                "ecr:PutImage",
                "ecr:InitiateLayerUpload",
                "ecr:UploadLayerPart",
                "ecr:CompleteLayerUpload",
            ],
            "Resource": repo_url
        }]
    }


policy = aws.ecr.RepositoryPolicy("policy",
                                  repository=repo.name,
                                  policy=repo.repository_url.apply(
                                      lambda url: pulumi.Output.from_input(repository_policy(url)).apply(
                                          lambda policy: json.dumps(policy)))
                                  )

# The registry ID and repository URL are output by the program so they can be consumed by CI/CD pipelines.
pulumi.export('registryId', repo.registry_id)
