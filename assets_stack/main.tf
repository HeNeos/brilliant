provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "problems_bucket" {
  bucket = "brilliant-problems"
  tags = {
    Name = "Brilliant problems"
  }
}

resource "aws_s3_bucket_ownership_controls" "problems_bucket_ownership_controls" {
  bucket = aws_s3_bucket.problems_bucket.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_public_access_block" "problems_bucket_public_access_block" {
  bucket = aws_s3_bucket.problems_bucket.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_acl" "problems_bucket_acl" {
  depends_on = [
    aws_s3_bucket_ownership_controls.problems_bucket_ownership_controls,
    aws_s3_bucket_public_access_block.problems_bucket_public_access_block
  ]

  bucket = aws_s3_bucket.problems_bucket.id
  acl    = "public-read"
}

data "aws_iam_policy_document" "problems_bucket_policy_document" {
  statement {

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    actions = [
      "s3:GetObject",
      "s3:ListBucket",
    ]

    resources = [
      aws_s3_bucket.problems_bucket.arn,
      "${aws_s3_bucket.problems_bucket.arn}/*",
    ]
  }
}

resource "aws_s3_bucket_policy" "problems_bucket_policy" {
  bucket = aws_s3_bucket.problems_bucket.id
  policy = data.aws_iam_policy_document.problems_bucket_policy_document.json
}

resource "aws_s3_bucket_website_configuration" "problems_bucket_website_configuration" {
  bucket = aws_s3_bucket.problems_bucket.id
  index_document {
    suffix = "index.html"
  }
}

locals {
  s3_origin_id = "S3-${aws_s3_bucket.problems_bucket.bucket}"
}

resource "aws_cloudfront_distribution" "brilliant_distribution" {
  origin {
    domain_name = aws_s3_bucket.problems_bucket.bucket_regional_domain_name
    origin_id   = local.s3_origin_id

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1", "TLSv1.1", "TLSv1.2"]
    }
  }

  enabled             = true
  is_ipv6_enabled     = true
  comment             = "Brilliant index distribution"
  default_root_object = "index.html"

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD", "OPTIONS"]
    target_origin_id = local.s3_origin_id

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 15
    default_ttl            = 3600
    max_ttl                = 86400
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  tags = {
    Name = "BrilliantDistribution"
  }
}
