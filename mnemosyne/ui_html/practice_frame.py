from __future__ import annotations

TOPBAR_AND_PRACTICE_FRAME = r"""<body data-mode="practice">
  <header class="topbar">
    <div class="brand">
      <span>Mnemosyne</span>
    </div>
    <nav class="top-nav">
      <button id="problemsModeTab" onclick="setAppMode('problems')">Problem List</button>
      <button id="practiceModeTab" class="active" onclick="setAppMode('practice')">Practice</button>
      <button id="manageModeTab" onclick="setAppMode('manage')">Manage</button>
      <button id="llmModeTab" onclick="setAppMode('llm')">Create</button>
    </nav>
    <select id="problemSelect" aria-label="Problem" hidden></select>
    <span id="syntaxBadge" class="badge" hidden>Python</span>
    <div class="topbar-spacer"></div>
  </header>

  <main class="layout">
    <section class="problem-pane">
      <div class="learning-tabs" role="tablist" aria-label="Learning sections">
        <button id="learningProblemTab" class="learning-tab active" onclick="setLearningSection('problem')">Problem</button>
        <button id="learningTheoryTab" class="learning-tab" onclick="setLearningSection('theory')">Theory</button>
        <button id="learningExampleTab" class="learning-tab" onclick="setLearningSection('example')">Example</button>
        <button id="learningSolutionTab" class="learning-tab" onclick="setLearningSection('solution')">Solution</button>
      </div>
      <div class="problem-inner">
        <h1 id="title" class="problem-title"></h1>
        <div id="meta" class="meta"></div>
        <div id="learningProblemPane" class="learning-pane">
          <div id="statement" class="statement"></div>
          <div id="visibleTests" class="leetcode-examples"></div>
        </div>
        <div id="learningTheoryPane" class="learning-pane" hidden>
          <div id="theoryContent" class="statement"></div>
        </div>
        <div id="learningExamplePane" class="learning-pane" hidden>
          <div id="exampleContent" class="statement"></div>
        </div>
        <div id="learningSolutionPane" class="learning-pane" hidden>
          <div id="learningSolutionContent"></div>
        </div>
        <div id="dependencyStatus" class="dependency-list" hidden></div>
      </div>
    </section>

    <div id="mainSplitter" class="main-splitter" aria-hidden="true"></div>

    <section class="work-pane">
      <div class="work-tabs">
        <button id="codeTab" class="tab active" onclick="setView('code')">Code</button>
        <button id="manageTab" class="tab" onclick="setAppMode('manage')" hidden>Manage</button>
        <button id="solutionTab" class="tab" onclick="setView('solution')">Solution</button>
        <button id="runtimeTab" class="tab" onclick="setView('runtime')">Runtime</button>
        <button id="historyTab" class="tab" onclick="setView('history')">Submissions</button>
        <div class="language-pill">Python 3</div>
      </div>

      """
