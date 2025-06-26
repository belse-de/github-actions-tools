#!/usr/bin/env python

import glob
import os
import shutil

if __name__ == '__main__':
    print("hallo")
    # os.path.realpath(__file__)

    actions_dir = "test/data/actions"
    # for every sub-folder in "test/data" which is not "actions" or "workflows"
    for action_file in glob.glob("test/data/**/action.y*ml", include_hidden=True):
        if not action_file.endswith((".yml", ".yaml")):
            continue
        action_dir = os.path.dirname(action_file)
        if actions_dir == action_dir:
            continue
        print(action_file)
        shutil.move(action_dir, actions_dir)

    #print(os.getcwd())
    print()

    workflows_dir = "test/data/workflows"
    for workflow_file in glob.glob("test/data/**/workflows/*.y*ml", recursive=True, include_hidden=True):
        if not workflow_file.endswith((".yml", ".yaml")):
            continue
        if workflow_file.startswith(workflows_dir):
            continue
        if  workflow_file.startswith(actions_dir):
            continue

        try:
            print(f"{workflow_file} -> {workflows_dir}")
            shutil.move(workflow_file, workflows_dir)
        except:
            new_workflow_file_name = workflow_file.removeprefix("test/data/")
            new_workflow_file_name = new_workflow_file_name.replace("/", "_")
            new_workflow_file_path = os.path.join(workflows_dir, new_workflow_file_name)
            try:
                print(f"{workflow_file} -> {new_workflow_file_path}")
                shutil.move(workflow_file, new_workflow_file_path)
            except:
                print(f"skipping: {workflow_file}")

    for workflow_file in glob.glob("test/data/starter-workflows/**/*.y*ml", include_hidden=True):
        if not workflow_file.endswith((".yml", ".yaml")):
            continue
        if workflow_file.startswith(workflows_dir):
            continue
        if  workflow_file.startswith(actions_dir):
            continue

        new_workflow_file_name = workflow_file.removeprefix("test/data/")
        new_workflow_file_name = new_workflow_file_name.replace("/", "_")
        new_workflow_file_path = os.path.join(workflows_dir, new_workflow_file_name)
        try:
            print(f"{workflow_file} -> {new_workflow_file_path}")
            shutil.move(workflow_file, new_workflow_file_path)
        except:
            print(f"skipping: {workflow_file}")