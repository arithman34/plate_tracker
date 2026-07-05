resource "aws_acm_certificate" "api" {
  domain_name = "plate-tracker.arithman.dev"
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

output "acm_validation_records" {
  description = "Add these DNS records in Cloudflare to validate the certificate"
  value = {
    for dvo in aws_acm_certificate.api.domain_validation_options : dvo.domain_name => {
      name  = dvo.resource_record_name
      type  = dvo.resource_record_type
      value = dvo.resource_record_value
    }
  }
}
