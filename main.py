#!/usr/bin/env python

import json
import os.path
import glob
import unittest

import pytest
import yaml

from models.github.action import Action
from  models.github.workflow import Workflow

from pydantic import ValidationError

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


# Press the green button in the gutter to run the script.l
if __name__ == '__main__':
    print_hi('PyCharm')


def load_workflow(path: str) -> dict[str, any] | None:
    yaml_dict = None
    with open(path, "rt") as file:
        yaml_dict = yaml.safe_load(file)
        if True in yaml_dict:
            yaml_dict["on"] = yaml_dict.pop(True)
    return yaml_dict

test_actions_dir = "test/data/actions"
@pytest.mark.parametrize("action_path", glob.glob(os.path.join(test_actions_dir, "**", "action.y*ml")))
def test_actions(action_path: str):
    assert(action_path.endswith((".yml", ".yaml")))

    action_yaml = load_workflow(action_path)
    action = Action(**action_yaml)
    assert action is not None

test_workflows_dir = "test/data/workflows"
@pytest.mark.parametrize("workflow_path", glob.glob(os.path.join(test_workflows_dir, "**", "*.y*ml"),recursive=True))
def test_workflows(workflow_path):
    assert (workflow_path.endswith((".yml", ".yaml")))

    workflow_yaml = load_workflow(workflow_path)
    workflow = Workflow(**workflow_yaml)
    assert workflow is not None








# See PyCharm help at https://www.jetbrains.com/help/pycharm/
