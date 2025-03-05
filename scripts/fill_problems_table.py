import json
from pathlib import Path
from typing import Dict

import boto3
from get_category_and_level import get_category_and_level

dynamodb = boto3.resource("dynamodb")
problems_table = dynamodb.Table("ProblemsTable")
problems_files = Path.cwd() / "../../brilliant_problems/renamed_problems"


def put_item(pk: str, sk: str, fields: Dict[str, str] = {}):
    problems_table.put_item(
        Item={
            "Category": pk,
            "DifficultyAndProblemId": sk,
            **fields,
        }
    )


with open(
    Path.cwd() / "../../brilliant_problems/problems_id_to_name.json", "r"
) as json_file:
    problems_id_to_name: Dict[str, str] = json.load(json_file)

counter = 0
for problem_id, problem_name in problems_id_to_name.items():
    counter += 1
    topic, level = get_category_and_level(
        problems_files / problem_id / f"{problem_id}.html"
    )
    topic.replace(" ", "")
    level.replace(" ", "")
    put_item(
        topic,
        f"{level}#{problem_id}",
        {"ProblemId": problem_id, "Difficulty": level, "ProblemName": problem_name},
    )
    if counter % 500 == 0:
        print(counter)

