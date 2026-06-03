from __future__ import annotations

"""Practice-page run flow, syntax checks, result/error panes, history tables, and code editor wiring."""

PRACTICE_RUNNER_SCRIPT = r"""    async function submitCode(mode) {
      if (!currentProblem) return;
      setPracticeConsoleView('result');
      document.getElementById('status').textContent = 'Checking...';
      const syntax = await validateCode({quiet: false});
      if (!syntax.ok) {
        renderSyntaxStop(syntax);
        document.getElementById('status').textContent = 'Fix syntax first.';
        return;
      }

      document.getElementById('status').textContent = 'Running...';
      document.getElementById('resultMeta').className = 'badge';
      document.getElementById('resultMeta').textContent = 'Running tests';
      latestPracticeRun = null;
      document.getElementById('result').innerHTML = '<div class="empty">Running tests...</div>';
      renderPracticeErrorEmpty('Running code...');
      const res = await fetch('/api/submit', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          problem_id: currentProblem.id,
          code: getCodeValue(),
          mode
        })
      });
      const data = await res.json();
      renderResult(data, mode);
      document.getElementById('status').textContent = `Saved as submission #${data.submission_id}`;
      await loadCurrentHistory();
      await loadAllHistory();
      await loadWrongProblems();
    }

    async function validateCode({quiet = true} = {}) {
      const token = ++checkCounter;
      if (!quiet) {
        document.getElementById('diagnostic').className = 'diagnostic';
        document.getElementById('diagnostic').textContent = 'Checking Python syntax...';
      }
      const res = await fetch('/api/check-code', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({code: getCodeValue()})
      });
      const data = await res.json();
      if (token !== checkCounter) return currentSyntax;
      currentSyntax = data;
      renderDiagnostic(data);
      return data;
    }

    function renderDiagnostic(data) {
      const diagnostic = document.getElementById('diagnostic');
      const badge = document.getElementById('syntaxBadge');
      if (data.ok) {
        diagnostic.className = 'diagnostic ok';
        diagnostic.textContent = data.message || 'Python syntax OK';
        badge.className = 'badge ok';
        badge.textContent = 'Syntax OK';
        updateLineNumbers();
        return;
      }
      const lineText = data.text ? `<pre>${escapeHtml(data.text)}</pre>` : '';
      diagnostic.className = 'diagnostic error';
      diagnostic.innerHTML = `
        <strong>${escapeHtml(data.error_type || 'SyntaxError')}</strong>
        ${data.line ? ` on line ${escapeHtml(data.line)}` : ''}: ${escapeHtml(data.message || 'Invalid Python syntax')}
        ${lineText}
      `;
      badge.className = 'badge error';
      badge.textContent = data.line ? `Line ${data.line}` : 'Syntax error';
      updateLineNumbers(data.line);
    }

    function renderSyntaxStop(data) {
      document.getElementById('resultMeta').className = 'badge error';
      document.getElementById('resultMeta').textContent = data.error_type || 'Syntax error';
      document.getElementById('result').innerHTML = `
        <div class="result-summary-card failed">
          <div>
            <div class="result-title status-text wrong">Compile Error</div>
            <div class="result-subtitle">Python parser stopped before tests could run.</div>
          </div>
          <span class="badge error">${escapeHtml(data.error_type || 'SyntaxError')}</span>
        </div>
        <div class="empty">Open the Error tab for the parser message.</div>
      `;
      renderSyntaxErrorPanel(data);
      setPracticeConsoleView('error');
      document.getElementById('practiceResultPane')?.scrollTo({top: 0});
    }

    function runtimeDetailEntries(data, tests) {
      if (!data || data.status === 'Accepted') return [];
      const dependencyStatus = data.metadata?.dependency_status || null;
      const installCommand = dependencyStatus?.install_command || '';
      const errorTitle = data.status === 'Missing Dependencies' ? 'Missing dependencies' : 'Runtime error';
      const details = [];
      if (data.error) {
        const installLine = installCommand ? `

Install command:
${installCommand}` : '';
        details.push([errorTitle, data.error + installLine]);
      }
      (tests || []).forEach((test, idx) => {
        if (!test?.error) return;
        const title = test.name ? `Case ${idx + 1}: ${test.name}` : `Case ${idx + 1} traceback`;
        if (!details.some(([, text]) => text === test.error)) details.push([title, test.error]);
      });
      if (data.stderr) details.push(['stderr', data.stderr]);
      if (data.stdout && !String(data.stdout).includes('__JUDGE_RESULT__=')) details.push(['stdout', data.stdout]);
      return details;
    }

    function renderRuntimeDetailCards(data, tests) {
      return runtimeDetailEntries(data, tests).slice(0, 3).map(([title, text]) => `
        <div class="case-card failed runtime-detail-card">
          <div class="case-title"><span>${escapeHtml(title)}</span><span class="status-text wrong">failed</span></div>
          <pre>${escapeHtml(sanitizeLocalPaths(text))}</pre>
        </div>
      `).join('');
    }

    function renderPracticeErrorEmpty(message = uiText('practice.no_program_errors', 'No program errors yet.')) {
      const box = document.getElementById('practiceError');
      if (!box) return;
      box.innerHTML = `<div class="empty">${escapeHtml(message)}</div>`;
    }

    function renderSyntaxErrorPanel(data) {
      const box = document.getElementById('practiceError');
      if (!box) return;
      const line = data.line ? `Line ${escapeHtml(data.line)}` : 'Syntax check';
      const body = `${data.message || 'Invalid Python syntax'}${data.text ? '\\n\\n' + data.text : ''}`;
      box.innerHTML = `
        <div class="result-summary-card failed">
          <div>
            <div class="result-title status-text wrong">${escapeHtml(data.error_type || 'SyntaxError')}</div>
            <div class="result-subtitle">${line}</div>
          </div>
          <span class="badge error">Error</span>
        </div>
        <div class="case-list">
          <div class="case-card failed runtime-detail-card">
            <div class="case-title"><span>${line}</span><span class="status-text wrong">failed</span></div>
            <pre>${escapeHtml(body)}</pre>
          </div>
        </div>
      `;
      document.getElementById('practiceErrorPane')?.scrollTo({top: 0});
    }

    function renderPracticeErrorPanel(data) {
      const box = document.getElementById('practiceError');
      if (!box) return;
      const tests = data?.tests || [];
      const details = runtimeDetailEntries(data, tests);
      if (!details.length) {
        box.innerHTML = `
          <div class="result-summary-card accepted">
            <div>
              <div class="result-title status-text accepted">No Program Error</div>
              <div class="result-subtitle">${escapeHtml(data?.status || 'Run finished')}</div>
            </div>
            <span class="badge ok">Clear</span>
          </div>
          <div class="empty">Wrong answers still appear in Test Result. This panel only shows syntax, runtime, stderr, stdout, and dependency errors.</div>
        `;
        document.getElementById('practiceErrorPane')?.scrollTo({top: 0});
        return;
      }
      box.innerHTML = `
        <div class="result-summary-card failed">
          <div>
            <div class="result-title status-text wrong">Program Error</div>
            <div class="result-subtitle">${escapeHtml(data.status || 'Run failed')}</div>
          </div>
          <span class="badge error">${escapeHtml(details.length)} item${details.length === 1 ? '' : 's'}</span>
        </div>
        <div class="case-list">
          ${details.map(([title, text]) => `
            <div class="case-card failed runtime-detail-card">
              <div class="case-title"><span>${escapeHtml(title)}</span><span class="status-text wrong">error</span></div>
              <pre>${escapeHtml(sanitizeLocalPaths(text))}</pre>
            </div>
          `).join('')}
        </div>
      `;
      document.getElementById('practiceErrorPane')?.scrollTo({top: 0});
    }

    function renderResult(data, mode = 'run') {
      const accepted = data.status === 'Accepted';
      const resultMeta = document.getElementById('resultMeta');
      resultMeta.className = accepted ? 'badge ok' : 'badge error';
      resultMeta.textContent = `#${data.submission_id || '-'} ${data.passed}/${data.total}`;

      latestPracticeRun = data;
      const tests = data.tests || [];
      const cards = tests.map((t, idx) => {
        return renderRunCaseCard(t, idx, currentProblem, mode, {includeErrors: false});
      }).join('');
      const caseStrip = tests.length ? `
        <div class="result-case-strip">
          ${tests.map((test, idx) => `
            <span class="case-tab ${test.passed ? 'passed' : 'failed'}">Case ${idx + 1}</span>
          `).join('')}
        </div>
      ` : '';

      const detailCards = cards || '<div class="empty">No test details returned.</div>';

      document.getElementById('result').innerHTML = `
        <div class="result-summary-card ${accepted ? 'accepted' : 'failed'}">
          <div>
            <div class="result-title status-text ${accepted ? 'accepted' : 'wrong'}">${escapeHtml(data.status)}</div>
            <div class="result-subtitle">Explicit tests · submission #${escapeHtml(data.submission_id || '')}</div>
          </div>
          <span class="badge ${accepted ? 'ok' : 'error'}">${escapeHtml(data.passed)}/${escapeHtml(data.total)} passed</span>
        </div>
        ${caseStrip}
        <div class="case-list">${detailCards}</div>
      `;
      renderPracticeErrorPanel(data);
      if (runtimeDetailEntries(data, tests).length) {
        setPracticeConsoleView('error');
      }
      document.getElementById('practiceResultPane')?.scrollTo({top: 0});
    }

    async function loadCurrentHistory() {
      if (!currentProblem) return;
      const res = await fetch(`/api/submissions?problem_id=${encodeURIComponent(currentProblem.id)}&limit=50`);
      const data = await res.json();
      renderSubmissionTable('currentHistoryTable', data.submissions || []);
    }

    async function loadAllHistory() {
      const res = await fetch('/api/submissions?limit=100');
      const data = await res.json();
      renderSubmissionTable('allHistoryTable', data.submissions || []);
    }

    async function loadWrongProblems() {
      const res = await fetch('/api/wrong-problems');
      const data = await res.json();
      renderWrongProblemsTable(data.wrong_problems || []);
    }

    function renderSubmissionTable(tableId, rows) {
      const table = document.getElementById(tableId);
      if (!rows.length) {
        table.innerHTML = '<tr><td class="empty">No submissions yet.</td></tr>';
        return;
      }
      table.innerHTML = `
        <tr>
          <th>ID</th><th>Problem</th><th>Mode</th><th>Status</th><th>Passed</th><th>Time</th><th></th>
        </tr>
        ${rows.map(r => {
          const klass = r.status === 'Accepted' ? 'accepted' : 'wrong';
          return `<tr>
            <td>#${escapeHtml(r.id)}</td>
            <td>${escapeHtml(r.problem_title)}</td>
            <td>${escapeHtml(r.mode)}</td>
            <td class="status-text ${klass}">${escapeHtml(r.status)}</td>
            <td>${escapeHtml(r.passed)}/${escapeHtml(r.total)}</td>
            <td>${escapeHtml(formatTime(r.created_at))}</td>
            <td><button class="small" onclick="loadSubmissionDetail(${escapeHtml(r.id)})"><span class="material-symbols-outlined" aria-hidden="true">visibility</span><span>Detail</span></button></td>
          </tr>`;
        }).join('')}
      `;
    }

    function renderWrongProblemsTable(rows) {
      const table = document.getElementById('wrongProblemsTable');
      if (!rows.length) {
        table.innerHTML = '<tr><td class="empty">No wrong submissions yet.</td></tr>';
        return;
      }
      table.innerHTML = `
        <tr>
          <th>Problem</th><th>Wrong count</th><th>Latest status</th><th>Latest result</th><th>Latest time</th><th></th>
        </tr>
        ${rows.map(r => {
          const klass = r.latest_status === 'Accepted' ? 'accepted' : 'wrong';
          return `<tr>
            <td>${escapeHtml(r.problem_title)}</td>
            <td>${escapeHtml(r.wrong_count)}</td>
            <td class="status-text ${klass}">${escapeHtml(r.latest_status)}</td>
            <td>${escapeHtml(r.latest_passed)}/${escapeHtml(r.latest_total)}</td>
            <td>${escapeHtml(formatTime(r.latest_created_at))}</td>
            <td><button class="small" onclick="loadSubmissionDetail(${escapeHtml(r.latest_submission_id)})"><span class="material-symbols-outlined" aria-hidden="true">visibility</span><span>Latest</span></button></td>
          </tr>`;
        }).join('')}
      `;
    }

    async function loadSubmissionDetail(id) {
      const res = await fetch(`/api/submissions/${id}`);
      const data = await res.json();
      const failedTests = (data.result?.tests || []).filter(t => !t.passed);
      const view = {
        id: data.id,
        problem_id: data.problem_id,
        problem_title: data.problem_title,
        mode: data.mode,
        status: data.status,
        passed: `${data.passed}/${data.total}`,
        created_at: data.created_at,
        failed_tests: failedTests,
        result: data.result,
        code: data.code,
      };
      document.getElementById('submissionDetail').textContent = JSON.stringify(view, null, 2);
      setView('history');
    }

    const codeEl = () => document.getElementById('code');

    function getCodeValue() {
      return codeMirrorEditor ? codeMirrorEditor.getValue() : codeEl().value;
    }

    function setCodeValue(value) {
      const text = String(value ?? '');
      codeEl().value = text;
      if (codeMirrorEditor && codeMirrorEditor.getValue() !== text) {
        codeMirrorEditor.setValue(text);
        codeMirrorEditor.refresh();
      }
    }

    function resetCurrentCode() {
      if (!currentProblem) return;
      setCodeValue(currentProblem.starter_code || '');
      markPracticeDirty();
      document.getElementById('diagnostic').textContent = 'Starter code restored.';
      document.getElementById('diagnostic').className = 'diagnostic';
      document.getElementById('result').innerHTML = `<div class="empty">${escapeHtml(uiText('practice.run_to_see_results', 'Run your code to see test results.'))}</div>`;
      document.getElementById('resultMeta').textContent = 'No submission';
      document.getElementById('status').textContent = '';
      activePracticeCaseIndex = 0;
      renderPracticeTestcases();
      updateCursorStatus();
      queueCheck();
    }

    function initCodeEditor() {
      if (codeMirrorEditor || !window.CodeMirror || !codeEl()) return;
      codeMirrorEditor = window.CodeMirror.fromTextArea(codeEl(), {
        mode: 'python',
        theme: 'default',
        lineNumbers: true,
        indentUnit: 4,
        tabSize: 4,
        indentWithTabs: false,
        matchBrackets: true,
        autoCloseBrackets: true,
        lineWrapping: false,
        viewportMargin: Infinity,
        extraKeys: {
          Tab(editor) {
            if (editor.somethingSelected()) {
              editor.indentSelection('add');
            } else {
              editor.replaceSelection(' '.repeat(editor.getOption('indentUnit')), 'end');
            }
          },
        },
      });
      document.querySelector('.practice-editor-shell .editor-body')?.classList.add('cm-enabled');
      codeMirrorEditor.on('change', editor => {
        codeEl().value = editor.getValue();
        markPracticeDirty();
        updateLineNumbers();
        updateCursorStatus();
        queueCheck();
      });
      codeMirrorEditor.on('cursorActivity', updateCursorStatus);
      codeMirrorEditor.on('focus', updateCursorStatus);
      setTimeout(() => codeMirrorEditor?.refresh(), 0);
      updateCursorStatus();
    }

    codeEl()?.addEventListener('input', () => {
      markPracticeDirty();
      updateLineNumbers();
      updateCursorStatus();
      queueCheck();
    });

    function updateLineNumbers(errorLine = null) {
      if (codeMirrorEditor) return;
      const code = getCodeValue() || '';
      const count = Math.max(1, code.split('\n').length);
      const html = Array.from({length: count}, (_, i) => {
        const line = i + 1;
        const klass = Number(errorLine) === line ? 'line error-line' : 'line';
        return `<div class="${klass}">${line}</div>`;
      }).join('');
      document.getElementById('lineNumbers').innerHTML = html;
    }

    function updateCursorStatus() {
      const status = document.getElementById('cursorStatus');
      if (!status) return;
      if (codeMirrorEditor) {
        const cursor = codeMirrorEditor.getCursor();
        status.textContent = `Ln ${cursor.line + 1}, Col ${cursor.ch + 1}`;
        return;
      }
      const el = codeEl();
      if (!el) return;
      const pos = el.selectionStart ?? 0;
      const before = el.value.slice(0, pos);
      const line = before.split('\n').length;
      const lastBreak = before.lastIndexOf('\n');
      const col = pos - lastBreak;
      status.textContent = `Ln ${line}, Col ${col}`;
    }

    function queueCheck() {
      clearTimeout(checkTimer);
      currentSyntax = {ok: false, stale: true};
      document.getElementById('diagnostic').className = 'diagnostic';
      document.getElementById('diagnostic').textContent = 'Syntax not checked after latest edit.';
      document.getElementById('syntaxBadge').className = 'badge';
      document.getElementById('syntaxBadge').textContent = 'Unchecked';
    }

"""
