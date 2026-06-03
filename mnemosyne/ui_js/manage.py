from __future__ import annotations

"""Manage-page editing, test-case management, verifier actions, and local problem saves."""

MANAGE_SCRIPT = r"""    async function loadManagerWorkspace() {
      if (await restoreManageState()) {
        return;
      }
      if (managerProblem) {
        document.getElementById('managerPanel').hidden = false;
        renderManagerProblem();
        return;
      }
      if (managerSelectedProblemId) {
        await selectManagerProblem(managerSelectedProblemId);
        return;
      }
      if (allProblems.length) {
        await selectManagerProblem(allProblems[0].id);
        return;
      }
      startManagerCreateDraft();
    }

    async function loadManagerForCurrentProblem() {
      await loadManagerWorkspace();
    }

    async function selectManagerProblem(problemId) {
      if (!restoringUiState) saveManageState();
      managerSelectedProblemId = problemId;
      managerIsNewDraft = false;
      const res = await fetch(`/api/problems/${encodeURIComponent(problemId)}/raw`);
      const data = await res.json();
      managerProblem = data.problem;
      managerLlmTestDrafts = [];
      activeManagerTestCaseIndex = 0;
      hideManagerAddCase();
      document.getElementById('managerApplyLlmTests').hidden = true;
      document.getElementById('managerPanel').hidden = false;
      document.getElementById('managerJson').value = stringifyProblemJson(managerProblem);
      renderManagerProblem();
      setManagerStatus('Loaded', true);
      managerDirty = false;
    }

    function startManagerCreateDraft() {
      if (!restoringUiState) saveManageState();
      managerSelectedProblemId = null;
      managerIsNewDraft = true;
      managerProblem = blankManagerProblemDraft();
      const defaultTitle = managerProblem.title || managerProblem.id || 'New Problem';
      const promptedTitle = promptManagerDraftTitle(defaultTitle);
      const titleWasEdited = Boolean(promptedTitle && promptedTitle !== defaultTitle);
      if (promptedTitle) managerProblem.title = promptedTitle;
      managerLlmTestDrafts = [];
      activeManagerTestCaseIndex = 0;
      hideManagerAddCase();
      document.getElementById('managerApplyLlmTests').hidden = true;
      document.getElementById('managerPanel').hidden = false;
      document.getElementById('managerJson').value = stringifyProblemJson(managerProblem);
      renderManagerProblem();
      setManagerLearningSection('problem');
      setManagerEditMode('edit');
      setManagerStatus('New draft', null);
      document.getElementById('managerOutput').textContent = 'New problem draft.';
      managerDirty = titleWasEdited;
      if (managerDirty) saveManageState();
    }

    function promptManagerDraftTitle(defaultTitle) {
      const value = prompt('Problem title', defaultTitle || '');
      if (value === null) return null;
      return value.trim() || null;
    }

    function blankManagerProblemDraft() {
      const problemId = nextManagerDraftId();
      return {
        id: problemId,
        title: titleCase(problemId.replace(/_/g, ' ')),
        difficulty: 'easy',
        entry_kind: 'function',
        function_name: 'solve',
        tags: ['python', 'template'],
        requirements: [],
        constraints: ['Return 0 when nums is empty.'],
        checker: {type: 'exact'},
        timeout_seconds: 3,
        statement: '# Sum Values\n\n## Problem\n\nGiven `nums`, return the sum of all integers in `nums`. Return `0` when `nums` is empty.\n\n## Input / Output\n\n- `nums`: `list[int]`, the values to add.\n- Return: `int`, the total sum of the values in `nums`.',
        theory: 'Adding a list is an accumulation pattern: keep a running total and visit each value once.',
        examples: [
          {
            name: 'Walkthrough',
            body: 'For `nums = [1, 2, 3]`, compute $1 + 2 + 3 = 6$.',
          },
        ],
        starter_code: 'def solve(nums: list[int]) -> int:\n    pass\n',
        reference_solution: 'def solve(nums):\n    return sum(nums)\n',
        solution_explanation: 'Use `sum(nums)` to add every integer. Python returns `0` for an empty list, matching the required edge case.',
        complexity: {time: 'O(n)', space: 'O(1)'},
        visible_tests: [
          {name: 'basic', args: [[1, 2, 3]], expected: 6},
          {name: 'empty', args: [[]], expected: 0},
        ],
        hidden_tests: [],
      };
    }

    function nextManagerDraftId() {
      const existing = new Set((allProblems || []).map(problem => String(problem.id || problem.slug || '')));
      let suffix = 1;
      let candidate = 'new_problem';
      while (existing.has(candidate)) {
        suffix += 1;
        candidate = `new_problem_${suffix}`;
      }
      return candidate;
    }

    function renderManagerProblem() {
      if (!managerProblem) return;
      document.getElementById('managerProblemTitle').textContent = managerIsNewDraft
        ? `Create problem: ${managerProblem.title || managerProblem.id}`
        : `${managerProblem.title || managerProblem.id} (${managerProblem.difficulty || 'unknown'})`;
      const managerTagChips = (managerProblem.tags || []).map(tag => renderClickableTag(tag));
      document.getElementById('managerProblemMeta').innerHTML = [
        `<span class="tag">${escapeHtml(managerProblem.difficulty || 'unknown')}</span>`,
        ...managerTagChips
      ].join('') || '<span class="empty-inline">No tags yet.</span>';
      document.getElementById('managerStatement').value = managerProblem.statement || '';
      document.getElementById('managerTheory').value = managerTheoryText(managerProblem);
      document.getElementById('managerExamples').value = managerExamplesText(managerProblem);
      document.getElementById('managerSolutionExplanation').value = managerProblem.solution_explanation || '';
      const complexity = managerProblem.complexity || {};
      document.getElementById('managerComplexityTime').value = complexity.time || '';
      document.getElementById('managerComplexitySpace').value = complexity.space || '';
      document.getElementById('managerReferenceSolution').value = managerProblem.reference_solution || managerProblem.solution || '';
      document.getElementById('managerJson').value = stringifyProblemJson(managerProblem);
      const createButton = document.getElementById('managerCreateDraftButton');
      if (createButton) createButton.classList.toggle('active', managerIsNewDraft);
      const commitLabel = document.getElementById('managerCommitLabel');
      if (commitLabel) commitLabel.textContent = managerIsNewDraft ? 'Create' : 'Commit';
      syncManagerLearningPreviews();
      setManagerLearningSection(managerLearningSection);
      setManagerEditMode(managerEditMode);
      renderManagerTestList();
      setManagerTestOutputNotice('', false);
      document.getElementById('managerPreview').innerHTML = renderProblemPreview(managerProblem, {includeAnswer: true, includeTests: true});
      const managerTagsText = (managerProblem.tags || []).join(', ');
      document.getElementById('managerTagInput').value = managerTagsText;
      const inlineTagInput = document.getElementById('managerInlineTagInput');
      if (inlineTagInput) inlineTagInput.value = managerTagsText;
      typesetMath(document.getElementById('managerPreview'));
      const isUnit = managerProblem.entry_kind === 'unit_tests';
      document.getElementById('managerFunctionTestBox').hidden = isUnit;
      document.getElementById('managerCodeLabel').hidden = !isUnit;
      if (!isUnit) {
        renderManagerInputFields();
        resetManagerGeneratedOutput();
      }
      setManagerToolView(managerToolView);
    }

    function managerTheoryText(problem) {
      return problem?.theory || problem?.theory_markdown || problem?.algorithm_theory || '';
    }

    function managerExamplesText(problem) {
      const examples = problem?.examples || problem?.worked_examples || [];
      if (typeof examples === 'string') return examples;
      if (!Array.isArray(examples) || !examples.length) return '';
      return examples.map((example, idx) => {
        if (typeof example === 'string') return example;
        const name = example.name || example.title || `Example ${idx + 1}`;
        const body = example.walkthrough || example.explanation || example.body || '';
        return `### ${name}\n\n${body}`;
      }).join('\n\n---\n\n');
    }

    function setManagerLearningSection(section) {
      const sections = ['problem', 'theory', 'example', 'solution'];
      managerLearningSection = sections.includes(section) ? section : 'problem';
      sections.forEach(name => {
        const tab = document.getElementById(`manager${titleCase(name)}SectionTab`);
        const pane = document.getElementById(`manager${titleCase(name)}SectionPane`);
        if (tab) tab.classList.toggle('active', name === managerLearningSection);
        if (pane) pane.hidden = name !== managerLearningSection;
      });
    }

    function setManagerEditMode(mode) {
      managerEditMode = mode === 'preview' ? 'preview' : 'edit';
      if (managerEditMode === 'preview') syncManagerLearningPreviews();
      const panel = document.getElementById('managerPanel');
      if (panel) panel.classList.toggle('manager-preview-mode', managerEditMode === 'preview');
      document.getElementById('managerEditModeButton')?.classList.toggle('active', managerEditMode === 'edit');
      document.getElementById('managerPreviewModeButton')?.classList.toggle('active', managerEditMode === 'preview');
    }

    function setManagerToolView(view) {
      managerToolView = view;
      const views = ['tags', 'llm', 'json', 'preview'];
      views.forEach(name => {
        const tab = document.getElementById(`manager${titleCase(name)}ToolTab`);
        const pane = document.getElementById(`manager${titleCase(name)}Pane`);
        if (tab) tab.classList.toggle('active', name === view);
        if (pane) pane.hidden = name !== view;
      });
      if (view === 'llm') {
        loadLlmStatus();
      }
    }

    function openManagerJsonEditor() {
      try {
        syncManagerProblemFromEditors();
        syncManagerJsonFromProblem();
      } catch {}
      setManagerToolView('json');
      document.getElementById('managerJson')?.focus();
      document.getElementById('managerJsonPane')?.scrollIntoView({block: 'nearest'});
    }

    function managerContentFromEditors() {
      if (managerToolView === 'json') {
        try {
          managerProblem = JSON.parse(document.getElementById('managerJson').value);
        } catch (e) {
          throw new Error(`Problem JSON is invalid: ${e.message}`);
        }
        const compact = stringifyProblemJson(managerProblem);
        document.getElementById('managerJson').value = compact;
        return compact;
      }
      syncManagerProblemFromEditors();
      syncManagerJsonFromProblem();
      return document.getElementById('managerJson').value;
    }

    function syncManagerJsonFromProblem() {
      document.getElementById('managerJson').value = stringifyProblemJson(managerProblem);
    }

    function syncManagerProblemFromEditors() {
      if (!managerProblem) throw new Error('No problem is loaded.');
      const draft = managerDraftFromLearningEditors();
      Object.assign(managerProblem, draft);
      syncManagerTestsFromEditors();
      syncManagerLearningPreviews();
    }

    function managerDraftFromLearningEditors() {
      if (!managerProblem) return null;
      const examplesText = document.getElementById('managerExamples')?.value.trim() || '';
      return {
        ...managerProblem,
        statement: document.getElementById('managerStatement')?.value || '',
        theory: document.getElementById('managerTheory')?.value || '',
        examples: examplesText ? [{name: 'Worked examples', body: examplesText}] : [],
        solution_explanation: document.getElementById('managerSolutionExplanation')?.value || '',
        complexity: {
          time: document.getElementById('managerComplexityTime')?.value.trim() || '',
          space: document.getElementById('managerComplexitySpace')?.value.trim() || '',
        },
        reference_solution: document.getElementById('managerReferenceSolution')?.value || '',
      };
    }

    function refreshManagerFullPreview() {
      const preview = document.getElementById('managerPreview');
      const draft = managerDraftFromLearningEditors();
      if (!preview || !draft) return;
      preview.innerHTML = renderProblemPreview(draft, {includeAnswer: true, includeTests: true});
      typesetMath(preview);
    }

    function syncManagerStatementPreview() {
      syncManagerLearningPreviews();
    }

    function syncManagerLearningPreviews() {
      const pairs = [
        ['managerStatement', 'managerStatementPreview'],
        ['managerTheory', 'managerTheoryPreview'],
        ['managerExamples', 'managerExamplesPreview'],
      ];
      pairs.forEach(([sourceId, previewId]) => {
        const source = document.getElementById(sourceId);
        const preview = document.getElementById(previewId);
        if (!source || !preview) return;
        preview.innerHTML = source.value.trim() ? markdownLite(source.value) : `<div class="learning-empty">${escapeHtml(uiText('manager.nothing_written', 'Nothing written yet.'))}</div>`;
        typesetMath(preview);
      });
      syncManagerSolutionPreview();
      refreshManagerFullPreview();
    }

    function syncManagerSolutionPreview() {
      const explanationSource = document.getElementById('managerSolutionExplanation');
      const explanationPreview = document.getElementById('managerSolutionExplanationPreview');
      if (explanationSource && explanationPreview) {
        explanationPreview.innerHTML = explanationSource.value.trim()
          ? markdownLite(explanationSource.value)
          : '<div class="learning-empty">No solution explanation yet.</div>';
        typesetMath(explanationPreview);
      }

      const time = document.getElementById('managerComplexityTime')?.value.trim() || '';
      const space = document.getElementById('managerComplexitySpace')?.value.trim() || '';
      const complexityPreview = document.getElementById('managerComplexityPreview');
      if (complexityPreview) {
        complexityPreview.innerHTML = time || space
          ? `<div class="kv"><div><strong>Time:</strong> ${escapeHtml(time || 'Not set')}</div><div><strong>Space:</strong> ${escapeHtml(space || 'Not set')}</div></div>`
          : `<div class="learning-empty">${escapeHtml(uiText('manager.no_complexity', 'No complexity yet.'))}</div>`;
      }

      const codePreview = document.getElementById('managerReferenceSolutionPreview');
      const code = document.getElementById('managerReferenceSolution')?.value || '';
      if (codePreview) codePreview.textContent = code.trim() ? code : uiText('manager.no_reference_solution', 'No reference solution yet.');
    }

    function renderManagerTestList() {
      const box = document.getElementById('managerTestList');
      if (!box || !managerProblem) return;
      const tests = Array.isArray(managerProblem.visible_tests) ? managerProblem.visible_tests : [];
      if (activeManagerTestCaseIndex >= tests.length) activeManagerTestCaseIndex = tests.length ? 0 : -1;
      if (activeManagerTestCaseIndex < -1) activeManagerTestCaseIndex = tests.length ? 0 : -1;
      const adding = activeManagerTestCaseIndex === -1;

      const tabs = `
        <div class="manager-case-tabs">
          ${tests.map((test, idx) => `
            <button type="button" class="${idx === activeManagerTestCaseIndex ? 'active' : ''}" onclick="focusManagerTestCase(${idx})">Case ${idx + 1}</button>
          `).join('')}
          <button type="button" class="manager-add-case-tab ${adding ? 'active' : ''}" title="Add case" onclick="showManagerAddCase()">
            <span class="material-symbols-outlined" aria-hidden="true">add</span>
          </button>
        </div>
      `;

      if (!tests.length && !adding) {
        box.innerHTML = tabs + '<div class="empty">No explicit tests yet. Use the + tab to add one.</div>';
        return;
      }
      if (adding) {
        box.innerHTML = tabs;
        return;
      }

      const test = tests[activeManagerTestCaseIndex];
      const idx = activeManagerTestCaseIndex;
      const name = test?.name || `case_${idx + 1}`;
      let card = '';
      if (managerProblem.entry_kind === 'unit_tests') {
        card = `
          <div id="managerCase${idx}" class="test-card manager-test-editor manager-case-card">
            <div class="case-title">
              <input class="manager-test-name-input" data-manager-test-group="visible_tests" data-manager-test-index="${idx}" data-manager-test-field="name" spellcheck="false" value="${escapeHtml(name)}" />
              <span class="badge">code</span>
            </div>
            <label class="compact-io-label">
              Unit test code
              <textarea class="small-textarea" data-manager-test-group="visible_tests" data-manager-test-index="${idx}" data-manager-test-field="code" spellcheck="false">${escapeHtml(test.code || '')}</textarea>
            </label>
          </div>
        `;
      } else {
        card = `
          <div id="managerCase${idx}" class="test-card manager-test-editor manager-case-card">
            <div class="case-title">
              <input class="manager-test-name-input" data-manager-test-group="visible_tests" data-manager-test-index="${idx}" data-manager-test-field="name" spellcheck="false" value="${escapeHtml(name)}" />
              <span class="badge">input/output</span>
            </div>
            <div class="manager-test-grid">
              <label class="compact-io-label">
                Input
                <textarea class="small-textarea" data-manager-test-group="visible_tests" data-manager-test-index="${idx}" data-manager-test-field="args" spellcheck="false" wrap="off">${escapeHtml(stringifyEditableJson(test.args || []))}</textarea>
              </label>
              <label class="compact-io-label">
                Expected Output
                <textarea class="small-textarea" data-manager-test-group="visible_tests" data-manager-test-index="${idx}" data-manager-test-field="expected" spellcheck="false" wrap="off">${escapeHtml(stringifyEditableJson(test.expected))}</textarea>
              </label>
            </div>
          </div>
        `;
      }

      box.innerHTML = tabs + card;
    }

    function focusManagerTestCase(idx) {
      try { syncManagerTestsFromEditors(); } catch (e) { renderManagerResult({ok: false, errors: [e.message], warnings: []}, 'Needs fixes'); return; }
      activeManagerTestCaseIndex = idx;
      hideManagerAddCase();
      renderManagerTestList();
    }

    function showManagerAddCase() {
      try { syncManagerTestsFromEditors(); } catch (e) { renderManagerResult({ok: false, errors: [e.message], warnings: []}, 'Needs fixes'); return; }
      activeManagerTestCaseIndex = -1;
      renderManagerTestList();
      const card = document.getElementById('managerAddTestCard');
      if (card) card.hidden = false;
      document.getElementById('managerTestName')?.focus();
    }

    function hideManagerAddCase() {
      const card = document.getElementById('managerAddTestCard');
      if (card) card.hidden = true;
    }

    function focusManagerAddCase() {
      showManagerAddCase();
    }

    function setManagerTestOutputNotice(message, visible = true) {
      const notice = document.getElementById('managerTestOutputNotice');
      if (!notice) return;
      notice.hidden = !visible || !message;
      notice.textContent = message || '';
    }

    function markManagerOutputsStale(field = null) {
      if (field?.dataset) {
        const group = field.dataset.managerTestGroup;
        const idx = field.dataset.managerTestIndex;
        const expected = document.querySelector(`[data-manager-test-group="${group}"][data-manager-test-index="${idx}"][data-manager-test-field="expected"]`);
        if (expected) {
          expected.dataset.outputStale = 'true';
          expected.classList.add('stale-output');
        }
      }
      setManagerTestOutputNotice(uiText('manager.input_changed', 'Input changed. Click Outputs to regenerate expected outputs from the reference solution. Commit/Verify will also correct stale outputs.'));
    }

    function clearManagerExpectedStale(field = null) {
      if (!field) return;
      delete field.dataset.outputStale;
      field.classList.remove('stale-output');
    }

    function syncManagerTestsFromEditors() {
      const fields = [...document.querySelectorAll('[data-manager-test-group]')];
      for (const field of fields) {
        const group = field.dataset.managerTestGroup;
        const idx = Number(field.dataset.managerTestIndex);
        const key = field.dataset.managerTestField;
        if (!group || !Number.isInteger(idx) || !key || !managerProblem[group]?.[idx]) continue;
        if (key === 'name') {
          managerProblem[group][idx].name = field.value.trim() || `${group}_${idx + 1}`;
          continue;
        }
        if (key === 'code') {
          managerProblem[group][idx].code = field.value;
          continue;
        }
        if (key === 'expected' && field.dataset.outputStale === 'true') {
          delete managerProblem[group][idx].expected;
          continue;
        }
        try {
          const parsed = JSON.parse(field.value.trim() || (key === 'args' ? '[]' : 'null'));
          managerProblem[group][idx][key] = parsed;
        } catch (e) {
          throw new Error(`${group}[${idx}].${key} must be valid JSON.`);
        }
      }
    }

    async function refreshManagedTestOutputs() {
      if (!managerProblem) return;
      const addCard = document.getElementById('managerAddTestCard');
      if (activeManagerTestCaseIndex === -1 || (addCard && !addCard.hidden)) {
        return refreshManagerNewTestOutput();
      }
      const activeBefore = activeManagerTestCaseIndex;
      try {
        syncManagerProblemFromEditors();
      } catch (e) {
        renderManagerResult({ok: false, errors: [`Problem edit is invalid: ${e.message}`], warnings: []}, 'Needs fixes');
        return;
      }
      if (managerProblem.entry_kind !== 'function') {
        renderManagerResult({ok: false, errors: ['Output refresh is only available for function problems.'], warnings: []}, 'Not refreshed');
        return;
      }
      for (const test of managerProblem.visible_tests || []) {
        if (test && Array.isArray(test.args)) delete test.expected;
      }
      syncManagerJsonFromProblem();
      setManagerStatus('Refreshing outputs...', null);
      const result = await postJson('/api/authoring/validate', {content: document.getElementById('managerJson').value});
      if (result.problem) {
        managerProblem = result.problem;
        activeManagerTestCaseIndex = Math.max(0, Math.min(activeBefore, (managerProblem.visible_tests || []).length - 1));
        renderManagerProblem();
        focusManagerTestCase(activeManagerTestCaseIndex);
        const activeTest = managerProblem.visible_tests?.[activeManagerTestCaseIndex];
        const expectedText = activeTest ? ` Current case expected: ${formatPythonValueCompact(activeTest.expected)}` : '';
        setManagerTestOutputNotice(result.ok ? `Expected outputs refreshed from the reference solution.${expectedText}` : 'Refresh did not complete. See verifier output.', true);
      }
      renderManagerResult(result, result.ok ? 'Outputs refreshed' : 'Needs fixes');
      return result;
    }

    async function refreshManagerNewTestOutput() {
      if (!managerProblem) return;
      let content;
      let args;
      try {
        syncManagerProblemFromEditors();
        args = collectManagerInputArgs();
        content = managerContentWithDraftTest(args, document.getElementById('managerTestName').value.trim() || 'new test');
      } catch (e) {
        renderManagerResult({ok: false, errors: [`Test input is invalid: ${e.message}`], warnings: []}, 'Needs fixes');
        return {ok: false};
      }
      setManagerStatus('Generating output...', null);
      const result = await postJson('/api/authoring/validate', {content});
      const generated = result.problem?.visible_tests?.[result.problem.visible_tests.length - 1]?.expected;
      if (result.ok && generated !== undefined) {
        showManagerGeneratedOutput(generated);
        setManagerTestOutputNotice(`Generated output for the new case: ${formatPythonValueCompact(generated)}`, true);
      }
      renderManagerResult(result, result.ok ? 'Output generated' : 'Needs fixes');
      return result;
    }

    function managerContentWithDraftTest(args, name = 'new test') {
      const candidate = {
        ...managerProblem,
        visible_tests: [
          ...(Array.isArray(managerProblem.visible_tests) ? managerProblem.visible_tests : []),
          {name, args, expected: null},
        ],
      };
      return stringifyProblemJson(candidate);
    }

    function handleManagerTagKeydown(event) {
      if (event.key !== 'Enter') return;
      event.preventDefault();
      saveManagerTagsFromInline();
    }

    async function saveManagerTagsFromInline() {
      const inline = document.getElementById('managerInlineTagInput');
      if (inline) document.getElementById('managerTagInput').value = inline.value;
      await saveManagerTags();
    }

    async function promptManagerTagEdit() {
      await saveManagerTagsFromInline();
    }

    async function saveManagerTags() {
      if (!managerProblem) return;
      const inline = document.getElementById('managerInlineTagInput');
      if (inline) document.getElementById('managerTagInput').value = inline.value;
      const tags = parseTagsInput(document.getElementById('managerTagInput').value);
      try {
        syncManagerProblemFromEditors();
      } catch (e) {
        renderManagerResult({ok: false, errors: [`Problem edit is invalid: ${e.message}`], warnings: []}, 'Needs fixes');
        return;
      }
      managerProblem.tags = tags;
      syncManagerJsonFromProblem();
      if (managerIsNewDraft || !managerSelectedProblemId) {
        renderManagerProblem();
        renderManagerResult({ok: true, saved: false, errors: [], warnings: []}, 'Tags staged');
        setManagerToolView('tags');
        managerDirty = true;
        saveManageState();
        return;
      }
      const result = await postJson(`/api/problems/${encodeURIComponent(managerSelectedProblemId)}`, {
        content: document.getElementById('managerJson').value
      }, 'PUT');
      renderManagerResult(result, result.saved ? 'Tags saved' : 'Not saved');
      if (result.ok && result.saved) {
        managerProblem = result.problem;
        clearManageDraftState();
        const savedTagsText = (managerProblem.tags || []).join(', ');
        document.getElementById('managerTagInput').value = savedTagsText;
        const inlineTagInput = document.getElementById('managerInlineTagInput');
        if (inlineTagInput) inlineTagInput.value = savedTagsText;
        renderManagerProblem();
        await refreshProblemIndex();
        if (currentProblem?.id === managerSelectedProblemId) {
          await loadProblem(managerSelectedProblemId);
        }
        setManagerToolView('tags');
      }
    }

    function renderManagerInputFields() {
      const box = document.getElementById('managerInputFields');
      const names = functionArgNames(managerProblem);
      const firstVisible = managerProblem?.visible_tests?.find(test => Array.isArray(test.args));
      const argNames = names.length ? names : ['arg1'];
      box.innerHTML = argNames.map((name, idx) => {
        const sample = firstVisible?.args?.[idx];
        const value = sample === undefined ? 'null' : stringifyEditableJson(sample);
        return `
          <div class="manager-input-row">
            <div class="manager-input-name">${escapeHtml(name)}</div>
            <textarea class="small-textarea" data-manager-input-index="${idx}" data-manager-input-name="${escapeHtml(name)}" spellcheck="false">${escapeHtml(value)}</textarea>
          </div>
        `;
      }).join('');
      syncManagerArgsFromFields();
    }

    function resetManagerGeneratedOutput() {
      document.getElementById('managerTestExpected').value = 'null';
      const output = document.getElementById('managerGeneratedOutput');
      output.className = 'empty';
      output.textContent = 'Output will be generated when you add the test.';
    }

    async function validateManagedProblem() {
      const activeBefore = activeManagerTestCaseIndex;
      let content;
      try {
        content = managerContentFromEditors();
      } catch (e) {
        renderManagerResult({ok: false, errors: [`Problem edit is invalid: ${e.message}`], warnings: []}, 'Needs fixes');
        return {ok: false};
      }
      const result = await postJson('/api/authoring/validate', {content});
      if (result.problem) {
        managerProblem = result.problem;
        managerDirty = true;
        activeManagerTestCaseIndex = Math.max(-1, Math.min(activeBefore, (managerProblem.visible_tests || []).length - 1));
        renderManagerProblem();
        if (activeManagerTestCaseIndex >= 0) focusManagerTestCase(activeManagerTestCaseIndex);
        if ((result.warnings || []).some(warning => String(warning).includes('expected output'))) {
          const activeTest = managerProblem.visible_tests?.[activeManagerTestCaseIndex];
          const expectedText = activeTest ? ` Current case expected: ${formatPythonValueCompact(activeTest.expected)}` : '';
          setManagerTestOutputNotice(`Verifier updated expected outputs.${expectedText}`, true);
        }
      }
      renderManagerResult(result, result.ok ? 'Checked' : 'Needs fixes');
      saveManageState();
      return result;
    }

    async function runManagedReference() {
      let content;
      try {
        content = managerContentFromEditors();
      } catch (e) {
        renderManagerResult({ok: false, errors: [`Problem edit is invalid: ${e.message}`], warnings: []}, 'Needs fixes');
        return {ok: false};
      }
      setManagerStatus('Running reference...', null);
      const result = await postJson('/api/authoring/run-reference', {content});
      renderManagerRunResult(result);
      saveManageState();
      return result;
    }

    async function saveManagedProblem() {
      if (!managerProblem) return;
      let content;
      try {
        content = managerContentFromEditors();
      } catch (e) {
        renderManagerResult({ok: false, errors: [`Problem edit is invalid: ${e.message}`], warnings: []}, 'Needs fixes');
        return;
      }
      const wasNewDraft = managerIsNewDraft || !managerSelectedProblemId;
      const result = wasNewDraft
        ? await postJson('/api/authoring/problems', {content, overwrite: false})
        : await postJson(`/api/problems/${encodeURIComponent(managerSelectedProblemId)}`, {content}, 'PUT');
      const saved = Boolean(result.saved || result.created);
      renderManagerResult(result, saved ? (wasNewDraft ? 'Created' : 'Saved') : 'Not saved');
      if (result.ok && saved) {
        managerProblem = result.problem;
        managerSelectedProblemId = result.problem_id || managerProblem.id;
        managerIsNewDraft = false;
        document.getElementById('managerJson').value = stringifyProblemJson(managerProblem);
        renderManagerProblem();
        clearManageDraftState();
        await refreshProblemIndex();
        if (wasNewDraft || !currentProblem || currentProblem?.id === managerSelectedProblemId) {
          await loadProblem(managerSelectedProblemId);
          setView('manage');
        }
        setManagerStatus(wasNewDraft ? 'Created' : 'Saved', true);
      }
    }

    async function deleteManagedProblem() {
      if (!managerSelectedProblemId) {
        if (managerIsNewDraft) {
          managerProblem = null;
          managerIsNewDraft = false;
          document.getElementById('managerPanel').hidden = true;
          clearManageDraftState();
          renderManagerResult({ok: true, deleted: false, errors: [], warnings: []}, 'Draft closed');
        }
        return;
      }
      if (!confirm(`Delete problem "${managerSelectedProblemId}"? This removes its folder from the local problem bank.`)) return;
      const res = await fetch(`/api/problems/${encodeURIComponent(managerSelectedProblemId)}`, {method: 'DELETE'});
      const result = await res.json();
      renderManagerResult(result, result.deleted ? 'Deleted' : 'Not deleted');
      if (result.ok && result.deleted) {
        managerSelectedProblemId = null;
        managerProblem = null;
        document.getElementById('managerPanel').hidden = true;
        await refreshProblemIndex();
        if (allProblems.length && (!currentProblem || result.problem_id === currentProblem.id)) {
          await loadProblem(allProblems[0].id);
        }
      }
    }

    async function addManagedTestCase() {
      if (!managerProblem) return;
      const group = document.getElementById('managerTestGroup').value;
      const name = document.getElementById('managerTestName').value.trim() || 'new test';
      let testCase = {name};
      try {
        syncManagerProblemFromEditors();
        if (managerProblem.entry_kind === 'unit_tests') {
          testCase.code = document.getElementById('managerTestCode').value;
        } else {
          testCase.args = collectManagerInputArgs();
          if (managerIsNewDraft || !managerSelectedProblemId) {
            setManagerStatus('Generating output...', null);
            const result = await postJson('/api/authoring/validate', {content: managerContentWithDraftTest(testCase.args, name)});
            renderManagerResult(result, result.ok ? 'Case staged' : 'Needs fixes');
            const generatedTest = result.problem?.visible_tests?.[result.problem.visible_tests.length - 1];
            if (result.ok && generatedTest) {
              managerProblem = result.problem;
              activeManagerTestCaseIndex = (managerProblem.visible_tests || []).length - 1;
              showManagerGeneratedOutput(generatedTest.expected);
              syncManagerJsonFromProblem();
              hideManagerAddCase();
              renderManagerProblem();
              focusManagerTestCase(activeManagerTestCaseIndex);
              setManagerTestOutputNotice('Case staged in this draft. Commit will create the problem.', true);
              managerDirty = true;
              saveManageState();
            }
            return;
          }
          setManagerStatus('Generating output...', null);
          const result = await postJson(`/api/problems/${encodeURIComponent(managerSelectedProblemId)}/tests/generated`, {
            group,
            name,
            args: testCase.args
          });
          if (result.ok && result.saved) {
            showManagerGeneratedOutput(result.test_case.expected);
            renderManagerResult(result, 'Test added');
            const newIndex = (managerProblem.visible_tests || []).length;
            await selectManagerProblem(managerSelectedProblemId);
            activeManagerTestCaseIndex = newIndex;
            hideManagerAddCase();
            renderManagerTestList();
            await refreshProblemIndex();
            return;
          }
          renderManagerResult(result, 'Not saved');
          return;
        }
      } catch (e) {
        renderManagerResult({ok: false, errors: [`Invalid test input: ${e.message}`], warnings: []}, 'Needs fixes');
        return;
      }

      if (managerIsNewDraft || !managerSelectedProblemId) {
        managerProblem[group] = Array.isArray(managerProblem[group]) ? managerProblem[group] : [];
        managerProblem[group].push(testCase);
        activeManagerTestCaseIndex = managerProblem[group].length - 1;
        syncManagerJsonFromProblem();
        hideManagerAddCase();
        renderManagerProblem();
        focusManagerTestCase(activeManagerTestCaseIndex);
        renderManagerResult({ok: true, saved: false, errors: [], warnings: []}, 'Case staged');
        managerDirty = true;
        saveManageState();
        return;
      }

      const result = await postJson(`/api/problems/${encodeURIComponent(managerSelectedProblemId)}/tests`, {group, test_case: testCase});
      renderManagerResult(result, result.saved ? 'Test added' : 'Not saved');
      if (result.ok && result.saved) {
        const newIndex = (managerProblem.visible_tests || []).length;
        await selectManagerProblem(managerSelectedProblemId);
        activeManagerTestCaseIndex = newIndex;
        hideManagerAddCase();
        renderManagerTestList();
        await refreshProblemIndex();
      }
    }

    async function draftManagedProblemEdit() {
      if (!managerProblem) return;
      if (!managerSelectedProblemId || managerIsNewDraft) {
        renderManagerResult({ok: false, errors: ['Commit this draft before using LLM edit.'], warnings: []}, 'Not ready');
        return;
      }
      const request = document.getElementById('managerLlmRequest').value;
      const provider = document.getElementById('managerLlmProvider').value;
      const api_key = currentLlmApiKey();
      const model = selectedLlmModel('managerLlmModel');
      setManagerStatus('Drafting edit...', null);
      renderManagerLlmOutput('Calling model...');
      const result = await postJson(`/api/llm/problems/${encodeURIComponent(managerSelectedProblemId)}/edit`, {
        request,
        provider,
        api_key,
        model,
        max_attempts: 2
      });
      renderManagerResult(result, result.ok ? 'Edit draft ready' : 'Needs fixes');
      renderManagerLlmOutput(formatLlmResult(result));
      if (result.ok && result.content && result.problem) {
        managerProblem = result.problem;
        document.getElementById('managerJson').value = result.content;
        renderManagerProblem();
        setManagerToolView('llm');
        managerDirty = true;
        saveManageState();
      }
    }

    async function draftManagedTests() {
      if (!managerProblem) return;
      if (!managerSelectedProblemId || managerIsNewDraft) {
        renderManagerResult({ok: false, errors: ['Commit this draft before generating LLM tests.'], warnings: []}, 'Not ready');
        return;
      }
      const request = document.getElementById('managerLlmRequest').value;
      const provider = document.getElementById('managerLlmProvider').value;
      const api_key = currentLlmApiKey();
      const model = selectedLlmModel('managerLlmModel');
      const count = Number(document.getElementById('managerLlmTestCount').value || 3);
      const group = document.getElementById('managerLlmTestGroup').value;
      managerLlmTestDrafts = [];
      managerLlmTestGroup = group;
      document.getElementById('managerApplyLlmTests').hidden = true;
      setManagerStatus('Drafting tests...', null);
      renderManagerLlmOutput('Calling model...');
      const result = await postJson(`/api/llm/problems/${encodeURIComponent(managerSelectedProblemId)}/tests`, {
        request,
        provider,
        api_key,
        group,
        count,
        model
      });
      renderManagerResult(result, result.ok ? 'Test draft ready' : 'Needs fixes');
      managerLlmTestDrafts = result.test_cases || [];
      document.getElementById('managerApplyLlmTests').hidden = !managerLlmTestDrafts.length;
      renderManagerLlmOutput(renderTestDraftText(result));
      if (managerLlmTestDrafts.length) managerDirty = true;
      saveManageState();
    }

    async function applyManagedLlmTests() {
      if (!managerSelectedProblemId || managerIsNewDraft || !managerLlmTestDrafts.length) return;
      setManagerStatus('Adding drafted tests...', null);
      const results = [];
      for (const testCase of managerLlmTestDrafts) {
        const result = await postJson(`/api/problems/${encodeURIComponent(managerSelectedProblemId)}/tests`, {
          group: managerLlmTestGroup,
          test_case: testCase
        });
        results.push(result);
        if (!result.ok || !result.saved) break;
      }
      const ok = results.length === managerLlmTestDrafts.length && results.every(item => item.ok && item.saved);
      const merged = {
        ok,
        saved: ok,
        errors: results.flatMap(item => item.errors || []),
        warnings: results.flatMap(item => item.warnings || []),
      };
      renderManagerResult(merged, ok ? 'Tests added' : 'Not saved');
      renderManagerLlmOutput(ok ? `Added ${results.length} drafted test(s).` : formatLlmResult(merged));
      if (ok) {
        managerLlmTestDrafts = [];
        document.getElementById('managerApplyLlmTests').hidden = true;
        await selectManagerProblem(managerSelectedProblemId);
        await refreshProblemIndex();
      }
    }

    function renderManagerLlmOutput(text) {
      const output = document.getElementById('managerLlmOutput');
      if (output) output.textContent = text;
    }

    function renderTestDraftText(result) {
      const lines = [];
      const errors = formatLimitedMessages('errors', result.errors);
      const warnings = formatLimitedMessages('warnings', result.warnings);
      if (errors) lines.push(errors);
      if (warnings) lines.push(warnings);
      if (result.test_cases?.length) {
        lines.push(`drafted ${result.test_cases.length} test(s) for ${result.group}:`);
        result.test_cases.forEach((test, idx) => {
          const body = test.args
            ? `Input: ${formatFunctionCall(managerProblem, test.args, {compact: true})}\nExpected: ${formatPythonValueCompact(test.expected)}`
            : (test.code || '');
          lines.push(`${idx + 1}. ${test.name || 'generated'}\n${body}`);
        });
      }
      if (result.attempts?.length) {
        lines.push(`attempts:\n${result.attempts.map((attempt, idx) => `- ${idx + 1}: ${attempt.ok ? 'ok' : 'failed'}`).join('\n')}`);
      }
      return lines.join('\n\n') || JSON.stringify(result, null, 2);
    }

    function showManagerGeneratedOutput(expected) {
      document.getElementById('managerTestExpected').value = stringifyProblemJson(expected);
      const output = document.getElementById('managerGeneratedOutput');
      output.className = '';
      output.textContent = formatPythonValue(expected);
    }

    function collectManagerInputArgs() {
      const fields = [...document.querySelectorAll('[data-manager-input-index]')]
        .sort((a, b) => Number(a.dataset.managerInputIndex) - Number(b.dataset.managerInputIndex));
      const args = fields.map(field => {
        const name = field.dataset.managerInputName || `arg${Number(field.dataset.managerInputIndex) + 1}`;
        try {
          return JSON.parse(field.value.trim() || 'null');
        } catch (e) {
          throw new Error(`${name} must be a valid value, for example [1, 2, 3], 9, or "text".`);
        }
      });
      document.getElementById('managerTestArgs').value = stringifyProblemJson(args);
      return args;
    }

    function syncManagerArgsFromFields() {
      try {
        collectManagerInputArgs();
      } catch {
        document.getElementById('managerTestArgs').value = '[]';
      }
    }

    async function practiceManagedProblem() {
      if (!managerSelectedProblemId) {
        renderManagerResult({ok: false, errors: ['Commit this draft before opening it in Practice.'], warnings: []}, 'Not ready');
        return;
      }
      await loadProblem(managerSelectedProblemId);
      setAppMode('practice');
      setView('code');
    }

    function renderManagerResult(result, status) {
      setManagerStatus(status, Boolean(result.ok));
      const lines = [];
      const errors = formatLimitedMessages('errors', result.errors);
      const warnings = formatLimitedMessages('warnings', result.warnings);
      const repairHints = formatRepairHints(result.repair_hints);
      if (errors) lines.push(errors);
      if (warnings) lines.push(warnings);
      if (repairHints) lines.push(`repair hints:\n${repairHints}`);
      if (!lines.length) lines.push(result.saved ? 'Saved.' : result.ok ? 'OK.' : 'No details returned.');
      document.getElementById('managerOutput').textContent = lines.join('\n\n');
    }

    function renderManagerRunResult(result) {
      const judge = result.result || {};
      const ok = Boolean(result.ok);
      setManagerStatus(judge.status || (ok ? 'Accepted' : 'Run failed'), ok);
      const tests = judge.tests || [];
      const cards = tests.map((test, idx) => renderRunCaseCard(test, idx, managerProblem, 'run')).join('');
      const runtimeCards = renderRuntimeDetailCards(judge, tests);
      const messages = [];
      const errors = formatLimitedMessages('errors', result.errors);
      const warnings = formatLimitedMessages('warnings', result.warnings);
      if (errors) messages.push(errors);
      if (warnings) messages.push(warnings);
      if (judge.error) messages.push(`runtime:\n${sanitizeLocalPaths(judge.error)}`);
      document.getElementById('managerOutput').innerHTML = `
        <div class="result-summary-card ${ok ? 'accepted' : 'failed'}">
          <div>
            <div class="result-title status-text ${ok ? 'accepted' : 'wrong'}">${escapeHtml(judge.status || (ok ? 'Accepted' : 'Run failed'))}</div>
            <div class="result-subtitle">Reference solution · explicit tests</div>
          </div>
          <span class="badge ${ok ? 'ok' : 'error'}">${escapeHtml(judge.passed ?? 0)}/${escapeHtml(judge.total ?? tests.length)} passed</span>
        </div>
        ${runtimeCards}
        <div class="case-list">${cards || (!runtimeCards ? '<div class="empty">No test result details returned.</div>' : '')}</div>
        ${messages.length ? `<pre class="manager-message-block">${escapeHtml(messages.join('\n\n'))}</pre>` : ''}
      `;
    }

    function renderRunCaseCard(test, idx, problem = currentProblem, mode = 'run', options = {}) {
      const passed = Boolean(test.passed);
      const includeErrors = options.includeErrors !== false;
      const bits = [];
      const source = testSourceForIndex(problem, idx, mode);
      if (source?.args) bits.push(renderIoBlock('Input', formatFunctionCall(problem, source.args, {compact: true})));
      if (source?.code) bits.push(renderIoBlock('Test code', source.code));
      if ('expected' in test) bits.push(renderValueBlock('Expected', test.expected));
      if ('actual' in test) bits.push(renderValueBlock('Actual', test.actual));
      if (includeErrors && test.error) bits.push(renderIoBlock('Traceback', sanitizeLocalPaths(test.error)));
      return `
        <div class="case-card ${passed ? 'passed' : 'failed'}">
          <div class="case-title">
            <div class="case-title-left">
              <span class="case-dot"></span>
              <span>${escapeHtml(test.name || `test_${idx}`)}</span>
            </div>
            <span class="status-text ${passed ? 'accepted' : 'wrong'}">${passed ? 'passed' : 'failed'}</span>
          </div>
          <div class="io-grid">${bits.join('')}</div>
        </div>
      `;
    }

    function testSourceForIndex(problem, idx, mode) {
      if (!problem) return null;
      const tests = Array.isArray(problem.visible_tests) ? problem.visible_tests : [];
      return tests[idx] || null;
    }

    function setManagerStatus(text, ok = null) {
      const status = document.getElementById('managerStatus');
      status.hidden = false;
      status.className = ok === null ? 'badge' : ok ? 'badge ok' : 'badge error';
      status.textContent = text;
    }

"""
