provider "aws" {
  region = "us-east-1"
}

data "local_file" "output_arn" {
  filename = "${path.module}/../database_stack/.output.arn.txt"
}

data "local_file" "output_name" {
  filename = "${path.module}/../database_stack/.output.name.txt"
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  account_id                 = data.aws_caller_identity.current.account_id
  region                     = data.aws_region.current.name
  get_problems_function_name = "get_problems_lambda_function"
  get_problems_role_name     = "get_problems_lambda_role"
  get_problems_source_path   = "${path.module}/lambda"
}

data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

data "aws_iam_policy_document" "logging" {
  statement {
    effect    = "Allow"
    actions   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:aws:logs:*:*:*"]
  }
}

resource "aws_iam_policy" "get_problems_logging" {
  name        = "get_problems_logging"
  path        = "/"
  description = "IAM policy for logging get_problems lambda"
  policy      = data.aws_iam_policy_document.logging.json
}

resource "aws_iam_policy" "get_problems_read_dynamo" {
  name        = "get_problems_read_dynamo_policy"
  description = "Policy for get_problems lambda to read dynamo Problems table"
  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [{
      "Effect" : "Allow",
      "Action" : [
        "dynamodb:Scan",
        "dynamodb:Query",
        "dynamodb:GetItem",
        "dynamodb:BatchGetItem"
      ],
      "Resource" : [
        data.local_file.output_arn.content,
        "${data.local_file.output_arn.content}/index/*"
      ]
    }]
  })
}

resource "aws_iam_role" "get_problems_lambda_role" {
  name               = local.get_problems_role_name
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

resource "aws_iam_role_policy_attachment" "get_problems_logs" {
  role       = aws_iam_role.get_problems_lambda_role.name
  policy_arn = aws_iam_policy.get_problems_logging.arn
}

resource "aws_iam_role_policy_attachment" "get_problems_read_dynamo" {
  role       = aws_iam_role.get_problems_lambda_role.name
  policy_arn = aws_iam_policy.get_problems_read_dynamo.arn
}

resource "aws_cloudwatch_log_group" "get_problems_log_group" {
  name              = "/aws/lambda/${local.get_problems_function_name}"
  retention_in_days = 14
}

data "archive_file" "get_problems_code" {
  type        = "zip"
  source_file = "${local.get_problems_source_path}/lambda_function.py"
  output_path = "${local.get_problems_source_path}/lambda_function.zip"
}

resource "aws_lambda_function" "get_problems_lambda" {
  filename      = "${local.get_problems_source_path}/lambda_function.zip"
  function_name = local.get_problems_function_name
  role          = aws_iam_role.get_problems_lambda_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.12"
  environment {
    variables = {
      "PROBLEMS_TABLE_NAME" = data.local_file.output_name.content
    }
  }

  source_code_hash = data.archive_file.get_problems_code.output_base64sha256

  depends_on = [aws_iam_role_policy_attachment.get_problems_logs, aws_cloudwatch_log_group.get_problems_log_group]
}


resource "aws_api_gateway_rest_api" "get_problems_api" {
  name = "get_problems_api"
}

resource "aws_api_gateway_resource" "get_problems_api" {
  rest_api_id = aws_api_gateway_rest_api.get_problems_api.id
  parent_id   = aws_api_gateway_rest_api.get_problems_api.root_resource_id
  path_part   = "get_problems"
}

resource "aws_api_gateway_method" "get_problems_api_method" {
  rest_api_id   = aws_api_gateway_rest_api.get_problems_api.id
  resource_id   = aws_api_gateway_resource.get_problems_api.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "get_problems_api_integration" {
  rest_api_id             = aws_api_gateway_rest_api.get_problems_api.id
  resource_id             = aws_api_gateway_resource.get_problems_api.id
  http_method             = aws_api_gateway_method.get_problems_api_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.get_problems_lambda.invoke_arn
}

resource "aws_lambda_permission" "get_problems_lambda_permission" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_problems_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${local.region}:${local.account_id}:${aws_api_gateway_rest_api.get_problems_api.id}/*"
}

resource "aws_api_gateway_method" "options_method" {
  rest_api_id   = aws_api_gateway_rest_api.get_problems_api.id
  resource_id   = aws_api_gateway_resource.get_problems_api.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options_integration" {
  rest_api_id          = aws_api_gateway_rest_api.get_problems_api.id
  resource_id          = aws_api_gateway_resource.get_problems_api.id
  http_method          = aws_api_gateway_method.options_method.http_method
  type                 = "MOCK"
  passthrough_behavior = "WHEN_NO_MATCH"
  request_templates = {
    "application/json" = jsonencode({
      statusCode = 200
    })
  }
}

resource "aws_api_gateway_method_response" "get_200" {
  rest_api_id = aws_api_gateway_rest_api.get_problems_api.id
  resource_id = aws_api_gateway_resource.get_problems_api.id
  http_method = aws_api_gateway_method.get_problems_api_method.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

# OPTIONS method response
resource "aws_api_gateway_method_response" "options_200" {
  rest_api_id = aws_api_gateway_rest_api.get_problems_api.id
  resource_id = aws_api_gateway_resource.get_problems_api.id
  http_method = aws_api_gateway_method.options_method.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true,
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_gateway_response" "cors_4xx" {
  rest_api_id   = aws_api_gateway_rest_api.get_problems_api.id
  response_type = "DEFAULT_4XX"
  response_parameters = {
    "gatewayresponse.header.Access-Control-Allow-Origin"  = "'http://brilliant-problems.s3-website-us-east-1.amazonaws.com'"
    "gatewayresponse.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "gatewayresponse.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
  }
}

resource "aws_api_gateway_integration_response" "get_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.get_problems_api.id
  resource_id = aws_api_gateway_resource.get_problems_api.id
  http_method = aws_api_gateway_method.get_problems_api_method.http_method
  status_code = aws_api_gateway_method_response.get_200.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = "'http://brilliant-problems.s3-website-us-east-1.amazonaws.com'"
  }

  depends_on = [aws_api_gateway_integration.get_problems_api_integration]
}

resource "aws_api_gateway_integration_response" "options_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.get_problems_api.id
  resource_id = aws_api_gateway_resource.get_problems_api.id
  http_method = aws_api_gateway_method.options_method.http_method
  status_code = aws_api_gateway_method_response.options_200.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'",
    "method.response.header.Access-Control-Allow-Origin"  = "'http://brilliant-problems.s3-website-us-east-1.amazonaws.com'"
  }

  depends_on = [aws_api_gateway_integration.options_integration]
}

resource "aws_api_gateway_deployment" "get_problems_api_deploy" {
  rest_api_id = aws_api_gateway_rest_api.get_problems_api.id
  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_method.get_problems_api_method,
      aws_api_gateway_method.options_method,
      aws_api_gateway_integration.get_problems_api_integration,
      aws_api_gateway_integration.options_integration,
      aws_api_gateway_method_response.get_200,
      aws_api_gateway_integration_response.get_integration_response
    ]))
  }
  lifecycle {
    create_before_destroy = true
  }
  depends_on = [aws_api_gateway_method.get_problems_api_method, aws_api_gateway_integration.get_problems_api_integration]
}


resource "aws_api_gateway_stage" "get_problems_api_stage" {
  deployment_id = aws_api_gateway_deployment.get_problems_api_deploy.id
  rest_api_id   = aws_api_gateway_rest_api.get_problems_api.id
  stage_name    = "dev"
}
