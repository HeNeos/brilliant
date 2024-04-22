import os

import boto3
import json

from boto3.dynamodb.conditions import Key, Attr

PROBLEMS_TABLE_NAME = os.getenv("PROBLEMS_TABLE_NAME")
dynamodb = boto3.resource("dynamodb")
problems_table = dynamodb.Table(PROBLEMS_TABLE_NAME)

all_categories = {
  "ElectricityAndMagnetism",
  "NumberTheory",
  "Geometry"
}

all_difficulties = {
  "1",
  "2",
  "3",
  "4",
  "5",
  "Pending"
}

def get_problem(problem_id: str):
  response = problems_table.get_item(
    IndexName="",
    Key={"Category": problem_id}
  )
  return response["Item"]

def query_problems(category: str, difficulty: str):
  response = problems_table.query(
    KeyConditionExpression=Key("Category").eq(category) & Key("DifficultyAndProblemId").begins_with(difficulty),
    Limit=50
  )
  return response["Items"]

def lambda_handler(event, context):
  query = event.get("multiValueQueryStringParameters", {})
  fields = ["Category", "Difficulty", "ProblemId"]
  filters = {field: query.get(field, None) for field in fields}
  if filters["ProblemId"]:
    problem_id = filters["ProblemId"]
    problems = get_problem(problem_id)
  else:
    categories = set(filters["Category"] or {})
    difficulties = set(filters["Difficulty"] or {})

    if len(categories) == 0:
      categories = all_categories
    if len(difficulties) == 0:
      difficulties = all_difficulties

    categories &= all_categories
    difficulties &= all_difficulties

    for category in categories:
      for difficulty in difficulties:
        problems = query_problems(category, difficulty)

    response = {
      "statusCode": 200,
      "headers": {
        "Content-Type": "application/json"
      },
      "body": json.dumps(problems)
    }

  return response