# Project Summary

## Project Goal

Mnemosyne is a local coding-practice system whose larger goal is to convert fuzzy human intent and irregular source materials into executable programming problems.

The target workflow is:

```text
Fuzzy request / notes / PDF / image / human judgment
  -> LLM draft generation
  -> deterministic verifier
  -> repair loop
  -> human preview and approval
  -> local problem library
  -> practice, submit, review history
```

The important product idea is that an LLM can propose problems, but it cannot decide correctness by itself. A deterministic verifier and judge must check the result before the problem becomes part of the library.

## What The System Does Today

The current app supports:

- Python coding-practice problems.
- Markdown problem statements with MathJax math rendering.
- Function-style problems and unit-test-style OOP problems.
- A local judge for visible tests and hidden tests.
- SQLite submission history and wrong-problem tracking.
- Problem browsing, search, tags, and deletion.
- Problem management: edit statement, edit reference solution, edit JSON, add tests, edit tags.
- Dependency metadata for NumPy, PyTorch, pandas, scikit-learn, scipy, and similar packages.
- Runtime conversion from JSON test values into `numpy.ndarray`, `torch.Tensor`, `pandas.DataFrame`, `pandas.Series`, tuples, sets, and simple objects.
- LLM-based problem generation, problem repair, problem editing, and test generation.
- Multimodal input for Gemini through PDF and image attachments.
- A lightweight source-digest agent for faster PDF/image-based generation.

## Core Architecture

```text
Browser UI
  -> FastAPI app
    -> problem_store.py
      -> problems/*/problem.json
    -> judge.py
      -> temporary test_runner.py
      -> user_solution.py
    -> problem_authoring.py
      -> deterministic verifier
      -> reference_solution execution
    -> llm_authoring.py
      -> provider clients
      -> prompt builder
      -> source digest agent
      -> repair loop
    -> database.py
      -> data/mnemosyne.sqlite3
```

The main boundary is:

```text
LLM output is untrusted.
Verifier output is trusted only after deterministic checks pass.
Human approval decides whether a draft enters the problem bank.
Judge execution decides whether user code passes.
```

This boundary is why the system can use LLMs without letting them silently corrupt the library.

## Main Difficulties We Encountered

### 1. LLMs Often Produce Almost-Correct JSON

The first major issue was that models generated plausible JSON that was not actually valid for the app.

Examples:

- Smart quotes like `“id”` instead of `"id"`.
- Empty test objects like `{}`.
- `input` / `output` instead of `args` / `expected`.
- Single-argument list tests written as `args: [1,2,3]` instead of `args: [[1,2,3]]`.
- Instructions placed in `requirements` instead of `constraints`.
- Missing imports for NumPy or PyTorch.
- Missing type hints in starter code.

The solution was a forgiving parser plus a strict normalizer:

- Strip fenced JSON and surrounding prose.
- Normalize smart quotes.
- Normalize common test aliases.
- Move instruction-like requirements into constraints.
- Infer package dependencies.
- Insert missing package imports when safe.
- Validate function names, starter signatures, test shapes, and expected output.

### 2. Test Outputs From LLMs Are Often Wrong

For math, ML, and numerical programming problems, the model often wrote incorrect expected outputs. This happened with gradient descent, Cholesky, attention, and linear algebra examples.

The solution was to make the reference solution the source of truth:

```text
reference_solution + test input
  -> judge execution
  -> actual output
  -> compare with expected
  -> correct expected if reference_solution is valid
```

This makes problem creation more reliable because the model only needs to propose useful inputs and a correct reference solution. The verifier can fill or correct outputs deterministically.

### 3. Floating-Point Equality Was Too Brittle

Numerical outputs from NumPy, PyTorch, and ML-style algorithms rarely match exactly. Early checks failed on tiny differences such as attention outputs or iterative optimization values.

The solution was to support checkers:

- `exact` for ordinary values.
- `allclose` for floats, arrays, tensors, and nested numeric outputs.
- `unordered_nested` for grouped outputs such as anagrams.

The verifier can infer or relax `allclose` tolerance for numeric array/tensor-style problems.

### 4. JSON Transport Was Confused With Python Runtime Types

At first, tests had to store arrays as JSON lists, and that made it look as if every user-facing function had to accept lists. That was too limiting for ML problems.

The solution was to separate storage format from runtime interface:

```json
{
  "arg_types": ["numpy.ndarray"],
  "return_type": "numpy.ndarray",
  "visible_tests": [
    {"name": "basic", "args": [[[1, 2], [3, 4]]], "expected": [1, 3]}
  ]
}
```

The JSON still stores portable values, but the judge converts them before calling user code.

Supported runtime interfaces now include:

- JSON-native list, dict, int, float, string, bool.
- `tuple`, `set`, `frozenset`.
- `numpy.ndarray`.
- `torch.Tensor`.
- `pandas.DataFrame`.
- `pandas.Series`.
- simple object / namespace-style inputs.
- object-like outputs through public attributes, dataclasses, and namedtuples.

### 5. Math Display Rules Were Too Strict

The verifier originally rejected inline equations like `$A = LU$` or `$i = j$`. This made LLM generation fragile because short inline equations are normal in mathematical writing.

The solution was to make math rendering more tolerant:

- Short inline equations are accepted.
- Long or multi-line formulas produce warnings instead of hard errors.
- The frontend also handles inline `$$...$$` and `\\[...\\]` more gracefully.
- Display math is still preferred for long equations, but no longer blocks problem creation for short inline math.

### 6. Batch Generation From PDFs Was Too Slow

For PDF inputs, the first sequential implementation generated one problem at a time and attached the PDF to every request.

That meant:

```text
PDF + prompt -> problem 1
PDF + prompt -> problem 2
PDF + prompt -> problem 3
...
```

This was stable but slow, and Gemini requests could time out.

The solution was a lightweight agent step:

```text
PDF/image
  -> source digest agent
  -> compact summary + problem briefs
  -> text-only per-problem generation
  -> verifier repair loop
```

Now the model reads the PDF/image once, then later calls use a compact text digest. This keeps sequential generation stable while avoiding repeated expensive multimodal calls.

### 7. Provider Compatibility Was Uneven

Different providers support different features:

- Gemini supports PDF/image attachments, but schema mode can fail on complex schemas.
- Gemini thinking models differ in whether thinking can be disabled.
- DeepSeek supports OpenAI-style JSON object mode.
- Ollama can support local structured output but model quality varies.
- OpenAI-compatible endpoints vary by server.

The solution was provider-specific clients with shared output validation:

```text
Provider-specific request format
  -> raw text / JSON
  -> same parser
  -> same verifier
  -> same repair loop
```

Gemini now uses JSON mode plus a compact prompt contract by default, with schema mode available as an experiment. Thinking configuration is handled per model family.

## Prompt Design

The prompt is intentionally strict about structure but flexible about content.

It asks the model to return:

- valid JSON only,
- compact test objects,
- clear `Input / Output` sections,
- type-annotated starter code,
- reference solution,
- visible and hidden tests,
- package dependencies only in `requirements`,
- problem rules in `constraints`,
- short inline math allowed, display math preferred for long formulas.

The prompt also includes few-shot examples because many models repeatedly made the same mistakes:

- single-list argument wrapping,
- multi-argument functions,
- NumPy/allclose problems,
- unit-test/OOP problems.

The prompt does not try to solve correctness alone. Instead, it gives the LLM a target shape, then the verifier checks the result.

## Why We Need An Agent

A single LLM call is not enough for this product because the input and output are both high-variance:

- User requests are vague.
- PDFs and notes are irregular.
- Generated problem JSON has many fields.
- Reference solutions can fail.
- Expected outputs can be wrong.
- Package/runtime types must match the code.

The current agent is intentionally small:

```text
1. Source digest agent
   Read long/multimodal material once and produce compact source context.

2. Problem generation agent
   Generate one verifier-friendly problem at a time.

3. Deterministic verifier
   Parse, normalize, run reference solution, compare expected outputs.

4. Repair loop
   Feed exact verifier errors back to the model.

5. Human approval
   User decides whether to add the draft to the library.
```

This is a semi-automatic agent, not a fully autonomous system. That is deliberate. The goal is to help the user create better problems faster while keeping correctness auditable.

## Why We Need RAG

The current system does not yet use a full vector database RAG pipeline, but it already uses a retrieval-augmented pattern:

```text
attached source materials
  -> source digest
  -> problem briefs
  -> generated problems
```

The source digest acts as temporary retrieval context. It lets the generator use information from a PDF or image without repeatedly sending the full document.

A future RAG layer would make this stronger:

- Store source digests by document.
- Split long PDFs into sections.
- Retrieve only the relevant section for each problem brief.
- Track which source section inspired each generated problem.
- Avoid duplicate problems from the same lecture.
- Let users ask for problems from a specific topic, page, or formula.

RAG matters because the project goal is not simply to generate generic exercises. The goal is to turn the user's real notes, lectures, screenshots, and rough judgments into targeted coding problems.

## Current Verification Framework

The verifier checks:

- JSON parseability.
- Required fields.
- Problem id format.
- `entry_kind`.
- Function name consistency.
- Starter-code type hints.
- Test shape.
- Argument count.
- Package dependency format.
- Known package inference.
- Runtime type declarations.
- Checker validity.
- Markdown/math warnings.
- Reference solution execution.
- Expected output consistency.

The judge supports:

- visible and hidden tests,
- local subprocess execution,
- optional Docker execution,
- dependency checks,
- exact comparison,
- allclose comparison,
- unordered nested comparison,
- output normalization for arrays, tensors, pandas objects, dataclasses, namedtuples, sets, and simple objects.

## Current UI Framework

The UI is a single FastAPI-served web app. It has these main modes:

- `Practice`: solve problems, run tests, submit, view results.
- `Problems`: browse, search, tag-filter, and open problems.
- `Manage`: edit problem statement, solution, tests, tags, JSON, and use LLM-assisted edits.
- `Create through LLM`: generate drafts from fuzzy requests or source materials.
- `Create`: paste or upload JSON directly.
- `Runtime`: inspect and install dependencies.
- `Submissions`: view history, wrong attempts, and details.

The UI tries to stay understandable for a local technical user, while gradually moving toward a cleaner nontechnical workflow.

## Future_test

The next step is broad testing. The goal is not only to find bugs, but to measure whether the whole fuzzy-input-to-problem pipeline is becoming reliable.

### 1. Git Baseline

Before large testing:

```text
initialize git
commit current stable version
run smoke, system, acceptance, adversarial, runtime type matrix checks
record baseline results
```

This lets every later improvement be compared against a stable point.

### 2. Test Corpus

Create a `test_corpus/` directory outside private data, with cases such as:

- fuzzy natural-language requests,
- bad JSON from LLMs,
- Markdown notes,
- lecture PDFs,
- screenshots,
- math-heavy prompts,
- NumPy problems,
- PyTorch problems,
- pandas problems,
- OOP/unit-test problems,
- wrong expected outputs,
- broken reference solutions,
- package dependency problems,
- short inline math and long display math,
- multi-problem generation.

Each case should define:

```text
input material
requested count
provider/model
expected behavior
manual quality notes
```

### 3. Provider Matrix

Test across:

- Gemini Flash.
- Gemini Pro / thinking models.
- DeepSeek.
- Ollama local models.
- OpenAI or OpenAI-compatible endpoints.

Important dimensions:

- `count = 1`, `3`, `5`.
- text-only vs PDF/image attachments.
- timeout settings.
- with and without source digest agent.
- repair attempts.

### 4. Metrics

Track:

- first-pass valid rate,
- valid-after-repair rate,
- average repair attempts,
- timeout rate,
- JSON parse error rate,
- reference solution runtime error rate,
- expected-output correction count,
- package dependency failure rate,
- user manual edit rate,
- generated problem quality score,
- average time per accepted problem.

### 5. UI Testing

Add browser-level tests for:

- creating from LLM,
- uploading JSON,
- previewing drafts,
- editing in Manage,
- adding generated tests,
- tag filtering,
- deleting problems,
- dependency install UI,
- submission detail UI,
- MathJax rendering.

### 6. Quality Testing

Correctness is not enough. We also need quality review:

- Is the statement clear?
- Is the input/output section precise?
- Is the starter code natural?
- Is the reference solution idiomatic?
- Are visible tests educational?
- Are hidden tests meaningful?
- Are tags useful?
- Is the problem too trivial or too large?
- Does it match the source material?

### 7. Future Product Improvements

Likely next build steps:

- Add a draft review queue before saving generated problems.
- Store source digests and generated drafts separately.
- Add diff views for LLM edits.
- Add progress state for long LLM generation.
- Add a true RAG index over uploaded materials.
- Add per-provider benchmark reports.
- Improve UI polish for Manage and Create through LLM.
- Add stronger sandboxing defaults for untrusted code.

## Summary

The project has evolved from a local judge into a controlled problem-generation system.

The key design principle is:

```text
Use LLMs for creativity and translation.
Use deterministic code for correctness.
Use humans for final judgment.
```

That combination is what makes the system promising. It can accept messy human inputs and rich source materials, but it still has a concrete path toward reliable, executable programming problems.
