schemas are from: https://github.com/SchemaStore/schemastore/tree/master (2025-06-25)

converted via:  https://github.com/koxudaxi/datamodel-code-generator
datamodel-codegen --input schemas/github-action.json --output github/action.py
datamodel-codegen --input schemas/github-workflow.json --output github/workflow.py

datamodel-codegen --input schemas/github-action.json --output models/github/action.py --output-model-type pydantic_v2.BaseModel --class-name Action
datamodel-codegen --input schemas/github-workflow.json --output models/github/workflow.py --output-model-type pydantic_v2.BaseModel --class-name Workflow


fetch test data:
 curl -s 'https://api.github.com/users/actions/repos?per_page=100' | jq -r '.[] | select( .name | test(".*")) | select(.fork == false).ssh_url' | xargs -L1 git clone



# Known issues
- parsing of on.schedule fails with load_action but not with load_workflow