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
