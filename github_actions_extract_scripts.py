#!usr/bin/env python3

import yaml
import pydot
import glob
import os
from collections import deque, namedtuple
""""

for action:
    runs.using = "composite"
    runs.steps[*].run script to extract if more than 3 lines
    runs.steps[*].shell in ["bash", "sh", "python", None]
    
    
    runs.steps[*].run may contain ${{ github.action_path }} or $GITHUB_ACTION_PATH -> probably script is extracted

    runs.steps[*].id and runs.steps[*].name can be used to identify the step -> extracted script name
    runs.steps[*].env yaml replacment strings must be resolved here
    
    example of extracted script inside an action:
    runs:
      using: "composite"
      steps:
        - run: "${GITHUB_ACTION_PATH}/script.sh"
          shell: bash
        
    
for workflow:
    jobs.<job_id>.runs.steps[*].run script to extract if more than 3 lines
    jobs.<job_id>.runs.steps[*].shell in ["bash", "sh", "python", None]
    
    
    jobs.<job_id>.runs.steps[*].run may contain ${{ github.action_path }} or $GITHUB_ACTION_PATH -> probably script is extracted

    jobs.<job_id> and jobs.<job_id>.name can be used to identify the step -> extracted script name
    runs.steps[*].env yaml replacment strings must be resolved here
"""


def build_bash_header(year: int, autor: str) -> str:
    """
    Build a bash header with copyright and strict mode settings.
    """
    shebang = "#!/bin/bash\n"
    copyright = f"# Copyright (C) {year} {autor}. All rights reserved.\n"
    bash_strict_mode = "# Bash strict mode\n"
    bash_strict_mode += "set -o pipefail set -o nounset set -o errexit set -o errtrace\n"
    github_style_error_trap = """trap 'echo "::error file=$0,line=$LINENO:: Error: Command: \"$BASH_COMMAND\" failed with status code: \"$?\"" >&2' ERR\n"""
    bash_strict_mode += github_style_error_trap

    return "\n".join([shebang, copyright, bash_strict_mode])


def name_to_id(string: str) -> str | None:
    """
    Convert a step name to step id by replacing invalid characters.
    """
    string_token = string.lower().split()
    string_token = ["".join(filter(lambda x: x.isalnum(), token)) for token in string_token]
    id_name = "-".join(string_token) if len(string_token) > 0 else ""

    return id_name if id_name else None


def step_to_basename(step_idx: int, step_id: str | None, step_name: str):
    step_name = name_to_id(step_name)

    run_script_name_tokens = [str(step_idx)]
    if step_id:
        run_script_name_tokens.append(step_id)
    elif step_name:
        run_script_name_tokens.append(step_name)

    run_script_basename = "-".join(run_script_name_tokens)
    return run_script_basename


def gh_script_usage_graph():
    edges = set()
    nodes = set()

    file_path_iter = glob.glob("./.github/**/*.yaml", recursive=True)
    for file_path in file_path_iter:
        with open(file_path) as gh_file:
            file_dir, file_name = os.path.split(file_path)

            node_attr = set()

            if file_name == "action.yaml":
                node_attr.add("action")
            elif file_path.startswith("./.github/workflows/"):
                node_attr.add("workflow")
            else:
                node_attr.add("config")

            gh_script = yaml.safe_load(gh_file)
            if "action" in node_attr:

                runs_steps = gh_script["runs"]["steps"]
                runs_steps_is_bash_script = ["run" in step and step["shell"] == "bash" for step in runs_steps]
                action_is_bash_script = all(runs_steps_is_bash_script)
                if action_is_bash_script:
                    node_attr.add("bash_script")
                    print(f"action file: {file_path}")
                    print(f"  !!! action is bash script !!! ")

                    for step_idx, step in enumerate(runs_steps):
                        run_script_basename = step_to_basename(step_idx, step.get("id"), step.get("name", ""))
                        run_script_name = f"{run_script_basename}.sh"

                        if "run" in step:
                            run_script = step["run"]
                            if isinstance(run_script, str) and len(run_script):
                                run_script = run_script.splitlines()
                                if len(run_script) > 1:
                                    print(f"  run_script_name: {run_script_name}")
                                    for line in run_script:
                                        #print(f"    {line}")
                                        pass
                    continue
                else:
                    continue


def main():
    gh_script_usage_graph()

if __name__ == "__main__":
    main()
