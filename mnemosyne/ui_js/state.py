from __future__ import annotations

"""Per-tab browser state snapshots for Practice, Manage, and Create."""

UI_STATE_SCRIPT = r"""    let currentView = 'code';
    let practiceDirty = false;
    let managerDirty = false;
    let createDirty = false;
    let restoringUiState = false;
    const SHELL_STATE_KEY = 'mnemosyne.shell.state';
    const PRACTICE_STATE_KEY = 'mnemosyne.practice.state';
    const MANAGE_STATE_KEY = 'mnemosyne.manage.state';
    const CREATE_STATE_KEY = 'mnemosyne.create.state';

    function readSessionState(key) {
      try {
        const raw = sessionStorage.getItem(key);
        return raw ? JSON.parse(raw) : null;
      } catch {
        return null;
      }
    }

    function writeSessionState(key, value) {
      try {
        sessionStorage.setItem(key, JSON.stringify({...value, updatedAt: Date.now()}));
      } catch {}
    }

    function removeSessionState(key) {
      try {
        sessionStorage.removeItem(key);
      } catch {}
    }

    function cloneJson(value) {
      if (value === undefined || value === null) return value;
      try {
        return JSON.parse(JSON.stringify(value));
      } catch {
        return value;
      }
    }

    function elValue(id) {
      return document.getElementById(id)?.value ?? '';
    }

    function elText(id) {
      return document.getElementById(id)?.textContent ?? '';
    }

    function elHtml(id) {
      return document.getElementById(id)?.innerHTML ?? '';
    }

    function elClass(id) {
      return document.getElementById(id)?.className ?? '';
    }

    function elHidden(id) {
      return document.getElementById(id)?.hidden ?? false;
    }

    function setElValue(id, value) {
      const el = document.getElementById(id);
      if (el && 'value' in el) el.value = String(value ?? '');
    }

    function setElText(id, value) {
      const el = document.getElementById(id);
      if (el) el.textContent = String(value ?? '');
    }

    function setElHtml(id, value) {
      const el = document.getElementById(id);
      if (el) el.innerHTML = String(value ?? '');
    }

    function setElClass(id, value) {
      const el = document.getElementById(id);
      if (el && value !== undefined) el.className = String(value || '');
    }

    function setElHidden(id, value) {
      const el = document.getElementById(id);
      if (el) el.hidden = Boolean(value);
    }

    function setElChecked(id, value) {
      const el = document.getElementById(id);
      if (el && 'checked' in el) el.checked = Boolean(value);
    }

    function cssEscape(value) {
      if (window.CSS?.escape) return window.CSS.escape(value);
      return String(value).replace(/["\\]/g, '\\$&');
    }

    function saveShellState() {
      writeSessionState(SHELL_STATE_KEY, {
        mode: document.body?.dataset?.mode || 'practice',
        view: currentView || 'code',
      });
    }

    function snapshotCurrentUiState() {
      savePracticeState();
      saveManageState();
      saveCreateState();
      saveShellState();
    }

    function hasUnsavedUiState() {
      const practiceState = readSessionState(PRACTICE_STATE_KEY);
      const practiceHasDirtyDraft = Object.values(practiceState?.problems || {}).some(item => item?.dirty);
      return practiceDirty
        || managerDirty
        || createDirty
        || practiceHasDirtyDraft
        || Boolean(readSessionState(MANAGE_STATE_KEY)?.dirty)
        || Boolean(readSessionState(CREATE_STATE_KEY)?.dirty);
    }

    function savePracticeState() {
      if (!document.getElementById('code')) return;
      const existing = readSessionState(PRACTICE_STATE_KEY) || {};
      const problems = existing.problems && typeof existing.problems === 'object' ? {...existing.problems} : {};
      const problemId = currentProblem?.id || '';
      if (problemId) {
        problems[problemId] = {
          code: getCodeValue(),
          activePracticeCaseIndex,
          activeLearningSection,
          practiceConsoleView,
          statusText: elText('status'),
          resultMetaText: elText('resultMeta'),
          resultMetaClass: elClass('resultMeta'),
          resultHtml: elHtml('result'),
          diagnosticHtml: elHtml('diagnostic'),
          diagnosticClass: elClass('diagnostic'),
          errorHtml: elHtml('practiceError'),
          syntaxBadgeText: elText('syntaxBadge'),
          syntaxBadgeClass: elClass('syntaxBadge'),
          currentSyntax: cloneJson(currentSyntax),
          dirty: practiceDirty,
        };
      }
      writeSessionState(PRACTICE_STATE_KEY, {
        currentProblemId: problemId || existing.currentProblemId || '',
        problems,
      });
    }

    function restorePracticeState(problemId = currentProblem?.id) {
      const state = readSessionState(PRACTICE_STATE_KEY);
      if (!state) return false;
      const id = problemId || state.currentProblemId;
      const draft = id ? state.problems?.[id] : null;
      if (!draft) return false;
      restoringUiState = true;
      try {
        if ('code' in draft) setCodeValue(draft.code);
        activePracticeCaseIndex = Number.isFinite(Number(draft.activePracticeCaseIndex)) ? Number(draft.activePracticeCaseIndex) : activePracticeCaseIndex;
        if (draft.activeLearningSection) activeLearningSection = draft.activeLearningSection;
        renderPracticeTestcases();
        setLearningSection(activeLearningSection || 'problem');
        if (draft.resultMetaClass !== undefined) setElClass('resultMeta', draft.resultMetaClass);
        if (draft.resultMetaText !== undefined) setElText('resultMeta', draft.resultMetaText);
        if (draft.resultHtml !== undefined) setElHtml('result', draft.resultHtml);
        if (draft.statusText !== undefined) setElText('status', draft.statusText);
        if (draft.diagnosticClass !== undefined) setElClass('diagnostic', draft.diagnosticClass);
        if (draft.diagnosticHtml !== undefined) setElHtml('diagnostic', draft.diagnosticHtml);
        if (draft.errorHtml !== undefined) setElHtml('practiceError', draft.errorHtml);
        if (draft.syntaxBadgeClass !== undefined) setElClass('syntaxBadge', draft.syntaxBadgeClass);
        if (draft.syntaxBadgeText !== undefined) setElText('syntaxBadge', draft.syntaxBadgeText);
        if (draft.currentSyntax) currentSyntax = draft.currentSyntax;
        setPracticeConsoleView(draft.practiceConsoleView || practiceConsoleView || 'tests');
        practiceDirty = Boolean(draft.dirty);
        updateLineNumbers(currentSyntax?.ok ? null : currentSyntax?.line);
        updateCursorStatus();
      } finally {
        restoringUiState = false;
      }
      return true;
    }

    function markPracticeDirty() {
      if (restoringUiState) return;
      practiceDirty = true;
    }

    function collectManagerTestEditorState() {
      return [...document.querySelectorAll('[data-manager-test-group]')].map(field => ({
        group: field.dataset.managerTestGroup || '',
        index: Number(field.dataset.managerTestIndex),
        field: field.dataset.managerTestField || '',
        value: field.value,
        outputStale: field.dataset.outputStale === 'true',
      }));
    }

    function applyManagerTestEditorState(fields) {
      if (!Array.isArray(fields)) return;
      fields.forEach(item => {
        const selector = `[data-manager-test-group="${cssEscape(item.group)}"][data-manager-test-index="${cssEscape(String(item.index))}"][data-manager-test-field="${cssEscape(item.field)}"]`;
        const field = document.querySelector(selector);
        if (!field || !('value' in field)) return;
        field.value = item.value ?? '';
        if (item.outputStale) {
          field.dataset.outputStale = 'true';
          field.classList.add('stale-output');
        }
      });
    }

    function collectManagerInputFieldState() {
      return [...document.querySelectorAll('[data-manager-input-index]')].map(field => ({
        index: Number(field.dataset.managerInputIndex),
        name: field.dataset.managerInputName || '',
        value: field.value,
      }));
    }

    function applyManagerInputFieldState(fields) {
      if (!Array.isArray(fields)) return;
      fields.forEach(item => {
        const field = document.querySelector(`[data-manager-input-index="${cssEscape(String(item.index))}"]`);
        if (field && 'value' in field) field.value = item.value ?? '';
      });
      syncManagerArgsFromFields();
    }

    function saveManageState() {
      const hasManagerDom = Boolean(document.getElementById('managerJson'));
      if (!hasManagerDom || (!managerProblem && !elValue('managerJson'))) return;
      let problem = cloneJson(managerProblem);
      const rawJson = elValue('managerJson');
      if (managerToolView === 'json') {
        try {
          problem = JSON.parse(rawJson);
        } catch {}
      } else if (managerProblem) {
        try {
          syncManagerProblemFromEditors();
          problem = cloneJson(managerProblem);
        } catch {}
      }
      writeSessionState(MANAGE_STATE_KEY, {
        selectedProblemId: managerSelectedProblemId,
        draftIsNew: managerIsNewDraft,
        problem,
        json: rawJson || (problem ? stringifyProblemJson(problem) : ''),
        statement: elValue('managerStatement'),
        theory: elValue('managerTheory'),
        examples: elValue('managerExamples'),
        solutionExplanation: elValue('managerSolutionExplanation'),
        complexityTime: elValue('managerComplexityTime'),
        complexitySpace: elValue('managerComplexitySpace'),
        referenceSolution: elValue('managerReferenceSolution'),
        tagInput: elValue('managerTagInput'),
        inlineTagInput: elValue('managerInlineTagInput'),
        learningSection: managerLearningSection,
        editMode: managerEditMode,
        toolView: managerToolView,
        activeTestCaseIndex: activeManagerTestCaseIndex,
        statusText: elText('managerStatus'),
        statusClass: elClass('managerStatus'),
        statusHidden: elHidden('managerStatus'),
        outputHtml: elHtml('managerOutput'),
        testOutputNotice: elText('managerTestOutputNotice'),
        testOutputNoticeHidden: elHidden('managerTestOutputNotice'),
        testEditors: collectManagerTestEditorState(),
        addTestCardHidden: elHidden('managerAddTestCard'),
        addTestGroup: elValue('managerTestGroup'),
        addTestName: elValue('managerTestName'),
        addTestCode: elValue('managerTestCode'),
        addTestArgs: elValue('managerTestArgs'),
        addTestExpected: elValue('managerTestExpected'),
        inputFields: collectManagerInputFieldState(),
        generatedOutputText: elText('managerGeneratedOutput'),
        generatedOutputClass: elClass('managerGeneratedOutput'),
        llmRequest: elValue('managerLlmRequest'),
        llmProvider: elValue('managerLlmProvider'),
        llmModel: elValue('managerLlmModel'),
        llmTestCount: elValue('managerLlmTestCount'),
        llmTestGroup: elValue('managerLlmTestGroup') || managerLlmTestGroup,
        llmOutputText: elText('managerLlmOutput'),
        llmTestDrafts: cloneJson(managerLlmTestDrafts),
        llmApplyHidden: elHidden('managerApplyLlmTests'),
        dirty: managerDirty,
      });
    }

    async function restoreManageState() {
      const state = readSessionState(MANAGE_STATE_KEY);
      if (!state) return false;
      let problem = cloneJson(state.problem);
      if (!problem && state.json) {
        try {
          problem = JSON.parse(state.json);
        } catch {}
      }
      if (!problem && state.selectedProblemId) {
        try {
          const res = await fetch(`/api/problems/${encodeURIComponent(state.selectedProblemId)}/raw`);
          const data = await res.json();
          problem = data.problem;
        } catch {}
      }
      if (!problem) return false;
      restoringUiState = true;
      try {
        managerIsNewDraft = Boolean(state.draftIsNew);
        managerSelectedProblemId = state.selectedProblemId || problem.id || null;
        managerProblem = problem;
        managerToolView = state.toolView || 'tags';
        managerLearningSection = state.learningSection || 'problem';
        managerEditMode = state.editMode || 'edit';
        managerLlmTestDrafts = Array.isArray(state.llmTestDrafts) ? state.llmTestDrafts : [];
        managerLlmTestGroup = state.llmTestGroup || 'visible_tests';
        activeManagerTestCaseIndex = Number.isFinite(Number(state.activeTestCaseIndex)) ? Number(state.activeTestCaseIndex) : 0;
        setElHidden('managerPanel', false);
        renderManagerProblem();
        setElValue('managerStatement', state.statement ?? managerProblem.statement ?? '');
        setElValue('managerTheory', state.theory ?? managerTheoryText(managerProblem));
        setElValue('managerExamples', state.examples ?? managerExamplesText(managerProblem));
        setElValue('managerSolutionExplanation', state.solutionExplanation ?? managerProblem.solution_explanation ?? '');
        setElValue('managerComplexityTime', state.complexityTime ?? managerProblem.complexity?.time ?? '');
        setElValue('managerComplexitySpace', state.complexitySpace ?? managerProblem.complexity?.space ?? '');
        setElValue('managerReferenceSolution', state.referenceSolution ?? managerProblem.reference_solution ?? managerProblem.solution ?? '');
        setElValue('managerJson', state.json || stringifyProblemJson(managerProblem));
        setElValue('managerTagInput', state.tagInput ?? (managerProblem.tags || []).join(', '));
        setElValue('managerInlineTagInput', state.inlineTagInput ?? state.tagInput ?? (managerProblem.tags || []).join(', '));
        activeManagerTestCaseIndex = Number.isFinite(Number(state.activeTestCaseIndex)) ? Number(state.activeTestCaseIndex) : activeManagerTestCaseIndex;
        renderManagerTestList();
        applyManagerTestEditorState(state.testEditors);
        setElHidden('managerAddTestCard', state.addTestCardHidden ?? true);
        setElValue('managerTestGroup', state.addTestGroup || 'visible_tests');
        setElValue('managerTestName', state.addTestName || '');
        setElValue('managerTestCode', state.addTestCode || 'from user_solution import Solution');
        setElValue('managerTestArgs', state.addTestArgs || '[]');
        setElValue('managerTestExpected', state.addTestExpected || 'null');
        applyManagerInputFieldState(state.inputFields);
        setElText('managerGeneratedOutput', state.generatedOutputText || 'Output will be generated when you add the test.');
        setElClass('managerGeneratedOutput', state.generatedOutputClass || 'empty');
        setElText('managerTestOutputNotice', state.testOutputNotice || '');
        setElHidden('managerTestOutputNotice', state.testOutputNoticeHidden ?? !state.testOutputNotice);
        setElValue('managerLlmRequest', state.llmRequest || '');
        setElValue('managerLlmProvider', state.llmProvider || elValue('managerLlmProvider'));
        setElValue('managerLlmModel', state.llmModel || elValue('managerLlmModel'));
        setElValue('managerLlmTestCount', state.llmTestCount || '3');
        setElValue('managerLlmTestGroup', state.llmTestGroup || managerLlmTestGroup);
        setElText('managerLlmOutput', state.llmOutputText || 'No LLM draft yet.');
        setElHidden('managerApplyLlmTests', state.llmApplyHidden ?? true);
        setManagerLearningSection(state.learningSection || 'problem');
        setManagerEditMode(state.editMode || 'edit');
        setManagerToolView(state.toolView || 'tags');
        syncManagerLearningPreviews();
        setElHtml('managerOutput', state.outputHtml || 'Open Manage to edit the current problem.');
        setElClass('managerStatus', state.statusClass || 'badge');
        setElText('managerStatus', state.statusText || (managerIsNewDraft ? 'Draft' : 'Loaded'));
        setElHidden('managerStatus', state.statusHidden ?? false);
        managerDirty = Boolean(state.dirty);
      } finally {
        restoringUiState = false;
      }
      return true;
    }

    function clearManageDraftState() {
      managerDirty = false;
      managerIsNewDraft = false;
      removeSessionState(MANAGE_STATE_KEY);
    }

    function markManagerDirty() {
      if (restoringUiState) return;
      managerDirty = true;
    }

    function saveCreateState() {
      const existing = readSessionState(CREATE_STATE_KEY) || {};
      const hasCreateContent = Boolean(
        elValue('llmProblemRequest').trim()
        || elValue('llmDraftJson').trim()
        || (elText('llmOutput') && elText('llmOutput') !== 'No LLM request yet.')
        || (elText('llmDecisionOutput') && elText('llmDecisionOutput') !== 'Generated drafts stay here until you add them to the library.')
        || createPreviewProblems.length
      );
      if (!hasCreateContent && !createDirty && !existing.dirty) {
        removeSessionState(CREATE_STATE_KEY);
        return;
      }
      writeSessionState(CREATE_STATE_KEY, {
        currentMode: createConversationMode || 'agent',
        activeCreatePreviewSection,
        createPrimaryCopyText,
        llmProblemRequest: elValue('llmProblemRequest'),
        llmProvider: elValue('llmProvider'),
        llmModel: elValue('llmModel'),
        llmProblemCount: elValue('llmProblemCount'),
        llmTimeoutSeconds: elValue('llmTimeoutSeconds'),
        llmOutputText: elText('llmOutput'),
        llmOutputClass: elClass('llmOutput'),
        directInstructionHidden: elHidden('directJsonInstructionBubble'),
        directInstructionTitle: elText('directJsonInstructionTitle'),
        directInstructions: elText('directJsonInstructions'),
        llmDraftJson: elValue('llmDraftJson'),
        llmOverwrite: Boolean(document.getElementById('llmOverwrite')?.checked),
        llmDecisionStatusText: elText('llmDecisionStatus'),
        llmDecisionStatusClass: elClass('llmDecisionStatus'),
        llmDecisionStatusHidden: elHidden('llmDecisionStatus'),
        llmDecisionOutputText: elText('llmDecisionOutput'),
        llmPreviewHtml: elHtml('llmPreview'),
        llmPreviewStatusText: elText('llmPreviewStatus'),
        llmPreviewStatusClass: elClass('llmPreviewStatus'),
        llmPreviewStatusHidden: elHidden('llmPreviewStatus'),
        llmDepsText: elText('llmDepsStatus'),
        llmDepsClass: elClass('llmDepsStatus'),
        llmDepsHidden: elHidden('llmDepsStatus'),
        llmResultView,
        createVerifierOpen,
        createPreviewProblems: cloneJson(createPreviewProblems),
        lastCreateValidationResult: cloneJson(lastCreateValidationResult),
        dirty: createDirty,
      });
    }

    function restoreCreateState() {
      const state = readSessionState(CREATE_STATE_KEY);
      if (!state) return false;
      restoringUiState = true;
      try {
        createConversationMode = state.currentMode === 'direct' ? 'direct' : 'agent';
        updateCreateModeUi();
        activeCreatePreviewSection = state.activeCreatePreviewSection || activeCreatePreviewSection || 'problem';
        createPrimaryCopyText = state.createPrimaryCopyText || '';
        setElValue('llmProblemRequest', state.llmProblemRequest || '');
        setElValue('llmProvider', state.llmProvider || elValue('llmProvider'));
        setElValue('llmModel', state.llmModel || elValue('llmModel'));
        setElValue('llmProblemCount', state.llmProblemCount || '1');
        setElValue('llmTimeoutSeconds', state.llmTimeoutSeconds || '180');
        setElText('llmOutput', state.llmOutputText || 'No LLM request yet.');
        setElClass('llmOutput', state.llmOutputClass || 'author-output chat-output');
        setElHidden('directJsonInstructionBubble', state.directInstructionHidden ?? (createConversationMode !== 'direct'));
        setElText('directJsonInstructionTitle', state.directInstructionTitle || (createConversationMode === 'direct' ? 'How to use' : ''));
        setElText('directJsonInstructions', state.directInstructions || '');
        setElValue('llmDraftJson', state.llmDraftJson || '');
        setElChecked('llmOverwrite', state.llmOverwrite);
        setElText('llmDecisionStatus', state.llmDecisionStatusText || 'Waiting');
        setElClass('llmDecisionStatus', state.llmDecisionStatusClass || 'badge');
        setElHidden('llmDecisionStatus', state.llmDecisionStatusHidden ?? false);
        setElText('llmDecisionOutput', state.llmDecisionOutputText || 'Generated drafts stay here until you add them to the library.');
        setElHtml('llmPreview', state.llmPreviewHtml || '<div class="empty">Generate a draft to preview the problem, theory, worked examples, solution, and tests.</div>');
        setElText('llmPreviewStatus', state.llmPreviewStatusText || 'No draft');
        setElClass('llmPreviewStatus', state.llmPreviewStatusClass || 'badge');
        setElHidden('llmPreviewStatus', state.llmPreviewStatusHidden ?? true);
        setElText('llmDepsStatus', state.llmDepsText || 'Not checked');
        setElClass('llmDepsStatus', state.llmDepsClass || 'badge');
        setElHidden('llmDepsStatus', state.llmDepsHidden ?? true);
        createPreviewProblems = Array.isArray(state.createPreviewProblems) ? state.createPreviewProblems : [];
        lastCreateValidationResult = state.lastCreateValidationResult || null;
        setCreatePreviewSection(activeCreatePreviewSection);
        setLlmResultView(state.llmResultView || 'preview');
        createVerifierOpen = Boolean(state.createVerifierOpen);
        const copyButton = document.getElementById('llmPrimaryCopyButton');
        if (copyButton) {
          copyButton.hidden = !createPrimaryCopyText;
          copyButton.dataset.copyLength = String(createPrimaryCopyText.length);
          copyButton.classList.remove('copied');
          const label = copyButton.querySelector('span:last-child');
          if (label) label.textContent = 'Copy';
        }
        clearLlmAttachments();
        createDirty = Boolean(state.dirty);
      } finally {
        restoringUiState = false;
      }
      return true;
    }

    function clearCreateDraftState() {
      createDirty = false;
      removeSessionState(CREATE_STATE_KEY);
    }

    function markCreateDirty() {
      if (restoringUiState) return;
      createDirty = true;
    }

    function bindDirtyStateTracking() {
      const markForTarget = target => {
        if (!(target instanceof Element)) return;
        if (target.id === 'llmApiKey' || target.id === 'managerLlmApiKey') return;
        if (target.id === 'code' || target.closest('.practice-editor-shell')) {
          markPracticeDirty();
          return;
        }
        if (target.closest('#managerPanel')) {
          markManagerDirty();
          return;
        }
        if (target.closest('#llmView')) {
          markCreateDirty();
        }
      };
      document.addEventListener('input', event => markForTarget(event.target));
      document.addEventListener('change', event => markForTarget(event.target));
    }

    function restoreInitialAppMode() {
      const shell = readSessionState(SHELL_STATE_KEY) || {};
      const createState = readSessionState(CREATE_STATE_KEY);
      const manageState = readSessionState(MANAGE_STATE_KEY);
      if (shell.mode === 'manage' && manageState) {
        setAppMode('manage');
        return;
      }
      if (shell.mode === 'problems') {
        setAppMode('problems');
        return;
      }
      if (shell.mode === 'llm' || shell.mode === 'create' || createState?.dirty) {
        setAppMode('llm');
        return;
      }
      setAppMode('practice');
      if (['solution', 'runtime', 'history'].includes(shell.view)) {
        setView(shell.view);
      }
    }

"""
