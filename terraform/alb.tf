resource "aws_security_group" "alb" {
  name = "${var.project}-alb-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port = 80
    to_port = 80
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port = 443
    to_port = 443
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_lb" "api" {
  name = "${var.project}-alb"
  internal = false
  load_balancer_type = "application"
  security_groups = [aws_security_group.alb.id]
  subnets = aws_subnet.public[*].id
}

resource "aws_lb_target_group" "api" {
  name = "${var.project}-api-tg"
  port = 8000
  protocol = "HTTP"
  vpc_id = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path = "/health"
    healthy_threshold = 2
    unhealthy_threshold = 3
    interval = 30
  }
}

# Redirect HTTP to HTTPS
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.api.arn
  port = 80
  protocol = "HTTP"

  default_action {
    type = "redirect"
    redirect {
      port = "443"
      protocol = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.api.arn
  port = 443
  protocol = "HTTPS"
  ssl_policy = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn = aws_acm_certificate.api.arn

  default_action {
    type = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
}
