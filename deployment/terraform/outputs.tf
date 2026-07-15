output "public_ip" {
  description = "The public IP address of the deployed EC2 server"
  value       = aws_instance.app_server.public_ip
}

output "s3_bucket_arn" {
  description = "The ARN of the assets storage bucket"
  value       = aws_s3_bucket.assets.arn
}

output "cloudwatch_log_group_arn" {
  description = "The ARN of the platform CloudWatch log group"
  value       = aws_cloudwatch_log_group.aates_logs.arn
}
