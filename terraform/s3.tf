data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "media" {
  bucket = "${var.project}-media-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_lifecycle_configuration" "media" {
  bucket = aws_s3_bucket.media.id

  rule {
    id = "expire-uploads"
    status = "Enabled"

    filter {
      prefix = "uploads/"
    }

    expiration {
      days = 7
    }
  }
}

output "s3_bucket" {
  description = "S3 bucket name for media storage"
  value = aws_s3_bucket.media.id
}
