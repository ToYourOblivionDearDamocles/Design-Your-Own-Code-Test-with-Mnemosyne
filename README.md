# Mnemosyne

Warm. White. Runnable.

Mnemosyne is a local-first Python coding practice platform. It keeps the product simple: browse problems, write code, edit the problem bank, and create new verifier-ready problems. The codebase is organized so a GitHub download feels understandable instead of mysterious.

![Problem List](docs/images/problem-list.png)

## Start

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

![Practice](docs/images/practice.png)

![Manage](docs/images/manage.png)

![Create](docs/images/create.png)

## Dependencies

`setup.sh` creates `.venv` and installs:

```text
fastapi, uvicorn, pydantic, numpy, torch, jax[cpu], pandas, scipy
```

## Use

- Problem List: choose a saved problem.
- Practice: write code, run tests, and read the result.
- Manage: edit saved problems or create a new one.
- Create: draft JSON and read verifier feedback.

## Files

```text
mnemosyne/          app code
content/problems/  problem JSON
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

## Product Taste

Do not make it messy.

User input should survive navigation. A new browser tab should be independent. Saved problems should stay shared through the local backend. The Manager Create button should do one clean thing: ask for a title, then open the normal editor.

Simple is not empty. Simple is stable.
