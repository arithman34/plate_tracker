# AWS infrastructure (portfolio reference)

Defines an ECS Fargate deployment (RDS, ElastiCache, ALB, ECR, S3) as an alternative to the
Railway/self-hosted deployments described in the root [README](../README.md). Not part of the
live deployment — kept here to show the AWS design.

```bash
terraform init
terraform apply
```

## Deploying to ECS

Once the stack is provisioned, build and push the images and roll the services:

```bash
aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.eu-west-2.amazonaws.com

docker build -f Dockerfile.api -t <account-id>.dkr.ecr.eu-west-2.amazonaws.com/plate-tracker-api:latest .
docker push <account-id>.dkr.ecr.eu-west-2.amazonaws.com/plate-tracker-api:latest

docker build -f Dockerfile.worker -t <account-id>.dkr.ecr.eu-west-2.amazonaws.com/plate-tracker-worker:latest .
docker push <account-id>.dkr.ecr.eu-west-2.amazonaws.com/plate-tracker-worker:latest

aws ecs update-service --cluster plate-tracker --service plate-tracker-api --force-new-deployment
aws ecs update-service --cluster plate-tracker --service plate-tracker-worker --force-new-deployment
```
