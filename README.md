# Mnemosyne

Design Your Own Code Problem with Mnemosyne.

Mnemosyne helps you build a small personal problem bank. 
It is useful for you if you want to design your own code 
test for different subjects like leetcode style coding problem,
ML coding, numerical methods coding.


<img src="docs/images/promblem-list.png" alt="Problem-list" width="520">

## Start
=======
*If you are trying to find a job, and create simple coding test for students. This is what you need, with the help of LLM, it can turn ambiguous request into specific coding problem for your practice !*

## Install


```bash
./scripts/setup.sh
./scripts/run.sh
```

Open:

```text
http://127.0.0.1:8000
```

Use another port:

```bash
./scripts/run.sh 8854
```

## Screens

You can practice your coding and look at your solution here.
<img src="docs/images/practice.png" alt="Practice" width="720">

You can modify the problem and create new problem here.
<img src="docs/images/manage.png" alt="Manage" width="720">

You can copy paste the prompt and chat with LLM to generate the .json file and import in the problem bank here
<img src="docs/images/create.png" alt="Create" width="720">

## Dependencies

`setup.sh` creates `.venv` and installs:

```text
fastapi, uvicorn, pydantic, numpy, torch, jax[cpu], pandas, scipy
```

## Customize Virtual Environment and LLM Prompts

### Virtual environment

`./scripts/setup.sh` creates the local `.venv`. It looks for Python 3.10 through Python 3.13.

To choose a specific Python version:

```bash
PYTHON=python3.12 ./scripts/setup.sh
```

To add or remove packages for the web app, edit:

```text
requirements/base.txt
```

To add or remove optional ML packages for problem examples, edit:

```text
requirements/ml.txt
```

After changing requirement files, rebuild the virtual environment:

```bash
rm -rf .venv
./scripts/setup.sh
```

For a quick experiment, you can install one package directly:

```bash
.venv/bin/python -m pip install package-name
```

If a problem needs a package, also add it to the problem JSON file:

```text
content/problems/<problem_id>/problem.json
```

Use the problem's `requirements` field so Mnemosyne knows what that problem depends on.

### LLM prompts

Prompt files are stored here:

```text
mnemosyne/prompts/json/
```

Useful prompt files:

```text
direct_json_authoring_prompt.json   prompt copied for Direct JSON mode
problem_agent_system.json           system prompt for in-app LLM problem creation
create_problem_user_message.json    template for creating new problems
repair_problem_user_message.json    template for repairing problem drafts
contract_problem_collection.json    JSON contract for generated problems
contract_test_drafts.json           JSON contract for generated tests
```

Most prompt files use a `text` field. Template prompts use a `template` field and placeholders like:

```text
{{user_request}}
{{count}}
{{errors_json}}
{{warnings_json}}
```

Keep these placeholders unless you also update the Python code that renders the prompt.

After changing a prompt file, check that it is still valid JSON:

```bash
.venv/bin/python -m json.tool mnemosyne/prompts/json/problem_agent_system.json >/dev/null
```

Restart the app after editing prompts:

```bash
./scripts/run.sh
```

## Use

- Problem List: choose a saved problem.
- Practice: write code, run tests, and read the result.
- Manage: edit saved problems or create a new one.
- Create: draft JSON and read verifier feedback.

## Files

```text
mnemosyne/          app code
content/problems/  problem JSON add your own problem from .json file.
requirements/      dependencies
scripts/           setup, run, checks
data/              local database, created when the app runs
```

## Check

```bash
.venv/bin/python -B scripts/checks/smoke_check.py
.venv/bin/python -B scripts/checks/stitch_ui_check.py
```

For a fuller local pass, run the other checks in `scripts/checks/` the same way.
