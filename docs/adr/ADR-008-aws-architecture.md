# ADR-008: AWS Deployment Strategy (Free Tier Focused)

## Status
Approved

## Context
AATES must run in a cost-efficient manner in AWS (Free Tier) during initial phases, but prepare for future scaling.

## Decision
Deploy the modular monolith using Docker Compose on a single AWS EC2 instance. Provision infrastructure via Terraform. Use Amazon S3 for media asset storage, and CloudWatch for logs.

## Alternatives
- **AWS ECS / EKS**: Rejected for initial phase due to cost.
- **Serverless (Lambda)**: Rejected due to execution time limits of video generation rendering pipelines.

## Consequences
- Zero or low running cost.
- Easy migration to ECS later as the Docker containers are already standard.

## Future Migration Path
Migrate the dockerized containers to ECS/Fargate when traffic or workloads scale.
