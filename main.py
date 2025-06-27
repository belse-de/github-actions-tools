#!/usr/bin/env python
import argparse
import json
import os.path
import glob
import unittest

import pydantic
from pydantic import ValidationError
import pytest
import yaml

from models.github.action import Action
from models.github.workflow import Workflow


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


def load_action_dict(path: str) -> dict[str, any] | None:
    yaml_dict = None
    with open(path, "rt") as file:
        yaml_dict = yaml.load(file, yaml.BaseLoader)
    return yaml_dict


def load_action(path: str) -> Action:
    yaml_dict = load_action_dict(path)
    return Action(**yaml_dict)


def load_action_log_only(path: str) -> Action | None:
    #assert path.endswith((".yml", ".yaml"))
    result: Action | None = None
    try:
        result = load_action(path)
    except ValidationError as e:
        print(f"Validation error in action {path}: {e}")
    return result


def load_workflow_dict(path: str) -> dict[str, any] | None:
    yaml_dict = None
    with open(path, "rt") as file:
        yaml_dict = yaml.safe_load(file)
        if True in yaml_dict:
            yaml_dict["on"] = yaml_dict.pop(True)
    return yaml_dict


def load_workflow(path: str) -> Workflow:
    yaml_dict = load_workflow_dict(path)
    return Workflow(**yaml_dict)


def load_workflow_log_only(path: str) -> Workflow | None:
    #assert path.endswith((".yml", ".yaml"))
    result: Workflow | None = None
    try:
        result = load_workflow(path)
    except ValidationError as e:
        print(f"Validation error in action {path}: {e}")
    return result


# Press the green button in the gutter to run the script.l
if __name__ == '__main__':
    print_hi('PyCharm')
    argument_parser = argparse.ArgumentParser(description="Tool for GitHub Actions and Workflows")
    argument_parser.add_argument("--validate-action", help="Path to the action yaml file to validate")
    argument_parser.add_argument("--validate-workflow", help="Path to the workflow yaml file to validate")
    argument_parser.add_argument("--validate-repo", help="Path to GitHub repository to validate actions and workflows")
    args = argument_parser.parse_args()

    if args.validate_action:
        action_path = args.validate_action
        assert action_path.endswith((".yml", ".yaml"))
        action = load_action_log_only(action_path)
        assert action is not None
    elif args.validate_workflow:
        workflow_path = args.validate_workflow
        assert workflow_path.endswith((".yml", ".yaml"))
        workflow = load_workflow_log_only(workflow_path)
    elif args.validate_repo:
        repo_path = args.validate_repo
        assert os.path.isdir(repo_path)

        action_paths = glob.glob(os.path.join(repo_path, ".github", "actions", "**", "action.y*ml"), recursive=True)
        for action_path in action_paths:
            if not action_path.endswith((".yml", ".yaml")):
                continue
            print(f"Validating action {action_path}", end="")
            action = load_action_log_only(action_path)
            if action is None:
                print(" - failed")
            else:
                print(" - ok")

        workflow_paths = glob.glob(os.path.join(repo_path, ".github", "workflows", "**", "*.y*ml"), recursive=True)
        for workflow_path in workflow_paths:
            if not workflow_path.endswith((".yml", ".yaml")):
                continue
            print(f"Validating workflow {workflow_path}", end="")
            workflow = load_workflow_log_only(workflow_path)
            if workflow is None:
                print(" - failed")
            else:
                print(" - ok")



test_actions_dir = "test/data/actions"
@pytest.mark.parametrize("action_path", glob.glob(os.path.join(test_actions_dir, "**", "action.y*ml")))
def test_actions(action_path: str):
    assert action_path.endswith((".yml", ".yaml"))
    action = load_action(action_path)
    assert action is not None

test_workflows_dir = "test/data/workflows"
@pytest.mark.parametrize("workflow_path", glob.glob(os.path.join(test_workflows_dir, "**", "*.y*ml"),recursive=True))
def test_workflows(workflow_path):
    assert workflow_path.endswith((".yml", ".yaml"))
    workflow = load_workflow(workflow_path)
    assert workflow is not None
