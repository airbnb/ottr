
# ALB
resource "aws_alb" "otter_alb" {
  name               = "otter-prod-alb"
  internal           = var.internal_alb
  load_balancer_type = "application"
  subnets            = [var.subnet_az1, var.subnet_az2]
  security_groups    = [aws_security_group.internal_to_alb.id]
}

resource "aws_alb_target_group" "otter_tg" {
  name        = "otter-api-target-group"
  protocol    = "HTTPS"
  port        = 8443
  target_type = "ip"
  vpc_id      = var.vpc_id

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_alb_listener" "api_development_listener" {
  load_balancer_arn = aws_alb.otter_alb.arn
  port              = 8443
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }

  depends_on = [aws_alb_target_group.otter_tg]
}
resource "aws_alb_listener" "api_ssl_listener" {
  load_balancer_arn = aws_alb.otter_alb.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_alb_target_group.otter_tg.arn
  }

  depends_on = [
    aws_alb_target_group.otter_tg
  ]
}

resource "aws_alb_listener" "http_to_https_redirect" {
  load_balancer_arn = aws_alb.otter_alb.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }

  depends_on = [aws_alb_target_group.otter_tg]
}

resource "aws_route53_record" "otter" {
  count   = var.internal_alb ? 0 : 1
  zone_id = var.api_zone_id
  name    = var.api_domain_name
  type    = "CNAME"
  ttl     = "300"
  records = [aws_alb.otter_alb.dns_name]
}
