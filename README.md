# Mnemosyne

**Recall, Rebuild, Test Yourself**

Mnemosyne is a local-first Python coding-practice app. It helps you solve problems, manage a personal problem bank, and optionally turn rough requests or source materials into verified coding-practice problems with an LLM.

## Install

```bash
git clone https://github.com/ToYourOblivionDearDamocles/Design-Your-Own-Code-Test-with-Mnemosyne.git
cd Design-Your-Own-Code-Test-with-Mnemosyne
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install "numpy>=2.0"
uvicorn app.main:app --reload --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

If port `8000` is busy, use another port:

```bash
uvicorn app.main:app --reload --port 8001
```

The app stores local history in:

```text
data/mnemosyne.sqlite3
```

## Optional Packages

The app itself only needs `requirements.txt`. Some problems may need extra packages such as NumPy or PyTorch.

For the bundled math/ML problems, NumPy is recommended:

```bash
pip install "numpy>=2.0"
```

For future PyTorch problems, install it only when needed:

```bash
pip install "torch>=2.2"
```

You can also install declared problem dependencies from the app Runtime page.

## Optional LLM Setup

The app works without an LLM. LLM features are only used in `Create through LLM` and related drafting tools.

You can paste an API key directly in the web page, or set environment variables before starting the app:

```bash
export LLM_PROVIDER="gemini"
export GEMINI_API_KEY="..."
uvicorn app.main:app --reload --port 8000
```

Other supported providers include Ollama, DeepSeek, OpenAI, and OpenAI-compatible local endpoints.

## Modules

### Practice

Solve one problem at a time. Read the description, write Python code, run visible tests, submit hidden tests, view results, and inspect past submissions.

### Problems

Browse the problem bank. Search by title or tag, click tags to filter problems, and jump into practice.

### Manage

Edit existing problems. You can update the statement, reference solution, tags, raw JSON, and test cases. You can also generate expected outputs from the reference solution.

### Create

Create problems by pasting or uploading problem JSON. The deterministic verifier checks the schema, reference solution, tests, expected outputs, dependencies, and checker behavior before a problem is saved.

### Create through LLM

Describe the kind of problem you want, optionally attach notes, Markdown, PDFs, or images, then let an LLM draft problem JSON. Mnemosyne runs verifier feedback loops before showing you a draft to approve.

### Runtime

Inspect Python package requirements for the current problem and install missing dependencies when needed.

### Submissions

View current-problem history, all submissions, wrong problems, and detailed failure records including expected output, actual output, traceback, stdout, stderr, and submitted code.

## License

Mnemosyne is licensed under the GNU Affero General Public License v3.0. See [LICENSE](LICENSE).
