# Mnemosyne System Overview

This note is written for Obsidian. The diagrams use Mermaid.

## Product Status

The app is now stable enough for local personal use and for building a small Python problem bank. The core loop is working:

- Practice a problem.
- Run visible tests and submit hidden tests.
- Store submission history in SQLite.
- View wrong attempts and details.
- Create or edit problems from JSON.
- Generate or repair problem drafts through an optional LLM API.
- Validate problem JSON deterministically.
- Run the reference solution against expected outputs.
- Manage tags, tests, dependencies, and solutions.

It is not yet fully polished for a nontechnical user. The main remaining gaps are:

- Browser-level end-to-end tests are still missing.
- The authoring UX is better, but still technical.
- Generated problems need a review queue before they enter the library.
- The current LLM loop is synchronous and small; long batch generation will need progress state.
- Arbitrary user code is still safest for trusted local use unless Docker sandboxing is enabled.
- Dependency installs should remain explicit and scoped.

## 1. Feature Map

```mermaid
mindmap
  root((Mnemosyne))
    Practice
      Read Markdown statement
      View examples
      Write Python
      Syntax check
      Run visible tests
      Submit hidden tests
      View result details
      Manage current problem
        Edit JSON
        Edit tags
        Add tests
        Draft edits with LLM
        Draft tests with LLM
        Delete problem
    Problems
      Browse all problems
      Filter by tag
      Search title id tag difficulty type
      Practice selected problem
      Edit tags
    Create through LLM
      Enter fuzzy request
      Generate draft JSON
      Repair with verifier feedback
      Preview before adding
      Add to library
    Create
      Paste JSON
      Upload JSON
      Batch create
      Copy LLM prompt
      Copy API schema
      Preview before adding
    Solution
      View reference solution
      View explanation
      View complexity
    Runtime
      Check Python environment
      Check current problem dependencies
      Install trusted dependency groups
    Submissions
      Current problem history
      All submissions
      Wrong problems
      Submission detail
```

## 2. Current Architecture

```mermaid
flowchart LR
  Browser[Browser UI] --> API[FastAPI app.main]

  API --> Store[problem_store.py]
  Store --> ProblemFiles[problems/*/problem.json]

  API --> Judge[judge.py]
  Judge --> Runner[temporary test_runner.py]
  Runner --> UserCode[user_solution.py]
  Runner --> Tests[visible_tests + hidden_tests]

  API --> DB[database.py]
  DB --> SQLite[data/mnemosyne.sqlite3]

  API --> Authoring[problem_authoring.py]
  Authoring --> Verifier[deterministic verifier]
  Verifier --> Judge

  API --> LLM[llm_authoring.py]
  LLM --> Model[Ollama / Gemini / OpenAI]
  LLM --> Authoring

  API --> Deps[dependencies.py]
  Deps --> Pip[pip install scoped groups]
```

## 3. User Flow

```mermaid
flowchart TD
  Start[Open app] --> Problems{Choose path}

  Problems -->|Practice| SelectProblem[Select problem]
  SelectProblem --> Code[Write Python code]
  Code --> Run[Run visible tests]
  Run --> Result[View result]
  Code --> Submit[Submit hidden tests]
  Submit --> History[Saved to SQLite history]

  Problems -->|Browse| Catalog[Problems page]
  Catalog --> TagFilter[Click tag or search]
  TagFilter --> ProblemList[Filtered problem list]
  ProblemList --> PracticeButton[Practice button]
  PracticeButton --> SelectProblem

  Problems -->|LLM| LlmPage[LLM page]
  LlmPage --> LlmDraft[Generate draft]
  LlmDraft --> Validate

  Problems -->|Create| CreatePage[Create page]
  CreatePage --> Validate[Validate JSON]
  Validate --> Preview[Preview problem and solution]
  Preview --> AddLibrary[Add to library]
  AddLibrary --> Catalog

  SelectProblem --> Manage[Practice Manage tab]
  Manage --> EditTags[Edit tags]
  Manage --> EditJSON[Edit problem JSON]
  Manage --> AddTest[Add generated test]
  Manage --> LlmEdit[LLM edit draft]
  Manage --> LlmTests[LLM test draft]
  Manage --> Delete[Delete problem]
```

## 4. Deterministic Authoring Verifier

```mermaid
flowchart TD
  Input[Problem JSON text or file] --> Clean[Clean input]
  Clean --> Fence[Strip fenced json/prose]
  Fence --> Quotes[Normalize smart quotes]
  Quotes --> Parse[Parse JSON object or array]

  Parse --> Normalize[Normalize fields]
  Normalize --> MoveReq[Move instruction-like requirements to constraints]
  MoveReq --> InferDeps[Infer known package requirements]
  InferDeps --> Imports[Insert missing starter/reference imports]
  Imports --> Checker[Infer allclose for numeric outputs]

  Checker --> StaticValidate[Static validation]
  StaticValidate --> FunctionCheck[Function name and arg count checks]
  FunctionCheck --> RefRun[Run reference_solution on tests]
  RefRun --> Compare[Compare actual vs expected]

  Compare -->|match| OK[Valid problem]
  Compare -->|mismatch| Error[Validation error with expected/actual]
  RefRun -->|runtime error| RefError[Validation error with traceback summary]
  RefRun -->|missing dependency| Warning[Warning: install dependency before full execution]
```

## 5. Request-To-Problem Generation

```mermaid
flowchart TD
  Request[User simple request] --> Intent[Request normalizer]
  Intent --> PromptBuilder[Prompt builder]
  PromptBuilder --> LLM[LLM structured JSON generation]
  LLM --> Draft[Draft problem JSON]

  Draft --> Verifier[Deterministic verifier]
  Verifier -->|valid| Review[Human preview and approval]
  Review -->|accept| Library[Save to problems library]
  Review -->|reject/edit| ManualEdit[Manual edit]
  ManualEdit --> Verifier

  Verifier -->|schema or test error| RepairPrompt[Repair prompt with exact errors]
  RepairPrompt --> LLMRepair[LLM repair attempt]
  LLMRepair --> Verifier

  Verifier -->|too many failures| FailedDraft[Show user errors and draft]
```

## 6. Current Generation Modules

```mermaid
flowchart LR
  UI[LLM and Manage UI] --> LlmAPI[/api/llm/*]
  LlmAPI --> LlmModule[app/llm_authoring.py]
  LlmModule --> Prompt[Prompt builders]
  LlmModule --> Client[OpenAIResponsesClient]
  LlmModule --> Repair[Small repair loop]
  LlmModule --> Tests[Test draft expected-output builder]

  Prompt --> Client
  Client --> RawJSON[raw model JSON]
  RawJSON --> ExistingVerifier[problem_authoring.validate_problem_collection]
  ExistingVerifier --> Repair
  Repair --> Client
  ExistingVerifier --> HumanReview[preview and approve]
  HumanReview --> ProblemFiles[problems/*/problem.json]
```

## 7. Suggested Boundary

Keep this boundary strict:

```mermaid
flowchart LR
  LLM[LLM generation] --> Draft[untrusted draft JSON]
  Draft --> Verifier[trusted deterministic verifier]
  Verifier --> Human[human approval]
  Human --> Judge[trusted deterministic judge]
  Judge --> History[SQLite history]

  LLM -. must not .-> Judge
  LLM -. must not .-> History
  LLM -. must not auto install .-> Deps[dependencies]
```

## Next Build Step

Before adding a larger agent, make the current request-to-draft path easier to audit:

1. Store generated drafts separately before they are accepted.
2. Show a diff when an LLM edits an existing problem.
3. Add browser-level tests for Create and Manage.
4. Add quality checks beyond correctness, such as duplicate tests and weak hidden cases.
5. Add progress state for larger batch generation.

This keeps the product simple while making generation useful.
