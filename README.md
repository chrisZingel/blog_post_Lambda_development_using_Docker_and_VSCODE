# Developing AWS Lambda with Docker & VS Code
This guide outlines how to develop and deploy AWS Lambda functions using Docker and Visual Studio Code, providing a consistent local environment that closely matches the AWS Lambda runtime.

This project sets up an AWS architecture using the AWS CDK that includes:

- An Elastic Container Registry (ECR) repository configured with mutable image tags with a lifecycle policy to automatically clean up untagged images and manage storage costs.
- S3 bucket to receive incoming files.
- AWS Lambda function, built from a Docker image stored in ECR, that automatically emails you any files uploaded to the S3 bucket.

This setup provides a simple and effective way to monitor incoming files via email, making it especially useful for lightweight reporting or quick notifications during development and testing.

If you are running CDK within the VSCODE container. You will need to execute the following in the terminal

```bash
dnf install npm
npm install -g aws-cdk
pip install -r requirements-dev.txt
```

cdk.json

{
  "context": {
    "env": "dev",
    "bucketName": "my-bucket-dev"
  }
}

## Running CDK
The Lambda function requires an existing Docker image tagged as current. However, when the resources are first created, the Docker image hasn’t yet been added to the Elastic Container Registry (ECR).

To handle this, I pass a parameter indicating whether the Docker image has been uploaded to the registry. If it hasn’t, CDK will create the ECR repository but not the Lambda function. Once the Docker image is uploaded, the full CDK deployment can be run to complete the setup.

In case you’re wondering why I didn’t check for the image within CDK: CDK is declarative — it defines the desired infrastructure state and does not allow AWS API calls (like checking ECR for an image) during synthesis.

### First run:
```
cdk deploy --context image_exists=0

```
#### Subsequent runs (after the Docker image has been pushed):

```
cdk deploy --context image_exists=1
```