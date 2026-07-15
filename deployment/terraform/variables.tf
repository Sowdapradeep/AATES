variable "aws_region" {
  description = "AWS region for resources deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Target environment stage"
  type        = string
  default     = "production"
}

variable "instance_type" {
  description = "EC2 instance size targeting free-tier limits"
  type        = string
  default     = "t2.micro"
}

variable "key_name" {
  description = "SSH keypair name to allow EC2 host access"
  type        = string
  default     = "aates-key"
}

variable "bucket_name" {
  description = "Unique identifier name for Amazon S3 assets storage"
  type        = string
  default     = "aates-assets-production-7788"
}
