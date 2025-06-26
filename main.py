#!/usr/bin/env python

import json

from models.github.action import Action
from  models.github.workflow import Workflow

# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


def scrub(obj: dict, bad_key: str):
    if isinstance(obj, dict):
        # the call to `list` is useless for py2 but makes
        # the code py2/py3 compatible
        for key in list(obj.keys()):
            if key == bad_key:
                del obj[key]
            else:
                scrub(obj[key], bad_key)
    elif isinstance(obj, list):
        for i in obj:
            scrub(i, bad_key)
    else:
        # neither a dict nor a list, do nothing
        pass


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')

    factory = sm.SchemaModelFactory()

    gh_action_schema_path = "schemas/github-action.json"
    gh_action_schema_file = open(gh_action_schema_path, "rt")
    gh_action_schema = json.load(gh_action_schema_file)
    gh_action_schema_file.close()
    gh_action_schema["title"] = "GithubAction"
    scrub(gh_action_schema, "$comment")
    #print(factory.register(gh_action_schema))

    gh_workflow_schema_path = "schemas/github-workflow.json"
    gh_workflow_schema_file = open(gh_workflow_schema_path, "rt")
    gh_workflow_schema = json.load(gh_workflow_schema_file)
    gh_workflow_schema_file.close()
    gh_workflow_schema["title"] = "GithubWorkflow"
    scrub(gh_workflow_schema, "$comment")
    scrub(gh_workflow_schema, "$ref")
    print(factory.register(gh_workflow_schema))

    Act = Action()
    wf = Workflow()
    print(wf)
    print(Act)









# See PyCharm help at https://www.jetbrains.com/help/pycharm/
