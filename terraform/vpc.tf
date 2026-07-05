locals {
  azs = ["${var.aws_region}a", "${var.aws_region}b"]
}

resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support = true

  tags = { Name = "${var.project}-vpc" }
}

# Public subnets — ECS tasks get public IPs directly (no NAT gateway needed)
resource "aws_subnet" "public" {
  count = 2
  vpc_id = aws_vpc.main.id
  cidr_block = "10.0.${count.index}.0/24"
  availability_zone = local.azs[count.index]
  map_public_ip_on_launch = true

  tags = { Name = "${var.project}-public-${count.index}" }
}

# Private subnets — RDS and ElastiCache only
resource "aws_subnet" "private" {
  count = 2
  vpc_id = aws_vpc.main.id
  cidr_block = "10.0.${count.index + 10}.0/24"
  availability_zone = local.azs[count.index]

  tags = { Name = "${var.project}-private-${count.index}" }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags = { Name = "${var.project}-igw" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = { Name = "${var.project}-public-rt" }
}

resource "aws_route_table_association" "public" {
  count = 2
  subnet_id = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_security_group" "ecs_api" {
  name = "${var.project}-ecs-api-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port = 8000
    to_port = 8000
    protocol = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "ecs_worker" {
  name = "${var.project}-ecs-worker-sg"
  vpc_id = aws_vpc.main.id

  egress {
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "rds" {
  name = "${var.project}-rds-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port = 5432
    to_port = 5432
    protocol = "tcp"
    security_groups = [aws_security_group.ecs_api.id, aws_security_group.ecs_worker.id]
  }
}

resource "aws_security_group" "elasticache" {
  name = "${var.project}-elasticache-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port = 6379
    to_port = 6379
    protocol = "tcp"
    security_groups = [aws_security_group.ecs_api.id, aws_security_group.ecs_worker.id]
  }
}
