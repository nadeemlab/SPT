data "aws_iam_policy_document" "s3_fast_counts_bucket" {
  statement {
    sid = ""

    actions = [
      "s3:*"
    ]

    effect = "Allow"

    resources = [
      "arn:aws:s3:::${var.fast_counts_bucket_name}",
      "arn:aws:s3:::${var.fast_counts_bucket_name}/*",
    ]

    principals {
      type = "AWS"
      identifiers = [
        "${module.s3_mounter_role.iam_role_arn}",
      ]
    }
  }
}

resource "aws_s3_bucket" "fast_counts_bucket" {
  bucket = var.fast_counts_bucket_name
  policy = "${data.aws_iam_policy_document.s3_fast_counts_bucket.json}"

  tags = {
    Name = var.fast_counts_bucket_name
    terraform = "true"
  }
}