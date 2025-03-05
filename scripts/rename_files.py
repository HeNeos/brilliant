import json
import shutil
from os import listdir, mkdir
from os.path import isfile, splitext
from pathlib import Path
from uuid import uuid4

problems_files = Path.cwd() / "../brilliant_problems/problems"
new_problems_files = Path.cwd() / "../brilliant_problems/renamed_problems"

map_problems_to_id = dict()
for problem_directory in listdir(problems_files):
    for problem_files in listdir(problems_files / problem_directory):
        problem_id = uuid4().hex
        map_problems_to_id[problem_directory] = problem_id
        if isfile(problems_files / problem_directory / problem_files):
            file_name, file_extension = splitext(problem_files)
            problem_path = problems_files / problem_directory / problem_files
            new_problem_path = (
                new_problems_files / problem_id / f"{problem_id}{file_extension}"
            )
            mkdir(new_problems_files / problem_id)
            shutil.copy(problem_path, new_problem_path)

with open(
    Path.cwd() / "../brilliant_problems/map_problems_to_id.json", "w+"
) as outfile:
    json.dump(map_problems_to_id, outfile)
