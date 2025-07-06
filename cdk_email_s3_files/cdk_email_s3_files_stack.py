from aws_cdk import (
    Duration,
    Stack,
    aws_s3 as s3,
    aws_ses as ses,
    aws_iam as iam,
    aws_ecr as ecr,
    aws_lambda as _lambda,
    aws_s3_notifications as s3_notifications
    # aws_sqs as sqs,
)
from constructs import Construct

class CdkEmailS3FilesStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        image_exists = self.node.try_get_context("image_exists") == "1"
        # Bucket name specified in cdk.json context
        bucket_name = self.node.try_get_context("bucketName")

        # Reference an existing bucket by name
        #bucket = s3.Bucket.from_bucket_name(self, "ExistingBucket", bucket_name)
        bucket = s3.Bucket(self, "MyBucket",
         bucket_name=bucket_name,
         lifecycle_rules=[ s3.LifecycleRule( expiration=Duration.days(5)) ])

        # ECR Repository (where Docker image is stored)
        # repository = ecr.Repository.from_repository_name(self, "MyLambdaRepo", "lambda_support_s3_bucket_emails")

        repository = ecr.Repository(self, "MyEcrRepo",
            repository_name="email-file-attachments-auto",
            lifecycle_rules=[ ecr.LifecycleRule( 
                rule_priority=1,
                description="Keep only the most recent untagged image",
                tag_status=ecr.TagStatus.UNTAGGED,
                max_image_count=1  # Only the most recent untagged image will be retained
                ) ]) 

        if image_exists:
            lambda_function = _lambda.DockerImageFunction(self, "MyLambdaFunction",
                                              function_name="email-file-attachments-auto",
                                              code=_lambda.DockerImageCode.from_ecr(repository, tag="latest"),
                                              memory_size=1024,
                                              timeout=Duration.seconds(60),
                                              environment={
                                                  "BUCKET_NAME": bucket.bucket_name
                                              })

            lambda_function.role.add_to_policy(
                    iam.PolicyStatement( actions=["ses:*", "s3:*"],
                                         resources=[ bucket.bucket_arn, f"{bucket.bucket_arn}/*"]))

            # Set up S3 event notification to trigger Lambda on object creation in a specific "folder"
            bucket.add_event_notification(
                s3.EventType.OBJECT_CREATED,  # Trigger on object creation
                s3_notifications.LambdaDestination(lambda_function)
            )