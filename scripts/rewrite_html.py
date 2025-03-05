import json
import re
from pathlib import Path

pattern = r'<a href="([^"]+)">([^<]+)</a>'
index_path = Path.cwd() / "../../brilliant_problems/index.html"
with open(
    Path.cwd() / "../../brilliant_problems/map_problems_to_id.json", "r"
) as json_file:
    map_problems_to_id = json.load(json_file)

problems_id_to_name = dict()

with open(index_path, "r") as index_file:
    with open(
        Path.cwd() / "../../brilliant_problems/modified_index.html", "w+"
    ) as new_index_file:
        for line in index_file:
            matches = re.search(pattern, line)
            new_line = line
            if matches:
                href_value = matches.group(1).split("/")
                problem_name = matches.group(2)
                thread_type = href_value[0]
                folder_name = href_value[1]
                if thread_type == "problems":
                    problem_id = map_problems_to_id[folder_name]
                    new_name = "/".join(href_value).replace(folder_name, problem_id)
                    problems_id_to_name[problem_id] = problem_name
                    new_line = line.replace("/".join(href_value), new_name)
            new_index_file.write(new_line)


with open(
    Path.cwd() / "../../brilliant_problems/problems_id_to_name.json", "w+"
) as outfile:
    json.dump(problems_id_to_name, outfile)
