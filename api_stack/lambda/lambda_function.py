import os

import boto3
import json

from boto3.dynamodb.conditions import Key, Attr

PROBLEMS_TABLE_NAME = os.getenv("PROBLEMS_TABLE_NAME")
dynamodb = boto3.resource("dynamodb")
problems_table = dynamodb.Table(PROBLEMS_TABLE_NAME)

all_categories = {"ElectricityAndMagnetism", "NumberTheory", "Geometry"}

all_difficulties = {"1", "2", "3", "4", "5", "Pending"}


def get_problem(problem_id: str):
    response = problems_table.get_item(IndexName="", Key={"Category": problem_id})
    return response["Item"]


def query_problems(category: str, difficulty: str):
    all_problems = []
    last_evaluated_key = None
    projection_expression: str = ", ".join(
        ["Category", "DifficultyAndProblemId", "ProblemName"]
    )
    query_args = {
        "KeyConditionExpression": Key("Category").eq(category)
        & Key("DifficultyAndProblemId").begins_with(f"{difficulty}#"),
        "ProjectionExpression": projection_expression,
    }
    while True:
        if last_evaluated_key:
            response = problems_table.query(
                **query_args,
                ExclusiveStartKey=last_evaluated_key,
            )
        else:
            response = problems_table.query(**query_args)
        problems = response.get("Items", [])
        problems = [
            {
                "Category": problem["Category"],
                "ProblemName": problem["ProblemName"],
                "Difficulty": problem["DifficultyAndProblemId"].split("#")[0],
                "ProblemId": problem["DifficultyAndProblemId"].split("#")[1],
            }
            for problem in problems
        ]
        all_problems.extend(problems)
        if "LastEvaluatedKey" in response:
            last_evaluated_key = response["LastEvaluatedKey"]
        else:
            break
    return all_problems


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
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "GET,OPTIONS",
                "Content-Type": "application/json",
            },
            "body": json.dumps(problems),
        }

    return response
