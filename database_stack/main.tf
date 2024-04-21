provider "aws" {
  region = "us-east-1"
}

resource "aws_dynamodb_table" "problems_table" {
  name         = "ProblemsTable"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "Category"
  range_key    = "DifficultyAndProblemId"

  attribute {
    name = "Category"
    type = "S"
  }

  attribute {
    name = "DifficultyAndProblemId"
    type = "S"
  }

  attribute {
    name = "ProblemId"
    type = "S"
  }

  global_secondary_index {
    name            = "ProblemIdIndex"
    hash_key        = "ProblemId"
    projection_type = "ALL"
  }
}

resource "aws_dynamodb_table" "users_table" {
  name         = "UsersTable"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "UserId"
  range_key    = "DifficultyAndProblemId"

  attribute {
    name = "UserId"
    type = "S"
  }

  attribute {
    name = "DifficultyAndProblemId"
    type = "S"
  }
}
