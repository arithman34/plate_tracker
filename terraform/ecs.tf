resource "aws_ecs_cluster" "main" {
  name = var.project
}

resource "aws_cloudwatch_log_group" "api" {
  name = "/ecs/${var.project}-api"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "worker" {
  name = "/ecs/${var.project}-worker"
  retention_in_days = 7
}

locals {
  db_url    = "postgresql+asyncpg://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.endpoint}/plate_tracker"
  redis_url = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:6379/0"

  common_env = [
    { name = "DATABASE_URL", value = local.db_url },
    { name = "REDIS_URL", value = local.redis_url },
    { name = "POSTGRES_USER", value = var.db_username },
    { name = "POSTGRES_PASSWORD", value = var.db_password },
    { name = "POSTGRES_DB", value = "plate_tracker" },
    { name = "S3_BUCKET", value = aws_s3_bucket.media.id },
    { name = "AWS_REGION", value = var.aws_region },
  ]
}

resource "aws_ecs_task_definition" "api" {
  family = "${var.project}-api"
  network_mode = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu = 256
  memory = 512
  execution_role_arn = aws_iam_role.ecs_execution.arn
  task_role_arn = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name = "api"
    image = "${aws_ecr_repository.api.repository_url}:latest"
    portMappings = [{ containerPort = 8000, protocol = "tcp" }]
    environment = local.common_env
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group = aws_cloudwatch_log_group.api.name
        awslogs-region = var.aws_region
        awslogs-stream-prefix = "api"
      }
    }
  }])
}

resource "aws_ecs_task_definition" "worker" {
  family = "${var.project}-worker"
  network_mode = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu = 512
  memory = 1024
  execution_role_arn = aws_iam_role.ecs_execution.arn
  task_role_arn = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name = "worker"
    image = "${aws_ecr_repository.worker.repository_url}:latest"
    environment = local.common_env
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group = aws_cloudwatch_log_group.worker.name
        awslogs-region = var.aws_region
        awslogs-stream-prefix = "worker"
      }
    }
  }])
}

resource "aws_ecs_service" "api" {
  name = "${var.project}-api"
  cluster = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count = 1
  launch_type = "FARGATE"

  network_configuration {
    subnets = aws_subnet.public[*].id
    security_groups = [aws_security_group.ecs_api.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name = "api"
    container_port = 8000
  }

  depends_on = [aws_lb_listener.https]
}

resource "aws_ecs_service" "worker" {
  name = "${var.project}-worker"
  cluster = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.worker.arn
  desired_count = 1
  launch_type = "FARGATE"

  network_configuration {
    subnets = aws_subnet.public[*].id
    security_groups = [aws_security_group.ecs_worker.id]
    assign_public_ip = true
  }
}
