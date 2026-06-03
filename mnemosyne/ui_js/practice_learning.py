from __future__ import annotations

"""Problem loading, learning-section rendering, visible testcase display, and dependency status."""

PRACTICE_LEARNING_SCRIPT = r"""    async function loadProblems() {
      await refreshProblemIndex();
      const practiceState = readSessionState(PRACTICE_STATE_KEY);
      const savedProblemId = practiceState?.currentProblemId;
      const initialProblemId = allProblems.some(problem => problem.id === savedProblemId)
        ? savedProblemId
        : allProblems[0]?.id;
      if (initialProblemId) await loadProblem(initialProblemId);
      await loadAllHistory();
      await loadWrongProblems();
      restoreInitialAppMode();
    }

    async function refreshProblemIndex() {
      const [res, tagRes] = await Promise.all([
        fetch('/api/problems'),
        fetch('/api/tags')
      ]);
      const data = await res.json();
      const tagData = await tagRes.json();
      allProblems = data.problems || [];
      tagSummaries = tagData.tags || [];
      const select = document.getElementById('problemSelect');
      select.innerHTML = '';
      allProblems.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.id;
        opt.textContent = `${p.title} (${p.difficulty})`;
        select.appendChild(opt);
      });
      select.onchange = () => loadProblem(select.value);
      renderCatalog();
    }

    async function loadProblem(problemId) {
      savePracticeState();
      const requestId = ++loadProblemRequestId;
      const res = await fetch(`/api/problems/${encodeURIComponent(problemId)}`);
      const loadedProblem = await res.json();
      if (requestId !== loadProblemRequestId) return;
      currentProblem = loadedProblem;
      document.getElementById('problemSelect').value = currentProblem.id;
      document.getElementById('title').textContent = currentProblem.title;
      document.getElementById('meta').innerHTML = renderMeta(currentProblem);
      renderLearningSections();
      activePracticeCaseIndex = 0;
      renderPracticeTestcases();
      renderDependencyStatus();
      if (!document.getElementById('runtimeView').hidden) {
        await loadRuntimeStatus();
      }
      practiceDirty = false;
      restoringUiState = true;
      try {
        setCodeValue(currentProblem.starter_code || '');
      } finally {
        restoringUiState = false;
      }
      document.getElementById('status').textContent = '';
      latestPracticeRun = null;
      document.getElementById('resultMeta').className = 'badge';
      document.getElementById('resultMeta').textContent = 'No submission';
      document.getElementById('result').innerHTML = `<div class="empty">${escapeHtml(uiText('practice.run_to_see_results', 'Run your code to see test results.'))}</div>`;
      renderPracticeErrorEmpty(uiText('practice.run_to_see_errors', 'Run your code to see program errors.'));
      document.getElementById('submissionDetail').textContent = 'Click Detail on a submission.';
      document.getElementById('solutionBody').innerHTML = '<div class="empty">Open this tab to load the reference solution.</div>';
      solutionLoadedFor = null;
      learningSolutionLoadedFor = null;
      updateLineNumbers();
      updateCursorStatus();
      setPracticeConsoleView('tests');
      await validateCode({quiet: true});
      restorePracticeState(problemId);
      await loadCurrentHistory();
    }

    function renderMeta(problem) {
      const tags = [
        `<span class="tag difficulty">${escapeHtml(problem.difficulty || 'unknown')}</span>`,
        `<span class="tag">${escapeHtml(problem.entry_kind || 'function')}</span>`,
        ...(problem.tags || []).map(t => renderClickableTag(t))
      ];
      return tags.join('');
    }

    function renderVisibleTests() {
      const box = document.getElementById('visibleTests');
      if (!box) return;
      const tests = currentProblem?.visible_tests || [];
      if (!tests.length) {
        box.innerHTML = '';
        return;
      }
      const rendered = tests.map((t, idx) => {
        const name = t.name ? `: ${t.name}` : '';
        if (currentProblem.entry_kind === 'function') {
          const input = formatFunctionCall(currentProblem, t.args || []);
          return `
            <div class="test-card leetcode-example-card">
              <div class="test-name">Example ${idx + 1}${escapeHtml(name)}</div>
              <div class="io-grid leetcode-io-grid">
                ${renderIoBlock('Input', input)}
                ${renderValueBlock('Output', t.expected)}
              </div>
            </div>
          `;
        }
        return `
          <div class="test-card leetcode-example-card">
            <div class="test-name">Example ${idx + 1}${escapeHtml(name)}</div>
            ${renderIoBlock('Test code', t.code || '')}
          </div>
        `;
      }).join('');
      box.innerHTML = `<h2 class="section-title">Examples</h2><div class="test-list">${rendered}</div>`;
    }


    function setLearningSection(section) {
      const sections = ['problem', 'theory', 'example', 'solution'];
      activeLearningSection = sections.includes(section) ? section : 'problem';
      sections.forEach(name => {
        const tab = document.getElementById(`learning${titleCase(name)}Tab`);
        const pane = document.getElementById(`learning${titleCase(name)}Pane`);
        if (tab) tab.classList.toggle('active', name === activeLearningSection);
        if (pane) pane.hidden = name !== activeLearningSection;
      });
      if (activeLearningSection === 'solution') {
        loadLearningSolutionSection();
      }
    }

    function renderLearningSections() {
      const statement = document.getElementById('statement');
      const theory = document.getElementById('theoryContent');
      const example = document.getElementById('exampleContent');
      const solution = document.getElementById('learningSolutionContent');
      if (statement) statement.innerHTML = markdownLite(currentProblem?.statement || '');
      renderVisibleTests();
      if (theory) theory.innerHTML = renderTheorySection(currentProblem);
      if (example) example.innerHTML = renderExampleSection(currentProblem);
      if (solution) solution.innerHTML = renderLearningSolutionPlaceholder(currentProblem);
      learningSolutionLoadedFor = null;
      setLearningSection(activeLearningSection || 'problem');
      typesetMath(document.getElementById('learningProblemPane'));
      typesetMath(document.getElementById('learningTheoryPane'));
      typesetMath(document.getElementById('learningExamplePane'));
    }

    function renderTheorySection(problem) {
      const theory = problem?.theory || problem?.theory_markdown || problem?.algorithm_theory || '';
      if (theory) return markdownLite(theory);
      const constraints = (problem?.constraints || []).map(item => `<li>${escapeHtml(item)}</li>`).join('');
      const tags = (problem?.tags || []).map(tag => renderClickableTag(tag)).join('');
      if (constraints || tags) {
        return `
          <p class="learning-section-kicker">Theory notes</p>
          <div class="learning-empty">No dedicated theory section exists yet. Manage can add one as this problem evolves to the five-part format.</div>
          ${tags ? `<h2 class="section-title">Topics</h2><div class="meta">${tags}</div>` : ''}
          ${constraints ? `<h2 class="section-title">Constraints</h2><ul>${constraints}</ul>` : ''}
        `;
      }
      return '<div class="learning-empty">No theory section has been added yet.</div>';
    }

    function renderExampleSection(problem) {
      const examples = problem?.examples || problem?.worked_examples || [];
      if (Array.isArray(examples) && examples.length) {
        return examples.map((example, idx) => {
          if (typeof example === 'string') {
            return `<div class="test-card"><div class="test-name">Example ${idx + 1}</div><div>${markdownLite(example)}</div></div>`;
          }
          const name = example.name || example.title || `Example ${idx + 1}`;
          const body = example.walkthrough || example.explanation || example.body || '';
          return `<div class="test-card"><div class="test-name">${escapeHtml(name)}</div><div>${markdownLite(body)}</div></div>`;
        }).join('');
      }
      const tests = problem?.visible_tests || [];
      if (!tests.length) return '<div class="learning-empty">No worked examples or visible tests have been added yet.</div>';
      return tests.slice(0, 2).map((test, idx) => renderWorkedExampleFromTest(problem, test, idx)).join('');
    }

    function renderWorkedExampleFromTest(problem, test, idx) {
      const name = test.name || `Example ${idx + 1}`;
      if (problem?.entry_kind === 'function') {
        const input = formatFunctionCall(problem, test.args || []);
        return `
          <div class="test-card">
            <div class="test-name">${escapeHtml(name)}</div>
            <p>This worked example uses the same explicit input/output format as the visible test case.</p>
            <div class="io-grid">
              ${renderIoBlock('Input', input)}
              ${renderValueBlock('Output', test.expected)}
            </div>
          </div>
        `;
      }
      return `
        <div class="test-card">
          <div class="test-name">${escapeHtml(name)}</div>
          ${renderIoBlock('Test code', test.code || '')}
        </div>
      `;
    }

    function renderLearningSolutionPlaceholder(problem) {
      const explanation = problem?.solution_explanation
        ? `<div class="test-card"><div class="test-name">Approach</div><div class="statement">${markdownLite(problem.solution_explanation)}</div></div>`
        : '<div class="learning-empty">Open this section to load the reference solution.</div>';
      return explanation;
    }

    async function loadLearningSolutionSection({force = false} = {}) {
      if (!currentProblem) return;
      const body = document.getElementById('learningSolutionContent');
      if (!body) return;
      if (!force && learningSolutionLoadedFor === currentProblem.id) return;
      body.innerHTML = '<div class="empty">Loading reference solution...</div>';
      const res = await fetch(`/api/problems/${encodeURIComponent(currentProblem.id)}/solution`);
      const data = await res.json();
      learningSolutionLoadedFor = currentProblem.id;
      const complexity = data.complexity || {};
      const complexityHtml = Object.keys(complexity).length
        ? `<div class="test-card"><div class="test-name">Complexity</div><div class="kv">${Object.entries(complexity).map(([k, v]) => `<div><strong>${escapeHtml(k)}:</strong> ${escapeHtml(v)}</div>`).join('')}</div></div>`
        : '';
      const explanation = data.explanation
        ? `<div class="test-card"><div class="test-name">Explanation</div><div class="statement">${markdownLite(data.explanation)}</div></div>`
        : '';
      const solution = data.solution
        ? `<pre class="solution-code">${escapeHtml(data.solution)}</pre>`
        : '<div class="empty">No reference solution has been added for this problem yet.</div>';
      body.innerHTML = `${explanation}${complexityHtml}${solution}`;
      typesetMath(body);
    }

    function setPracticeConsoleView(view) {
      const allowed = ['tests', 'result', 'error'];
      practiceConsoleView = allowed.includes(view) ? view : 'tests';
      const testsPane = document.getElementById('practiceTestsPane');
      const resultPane = document.getElementById('practiceResultPane');
      const errorPane = document.getElementById('practiceErrorPane');
      const testsTab = document.getElementById('practiceTestsTab');
      const resultTab = document.getElementById('practiceResultTab');
      const errorTab = document.getElementById('practiceErrorTab');
      if (!testsPane || !resultPane || !errorPane || !testsTab || !resultTab || !errorTab) return;
      testsPane.hidden = practiceConsoleView !== 'tests';
      resultPane.hidden = practiceConsoleView !== 'result';
      errorPane.hidden = practiceConsoleView !== 'error';
      testsTab.classList.toggle('active', practiceConsoleView === 'tests');
      resultTab.classList.toggle('active', practiceConsoleView === 'result');
      errorTab.classList.toggle('active', practiceConsoleView === 'error');
    }

    function setActivePracticeCase(index) {
      activePracticeCaseIndex = index;
      renderPracticeTestcases();
    }

    function renderPracticeTestcases() {
      const box = document.getElementById('practiceTestcases');
      if (!box) return;
      const tests = currentProblem?.visible_tests || [];
      if (!tests.length) {
        box.innerHTML = `<div class="empty">${escapeHtml(uiText('practice.no_visible_tests', 'No visible tests for this problem.'))}</div>`;
        return;
      }
      activePracticeCaseIndex = Math.min(Math.max(activePracticeCaseIndex, 0), tests.length - 1);
      const selected = tests[activePracticeCaseIndex] || tests[0];
      const tabs = tests.map((test, idx) => `
        <button class="case-tab ${idx === activePracticeCaseIndex ? 'active' : ''}" onclick="setActivePracticeCase(${idx})">
          Case ${idx + 1}
        </button>
      `).join('');

      let body = '';
      if (currentProblem.entry_kind === 'function') {
        const args = selected.args || [];
        const names = functionArgNames(currentProblem);
        const inputs = args.map((arg, idx) => renderConsoleValue(names[idx] || `arg${idx + 1}`, arg)).join('');
        body = `
          <div class="function-call-line">${escapeHtml(formatFunctionCall(currentProblem, args, {compact: true}))}</div>
          ${inputs}
          ${renderConsoleValue('Expected', selected.expected)}
        `;
      } else {
        body = renderConsoleText('Test code', selected.code || '');
      }

      box.innerHTML = `
        <div class="case-tabs">${tabs}</div>
        <div class="practice-case-body">${body}</div>
      `;
    }

    function renderConsoleValue(label, value) {
      return renderConsoleText(label, formatPythonValue(value));
    }

    function renderConsoleText(label, text) {
      return `
        <div class="console-field">
          <div class="console-field-label">${escapeHtml(label)}</div>
          <pre class="console-field-value">${escapeHtml(text)}</pre>
        </div>
      `;
    }

    function renderDependencyStatus() {
      const box = document.getElementById('dependencyStatus');
      const status = currentProblem?.dependency_status || {ok: true, requirements: []};
      const requirements = status.requirements || [];
      if (!requirements.length) {
        box.innerHTML = '<div class="dependency-row"><span>Standard library only</span><span class="badge ok">Ready</span></div>';
        return;
      }

      const rows = requirements.map(req => {
        const installed = Boolean(req.installed);
        const label = req.pip || req.package;
        const version = req.installed_version ? ` ${req.installed_version}` : '';
        const badge = installed
          ? `<span class="badge ok">Installed${escapeHtml(version)}</span>`
          : `<span class="badge error">Missing</span>`;
        return `
          <div class="dependency-row">
            <span><code>${escapeHtml(label)}</code></span>
            ${badge}
          </div>
        `;
      }).join('');

      const install = status.install_command
        ? `<div class="install-command"><strong>Install:</strong> <code>${escapeHtml(status.install_command)}</code></div>`
        : '';
      box.innerHTML = rows + install;
    }

"""
