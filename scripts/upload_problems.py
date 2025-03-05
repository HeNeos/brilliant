import json
import time
from os import listdir
from pathlib import Path

import boto3
from boto3.exceptions import S3UploadFailedError

s3_client = boto3.client("s3")
bucket_name = "brilliant-problems"
new_problems_files = Path.cwd() / "../../brilliant_problems/renamed_problems"


def upload_file_to_s3(file_path, bucket_name, object_name):
    try:
        s3_client.upload_file(
            file_path, bucket_name, object_name, ExtraArgs={"ContentType": "text/html"}
        )
    except S3UploadFailedError as e:
        print(e)
        return False
    return True


with open(
    Path.cwd() / "../../brilliant_problems/map_problems_to_id.json", "r"
) as json_file:
    map_problems_to_id = json.load(json_file)

with open(Path.cwd() / "../../brilliant_problems/nt_4.txt", "r") as txt_file:
    geometry_problems = txt_file.readlines()

for geometry_problem in geometry_problems:
    problem_id = geometry_problem.strip()
    for problem_file in listdir(new_problems_files / problem_id):
        if upload_file_to_s3(
            new_problems_files / problem_id / problem_file,
            bucket_name,
            f"problems/{problem_id}/{problem_file}",
        ):
            print(f"Successfully uploaded: {problem_file}")
        else:
            print(f"Failed to upload: {problem_file}")
    time.sleep(0.2)

# number_of_problems = len(map_problems_to_id) // 5
# keys_list = list(map_problems_to_id.keys())[:number_of_problems]

# for problem in keys_list:
#     problem_id = map_problems_to_id[problem]
#     for problem_file in listdir(new_problems_files / problem_id):
#         if upload_file_to_s3(
#             new_problems_files / problem_id / problem_file,
#             bucket_name,
#             f"problems/{problem_id}/{problem_file}",
#         ):
#             print(f"Successfully uploaded: {problem_file}")
#         else:
#             print(f"Failed to upload: {problem_file}")
