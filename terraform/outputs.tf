output "alb_dns" {
  description = "ALB DNS name, for me I will add this as a CNAME for plate-tracker.arithman.dev in Cloudflare"
  value = aws_lb.api.dns_name
}

output "ecr_api_url" {
  description = "ECR repository URL for the API image"
  value = aws_ecr_repository.api.repository_url
}

output "ecr_worker_url" {
  description = "ECR repository URL for the worker image"
  value = aws_ecr_repository.worker.repository_url
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value = aws_db_instance.postgres.endpoint
  sensitive = true
}

output "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  value = aws_elasticache_cluster.redis.cache_nodes[0].address
  sensitive = true
}
