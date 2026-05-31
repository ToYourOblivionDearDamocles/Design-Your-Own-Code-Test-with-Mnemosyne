# Mnemosyne

**Recall, Rebuild, Test Yourself**

A local-first Python coding-practice app that can also turn fuzzy requests,
notes, PDFs, images, or hand-written JSON into executable coding-practice
problems.

The project is built around one principle:

```text
Use LLMs for creativity and translation.
Use deterministic code for correctness.
Use humans for final approval.
```

LLM authoring is intentionally outside the judge. A model can only create draft
problem JSON; the deterministic verifier and your approval decide what enters
the problem bank.

## Quick Start

```bash
git clone <your-repo-url>
cd mnemosyne
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install "numpy>=2.0"  # recommended for the bundled math/ML problems
uvicorn app.main:app --reload --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

First things to try:

1. `Practice`: solve a bundled problem, run visible tests, then submit.
2. `Problems`: browse all problems, search, and filter by tag.
3. `Create`: paste or upload a valid `problem.json`.
4. `Create through LLM`: enter a fuzzy request or attach source material, then
   review the generated draft before adding it to the library.
5. `Manage`: edit a problem's statement, reference solution, tests, tags, or
   raw JSON.

For a deeper architecture and project-history summary, see:

- [System overview](docs/system_overview.md)
- [Project summary](docs/project_summary.md)

Current scope:

- Python-only problems
- Local web UI
- Visible tests and hidden tests
- Function-call problems
- Unit-test-style Python problems
- SQLite submission history
- Wrong-problem tracking
- Failed-test-case detail view
- Solution tab / reference solution API
- Problem catalog and tag filtering
- Per-problem package requirements
- Runtime / package management page
- Problem authoring from standard JSON
- Problem management: edit, add tests, delete
- Optional LLM draft generation, repair, problem edits, and test drafts
- Optional Docker sandbox runner

The first technical goal was to build the deterministic judge loop:

```text
Problem JSON -> User Code -> Test Runner -> Result -> SQLite History
```

## 1. Install

```bash
cd mnemosyne
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install "numpy>=2.0"
```

## 2. Run

```bash
uvicorn app.main:app --reload --port 8000
```

If file watching is unavailable in your environment, run without reload:

```bash
uvicorn app.main:app --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

The app creates this SQLite database automatically after the first run:

```text
data/mnemosyne.sqlite3
```

Optional LLM authoring supports Ollama, Gemini, OpenAI, and OpenAI-compatible
local endpoints. For local use with Ollama:

```bash
ollama serve
export LLM_PROVIDER="ollama"  # optional; auto-selected when Ollama is running
export OLLAMA_MODEL="hf.co/bartowski/Qwen_Qwen3-4B-Thinking-2507-GGUF:Q6_K"
uvicorn app.main:app --reload --port 8000
```

The Ollama client sends structured-output schemas and `think: false` by default.
You can opt back into thinking with:

```bash
export OLLAMA_THINK=true
```

For Gemini:

```bash
export LLM_PROVIDER="gemini"
export GEMINI_API_KEY="..."
export GEMINI_MODEL="gemini-2.5-flash"  # optional
export GEMINI_THINKING_BUDGET=0         # optional; default for Gemini 2.5 Flash
uvicorn app.main:app --reload --port 8000
```

If `GEMINI_API_KEY` is set and `LLM_PROVIDER` is not set, Gemini is selected
before local Ollama. The app still validates every generated draft with the
deterministic verifier before it can be saved.

You can also paste the Gemini key directly into `Create through LLM` in the
browser. That key is kept only in the current loaded page and is sent only with
the generation request; refreshing the browser clears it. The page includes a
Gemini model selector.
By default, Gemini avoids full `responseJsonSchema` and uses JSON mode plus a
compact prompt contract instead. This avoids Gemini errors where complex schemas
produce too many serving states. Set `GEMINI_USE_SCHEMA=true` only if you want to
experiment with Gemini's schema mode.

For OpenAI:

```bash
export LLM_PROVIDER="openai"
export OPENAI_API_KEY="..."
export OPENAI_MODEL="gpt-4.1-mini"  # optional
uvicorn app.main:app --reload --port 8000
```

Without a configured provider, the app still runs normally; the LLM draft
buttons show a provider warning instead of calling a model.

Quick smoke check after code changes:

```bash
python scripts/smoke_check.py
```

This validates the bundled problems, runs accepted and wrong-answer judge paths,
checks LLM authoring repairs, and verifies shell-safe dependency install
commands.

Stricter temporary acceptance check:

```bash
python scripts/acceptance_check.py
```

This creates a throwaway problem bank and SQLite database, then exercises problem
creation, judging, history, tags, unit-test problems, dependency inference,
problem editing, and deletion without modifying your real local data.

## 3. What gets recorded

Every Run or Submit is saved into the `submissions` table.

Stored fields:

```text
id
problem_id
problem_title
mode
status
passed
total
code
result_json
created_at
```

`result_json` contains the full judge result, including failed tests, expected output, actual output, traceback, stdout, and stderr when available.

The UI exposes:

```text
Current problem submission history
All submissions
Wrong problems
Submission detail
Reference solution
Problem catalog by tag
Runtime package status and scoped installs
Create problem from JSON
LLM request-to-problem drafts
Practice Manage tab: edit JSON, generate expected output for function tests, add test cases, delete
```

## 4. Optional Docker runner

By default, the system runs submissions as local subprocesses. This is okay only for personal local use.

To run submissions inside Docker:

```bash
export JUDGE_USE_DOCKER=1
uvicorn app.main:app --reload --port 8000
```

The Docker runner uses:

```bash
docker run --rm --network none --memory 256m --cpus 1 ... python:3.11-slim
```

Docker needs to be installed and running.

## 5. Add a problem

Create a folder under `problems/`, for example:

```text
problems/my_problem/problem.json
```

Problem statements are Markdown. They support headings, paragraphs, lists,
blockquote, fenced code blocks, simple Markdown tables, inline code, links, and
LaTeX-style math:

```markdown
# Quadratic Formula

Solve for the roots of:

$$
ax^2 + bx + c = 0
$$

Use the discriminant $\Delta = b^2 - 4ac$.
```

The browser uses MathJax for math rendering when it is available. If MathJax
cannot load, the original LaTeX remains visible.

Two supported `entry_kind` values:

### Function problem

```json
{
  "id": "two_sum",
  "title": "Two Sum",
  "entry_kind": "function",
  "function_name": "two_sum",
  "requirements": [],
  "constraints": ["Return indices in increasing order."],
  "checker": {"type": "exact"},
  "starter_code": "def two_sum(nums, target):\n    pass",
  "reference_solution": "def two_sum(nums, target):\n    ...",
  "solution_explanation": "Use a hash map from value to index.",
  "complexity": {"time": "O(n)", "space": "O(n)"},
  "visible_tests": [
    {"name": "basic", "args": [[2, 7, 11, 15], 9], "expected": [0, 1]}
  ],
  "hidden_tests": []
}
```

### Unit-test-style problem

```json
{
  "id": "counter_class",
  "title": "Counter Class",
  "entry_kind": "unit_tests",
  "requirements": [],
  "constraints": ["Each instance keeps independent state."],
  "checker": {"type": "exact"},
  "starter_code": "class Counter:\n    pass",
  "visible_tests": [
    {
      "name": "basic increment",
      "code": "from user_solution import Counter\nc = Counter()\nc.increment()\nassert c.get_value() == 1"
    }
  ],
  "hidden_tests": []
}
```

### Per-problem package requirements, constraints, and checkers

Keep app dependencies in `requirements.txt`. Add heavy/runtime-specific packages to each problem instead:

```json
{
  "id": "tensor_shape",
  "title": "Tensor Shape",
  "entry_kind": "function",
  "function_name": "tensor_shape",
  "requirements": [
    {"package": "numpy", "pip": "numpy>=2.0", "import_name": "numpy"},
    {"package": "torch", "pip": "torch>=2.2", "import_name": "torch"}
  ],
  "constraints": [
    "Return a tensor/array-compatible shape tuple.",
    "Do not mutate the input."
  ],
  "checker": {"type": "exact"},
  "starter_code": "def tensor_shape(x):\n    pass",
  "visible_tests": []
}
```

`requirements` is only for Python package dependencies. Put problem rules in
`constraints`. During Create/Validate, the app will also repair common LLM
mistakes by moving instruction-like strings from `requirements` into
`constraints`, inferring known package dependencies from imports/tags such as
`numpy` or `torch`, and choosing `allclose` for numeric array/tensor problems
when no checker is provided.

The authoring verifier is deterministic. It strips fenced JSON, normalizes
smart quotes, repairs common double-escaped newline markers in Markdown/code,
preserves LaTeX commands such as `\nabla`, completes package requirement
objects, inserts missing starter/reference imports for declared packages, and
rejects function problems whose starter or reference code does not define the
declared `function_name`. When local dependencies are available, it also runs
the `reference_solution` against visible and hidden tests, then rejects drafts
where the computed output does not match the declared `expected` output.

Supported checkers:

```json
{"type": "exact"}
```

Use this for ordinary values, strings, lists, dicts, and exact integer results.

```json
{"type": "allclose", "atol": 1e-6, "rtol": 1e-6}
```

Use this for floats, arrays, tensors, and approximate numeric answers. The judge
normalizes objects with `.tolist()`, plus common tensor `.detach().cpu()` flows,
before comparison.

The UI shows whether required packages are installed. The judge also checks
requirements before running a submission and returns `Missing Dependencies`
with an install command when needed.

Optional ML packages are listed in:

```text
requirements-ml.txt
```

The Runtime tab can install packages from two trusted sources only:

```text
Current problem requirements from problem.json
Optional ML stack from requirements-ml.txt
```

It does not accept arbitrary pip commands from the browser.

### Create a problem from JSON

The Create tab accepts either one standard `problem.json` object or a JSON array
of problem objects pasted into the text box or imported from a `.json` file. It
can validate the draft before writing each problem into:

```text
problems/{id}/problem.json
```

Batch shape:

```json
[
  {"id": "first_problem", "...": "..."},
  {"id": "second_problem", "...": "..."}
]
```

The browser also exposes a reusable LLM prompt. Paste that prompt into your LLM,
describe the topic you want, then paste the returned JSON back into the Create
tab. The prompt asks for a fenced `json` block because that tends to preserve
straight JSON quotes in chat UIs. The app will strip the fence and normalize
common smart double quotes before validation. It also applies the deterministic
verifier repairs described above, so a useful draft can usually be validated
without hand-editing every schema mistake.

For a more stable API workflow, copy the schema from the Create page or fetch
`GET /api/authoring/schema`, then use it with a structured-output / JSON-schema
response format in your model API call.

Create is a top-level page for manual JSON only. Validate first to preview each
statement, reference solution, visible tests, and hidden tests. Click
`Add to library` only after the preview looks right.

### Create Through LLM

The Create through LLM tab is separate from Create. Its flow is:

```text
user request -> LLM draft -> verifier/judge check -> up to 2 repair attempts -> preview/report/raw JSON -> Add to library
```

If the verifier rejects the draft, the app sends the exact verifier errors back
to the model and asks for corrected JSON before showing the final draft. The
draft is not saved until you click `Add to library`. You can also copy it into
Create with `Edit in Create`.

When `Problems` is greater than 1, the app now generates each problem one at a
time, validates and repairs it independently, then shows a combined result. This
is more reliable than asking a model to produce a large batch in one response.

Each LLM provider exposes a small profile to the UI, including its generation
strategy, structured-output support, and recommended batch size. The current
providers are Gemini, OpenAI, Ollama, and OpenAI-compatible endpoints.

You can either set provider keys in the shell or paste a Gemini/OpenAI API key
directly into the page. Browser-entered keys are kept only in the current loaded
page and are sent to the backend only for that generation request.
Gemini has a model selector in the page, with `gemini-2.5-flash` as the default.

Practice > Manage keeps the smaller LLM helpers for editing the current problem
and generating test-case drafts. For function problems, generated test drafts
contain only inputs; the app computes expected outputs by running the reference
solution before anything can be saved.

Minimal function-problem shape:

```json
{
  "id": "sum_of_squares",
  "title": "Sum of Squares",
  "difficulty": "easy",
  "entry_kind": "function",
  "function_name": "sum_of_squares",
  "tags": ["python", "math"],
  "requirements": [],
  "constraints": ["Do not modify the input list."],
  "checker": {"type": "exact"},
  "timeout_seconds": 3,
  "statement": "# Sum of Squares\n\nReturn $\\sum x_i^2$.",
  "starter_code": "def sum_of_squares(nums):\n    pass\n",
  "reference_solution": "def sum_of_squares(nums):\n    return sum(x * x for x in nums)\n",
  "solution_explanation": "Square each number and add the results.",
  "complexity": {"time": "O(n)", "space": "O(1)"},
  "visible_tests": [
    {"name": "basic", "args": [[1, 2, 3]], "expected": 14}
  ],
  "hidden_tests": [
    {"name": "negative values", "args": [[-2, 4]], "expected": 20}
  ]
}
```

## 6. API endpoints

```text
GET  /api/problems
GET  /api/problems?tag=python
GET  /api/problems/{problem_id}
GET  /api/problems/{problem_id}/raw
GET  /api/problems/{problem_id}/solution
GET  /api/tags
GET  /api/runtime
GET  /api/runtime?problem_id=two_sum
GET  /api/authoring/template
GET  /api/authoring/prompt
GET  /api/authoring/schema
GET  /api/llm/status
POST /api/submit
POST /api/check-code
POST /api/runtime/install
POST /api/authoring/validate
POST /api/authoring/expected
POST /api/authoring/problems
POST /api/llm/author/problems
POST /api/llm/author/repair
POST /api/llm/problems/{problem_id}/edit
POST /api/llm/problems/{problem_id}/tests
PUT  /api/problems/{problem_id}
POST /api/problems/{problem_id}/expected
POST /api/problems/{problem_id}/tests/generated
POST /api/problems/{problem_id}/tests
DELETE /api/problems/{problem_id}
GET  /api/submissions?problem_id=counter_class&limit=50
GET  /api/submissions/{submission_id}
GET  /api/wrong-problems
```

Example submission:

```bash
curl -X POST http://127.0.0.1:8000/api/submit \
  -H 'Content-Type: application/json' \
  -d '{"problem_id":"counter_class","mode":"run","code":"class Counter:\n    pass"}'
```

## 7. Next engineering step

Possible next modules:

```text
llm_authoring/
  draft_store.py
  provider_registry.py
  multi_step_repair.py
  problem_quality_checks.py
```

The LLM should continue to generate drafts only. The judge and verifier should
remain deterministic.

## 8. License

Mnemosyne is licensed under the GNU Affero General Public License v3.0. See [LICENSE](LICENSE).

AGPLv3 is intentional for this project: if someone modifies Mnemosyne and offers it as a network service, users of that service should also be able to receive the corresponding source code.
