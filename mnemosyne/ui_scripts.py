from __future__ import annotations

import json
from pathlib import Path

APP_UI_TEXT_JSON = json.dumps(json.loads((Path(__file__).parent / "ui_copy" / "ui_text.json").read_text(encoding="utf-8")), ensure_ascii=False)
from mnemosyne.ui_js import (
    CREATE_CHAT_SCRIPT,
    CREATE_DIRECT_JSON_SCRIPT,
    CREATE_LLM_SCRIPT,
    LLM_STATUS_SCRIPT,
    MANAGE_SCRIPT,
    PRACTICE_LEARNING_SCRIPT,
    PRACTICE_RUNNER_SCRIPT,
    PROBLEM_LIST_SCRIPT,
    UI_STATE_SCRIPT,
    VERIFIER_FEEDBACK_SCRIPT,
)

"""Browser-side behavior for the Mnemosyne single-page UI.

This remains plain JavaScript by design: easy to inspect, easy to run locally, and checked by node --check in regression tests.
"""

APP_SCRIPT = (
    f"""    window.MNEMOSYNE_UI_TEXT = {APP_UI_TEXT_JSON};
"""
    + r"""    let currentProblem = null;
    let currentSyntax = {ok: true};
    let checkTimer = null;
    let checkCounter = 0;
    let solutionLoadedFor = null;
    let allProblems = [];
    let tagSummaries = [];
    let activeCatalogTag = '';
    let catalogSearchQuery = '';
    let runtimeState = null;
    let directJsonPromptLoaded = false;
    let directJsonPromptText = '';
    let managerSelectedProblemId = null;
    let managerProblem = null;
    let managerIsNewDraft = false;
    let managerToolView = 'tags';
    let managerLearningSection = 'problem';
    let managerEditMode = 'edit';
    let activeManagerTestCaseIndex = 0;
    let llmState = null;
    let llmSessionApiKey = '';
    let llmResultView = 'preview';
    let llmAttachmentFiles = [];
    let directJsonUploadedDraft = null;
    let createConversationMode = 'agent';
    let activeCreatePreviewSection = 'problem';
    let createPrimaryCopyText = '';
    let createChatCopyTexts = {};
    let createChatMessageCounter = 0;
    let createVerifierOpen = false;
    let createPreviewProblems = [];
    let lastCreateValidationResult = null;
    let managerLlmTestDrafts = [];
    let managerLlmTestGroup = 'visible_tests';
    let activePracticeCaseIndex = 0;
    let activeLearningSection = 'problem';
    let learningSolutionLoadedFor = null;
    let practiceConsoleView = 'tests';
    let latestPracticeRun = null;
    let codeMirrorEditor = null;
    let loadProblemRequestId = 0;
    try {
      sessionStorage.removeItem('local_leetcode_llm_api_key');
      sessionStorage.removeItem('mnemosyne_llm_api_key');
    } catch {}

"""
    + UI_STATE_SCRIPT
    + r"""    function uiText(path, fallback = '') {
      const parts = String(path || '').split('.').filter(Boolean);
      let value = window.MNEMOSYNE_UI_TEXT || {};
      for (const part of parts) {
        if (!value || typeof value !== 'object' || !(part in value)) return fallback;
        value = value[part];
      }
      return typeof value === 'string' ? value : fallback;
    }

    function uiTextList(path, fallback = []) {
      const parts = String(path || '').split('.').filter(Boolean);
      let value = window.MNEMOSYNE_UI_TEXT || {};
      for (const part of parts) {
        if (!value || typeof value !== 'object' || !(part in value)) return fallback;
        value = value[part];
      }
      return Array.isArray(value) ? value.map(item => String(item)) : fallback;
    }

    function formatUiText(path, fallback = '', values = {}) {
      return templateText(uiText(path, fallback), values);
    }

    function templateText(text, values = {}) {
      return String(text || '').replace(/\{([A-Za-z0-9_]+)\}/g, (_, key) => String(values[key] ?? ''));
    }

    function setView(view) {
      const viewIds = ['code', 'catalog', 'manage', 'llm', 'solution', 'runtime', 'history'];
      const selected = viewIds.includes(view) ? view : 'code';
      if (!restoringUiState && selected !== currentView) {
        snapshotCurrentUiState();
      }
      viewIds.forEach(name => {
        const pane = document.getElementById(`${name}View`);
        if (pane) pane.hidden = name !== selected;
      });

      const tabs = {
        code: 'codeTab',
        solution: 'solutionTab',
        runtime: 'runtimeTab',
        history: 'historyTab',
      };
      Object.entries(tabs).forEach(([name, tabId]) => {
        const tab = document.getElementById(tabId);
        if (tab) tab.classList.toggle('active', name === selected);
      });

      if (selected === 'solution') loadSolution();
      if (selected === 'runtime') loadRuntimeStatus();
      if (selected === 'history') {
        loadCurrentHistory();
        loadAllHistory();
        loadWrongProblems();
      }
      if (selected === 'code') {
        restorePracticeState();
        setTimeout(() => codeMirrorEditor?.refresh(), 0);
      }
      currentView = selected;
    }

    function setAppMode(mode) {
      snapshotCurrentUiState();
      document.body.dataset.mode = mode;
      document.getElementById('practiceModeTab').classList.toggle('active', mode === 'practice');
      document.getElementById('problemsModeTab').classList.toggle('active', mode === 'problems');
      document.getElementById('manageModeTab').classList.toggle('active', mode === 'manage');
      document.getElementById('llmModeTab').classList.toggle('active', mode === 'llm' || mode === 'create');

      if (mode === 'practice') {
        setView('code');
        return;
      }

      if (mode === 'problems') {
        setView('catalog');
        renderCatalog();
        return;
      }

      if (mode === 'manage') {
        setView('manage');
        loadManagerWorkspace();
        return;
      }

      if (mode === 'llm') {
        setView('llm');
        loadLlmPanel();
        return;
      }

      if (mode === 'create') {
        setView('llm');
        const hasCreateState = Boolean(readSessionState(CREATE_STATE_KEY));
        setCreateConversationMode('direct', {reset: !hasCreateState});
      }
    }

"""
    + PRACTICE_LEARNING_SCRIPT
    + PROBLEM_LIST_SCRIPT
    + MANAGE_SCRIPT
    + LLM_STATUS_SCRIPT
    + CREATE_DIRECT_JSON_SCRIPT
    + CREATE_LLM_SCRIPT
    + CREATE_CHAT_SCRIPT
    + VERIFIER_FEEDBACK_SCRIPT
    + r"""    async function postJson(url, payload, method = 'POST') {
      const res = await fetch(url, {
        method,
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
      });
      return await res.json();
    }

    function cleanModelJsonText(text) {
      let cleaned = String(text || '').trim().replace(/^\\uFEFF/, '').trim();
      const fenced = cleaned.match(/^```(?:json|JSON)?\\s*\\n?([\\s\\S]*?)\\n?```\\s*$/);
      if (fenced) {
        cleaned = fenced[1].trim();
      } else {
        const [start, end] = jsonTextBounds(cleaned);
        if (start >= 0 && end > start && (start > 0 || end < cleaned.length - 1)) {
          cleaned = cleaned.slice(start, end + 1).trim();
        }
      }
      return cleaned
        .replace(/[“”„‟]/g, '"')
        .replace(/[‘’‚‛]/g, "'");
    }

    function jsonTextBounds(text) {
      const candidates = [
        [text.indexOf('{'), text.lastIndexOf('}')],
        [text.indexOf('['), text.lastIndexOf(']')],
      ].filter(([start, end]) => start >= 0 && end > start);
      if (!candidates.length) return [-1, -1];
      return candidates.sort((a, b) => a[0] - b[0])[0];
    }

    function stringifyProblemJson(value) {
      return formatCompactJson(value, 0);
    }

    function stringifyEditableJson(value) {
      return formatJsonInline(value);
    }

    function formatCompactJson(value, level = 0) {
      const inline = formatJsonInline(value);
      if (shouldInlineJson(value, inline)) return inline;

      const pad = '  '.repeat(level);
      const childPad = '  '.repeat(level + 1);
      if (Array.isArray(value)) {
        if (!value.length) return '[]';
        const items = value.map(item => formatCompactJson(item, level + 1));
        return `[\n${items.map(item => childPad + item).join(',\n')}\n${pad}]`;
      }
      if (value && typeof value === 'object') {
        const entries = Object.entries(value);
        if (!entries.length) return '{}';
        const lines = entries.map(([key, item]) => (
          `${childPad}${JSON.stringify(key)}: ${formatCompactJson(item, level + 1)}`
        ));
        return `{\n${lines.join(',\n')}\n${pad}}`;
      }
      return inline;
    }

    function formatJsonInline(value) {
      if (value === undefined) return 'null';
      if (value === null || typeof value !== 'object') return JSON.stringify(value);
      if (Array.isArray(value)) return `[${value.map(formatJsonInline).join(', ')}]`;
      return `{${Object.entries(value).map(([key, item]) => `${JSON.stringify(key)}: ${formatJsonInline(item)}`).join(', ')}}`;
    }

    function shouldInlineJson(value, inline) {
      if (!value || typeof value !== 'object') return true;
      if (String(inline).includes('\n')) return false;
      if (Array.isArray(value)) return inline.length <= 160 && value.every(item => !item || typeof item !== 'object' || !Array.isArray(item) || formatJsonInline(item).length <= 120);
      if (isTestCaseLike(value)) return inline.length <= 320;
      return inline.length <= 120 && Object.values(value).every(item => !item || typeof item !== 'object' || formatJsonInline(item).length <= 80);
    }

    function isTestCaseLike(value) {
      if (!value || Array.isArray(value) || typeof value !== 'object') return false;
      return 'name' in value && (('args' in value && 'expected' in value) || 'code' in value);
    }

    function setCreatePreviewSection(section) {
      const allowed = ['problem', 'theory', 'example', 'solution'];
      activeCreatePreviewSection = allowed.includes(section) ? section : 'problem';
      allowed.forEach(name => {
        const tab = document.getElementById(`createPreview${titleCase(name)}Tab`);
        if (tab) tab.classList.toggle('active', name === activeCreatePreviewSection);
      });
      renderCreatePreviewFromState();
    }

    function resetCreatePreview(message) {
      createPreviewProblems = [];
      lastCreateValidationResult = null;
      const status = document.getElementById('llmPreviewStatus');
      const box = document.getElementById('llmPreview');
      if (status) {
        status.className = 'badge';
        status.textContent = 'No draft';
      }
      if (box) box.innerHTML = `<div class="empty">${escapeHtml(message || 'No draft yet.')}</div>`;
      setCreatePreviewSection(activeCreatePreviewSection || 'problem');
    }

    function renderCreatePreview(result) {
      lastCreateValidationResult = result || null;
      createPreviewProblems = result?.problems?.length ? result.problems : result?.problem ? [result.problem] : [];
      const status = document.getElementById('llmPreviewStatus');
      const box = document.getElementById('llmPreview');
      if (!status || !box) return;
      if (!createPreviewProblems.length) {
        status.className = 'badge error';
        status.textContent = 'No preview';
        box.innerHTML = '<div class="empty">No valid problem JSON to preview yet.</div>';
        return;
      }
      status.className = result?.ok ? 'badge ok' : 'badge error';
      status.textContent = result?.ok
        ? createPreviewProblems.length === 1 ? 'Ready to add' : `${createPreviewProblems.length} ready to add`
        : 'Needs fixes';
      renderCreatePreviewFromState();
    }

    function renderCreatePreviewFromState() {
      const box = document.getElementById('llmPreview');
      if (!box) return;
      if (!createPreviewProblems.length) return;
      box.innerHTML = createPreviewProblems.map((problem, idx) => renderCreateProblemSection(problem, activeCreatePreviewSection, idx, createPreviewProblems.length)).join('');
      typesetMath(box);
    }

    function renderCreateProblemSection(problem, section, idx, total) {
      const tags = (problem.tags || []).map(t => renderClickableTag(t)).join('');
      const heading = `
        <div class="create-problem-heading">
          <div>
            <h2 class="problem-title">${escapeHtml(problem.title || problem.id || 'Untitled')}</h2>
            <div class="problem-card-meta">
              <span class="tag difficulty">${escapeHtml(problem.difficulty || 'unknown')}</span>
              <span class="tag">${escapeHtml(problem.entry_kind || 'function')}</span>
              ${tags}
            </div>
          </div>
          ${total > 1 ? `<span class="badge">Problem ${idx + 1}/${total}</span>` : ''}
        </div>
      `;
      let body = '';
      if (section === 'theory') {
        body = `<div class="statement">${renderTheorySection(problem)}</div>`;
      } else if (section === 'example') {
        body = `<div class="statement">${renderExampleSection(problem)}</div>`;
      } else if (section === 'solution') {
        body = renderCreateSolutionSection(problem);
      } else {
        body = `
          <div class="statement">${markdownLite(problem.statement || '')}</div>
          ${renderProblemExamplesPreview(problem)}
        `;
      }
      return `<article class="create-problem-preview">${heading}${body}</article>`;
    }

    function renderProblemExamplesPreview(problem) {
      const tests = problem?.visible_tests || [];
      if (!tests.length) return '';
      const rendered = tests.map((t, idx) => {
        const name = t.name ? `: ${t.name}` : '';
        if (problem.entry_kind === 'function') {
          const input = formatFunctionCall(problem, t.args || []);
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
      return `<h2 class="section-title">Examples</h2><div class="test-list">${rendered}</div>`;
    }

    function renderCreateSolutionSection(problem) {
      const complexity = problem.complexity || {};
      const complexityHtml = complexity.time || complexity.space ? `
        <div class="test-card">
          <div class="test-name">Complexity</div>
          <div class="kv">
            <div><strong>Time:</strong> ${escapeHtml(complexity.time || 'Not set')}</div>
            <div><strong>Space:</strong> ${escapeHtml(complexity.space || 'Not set')}</div>
          </div>
        </div>
      ` : '';
      const explanation = problem.solution_explanation
        ? `<div class="test-card"><div class="test-name">Solution</div><div class="statement">${markdownLite(problem.solution_explanation)}</div></div>`
        : '<div class="learning-empty">No solution explanation has been added yet.</div>';
      const code = problem.reference_solution || problem.solution || '';
      const codeHtml = code
        ? `<div class="test-card"><div class="test-name">reference_solution.py</div><pre class="solution-code">${escapeHtml(code)}</pre></div>`
        : '<div class="empty">No reference solution has been added yet.</div>';
      return `${explanation}${complexityHtml}${codeHtml}`;
    }

    function renderProblemPreview(problem, {includeAnswer = false, includeTests = false} = {}) {
      const tags = (problem.tags || []).map(t => renderClickableTag(t)).join('');
      const visible = problem.visible_tests || [];
      const constraints = (problem.constraints || []).map(c => `<li>${escapeHtml(c)}</li>`).join('');
      const checker = problem.checker ? `<span class="tag">checker: ${escapeHtml(problem.checker.type || 'exact')}</span>` : '';
      const theoryText = problem.theory || problem.theory_markdown || problem.algorithm_theory || '';
      const theory = theoryText ? `<div class="test-card"><div class="test-name">Theory</div><div class="statement">${markdownLite(theoryText)}</div></div>` : '';
      const examplesHtml = renderExampleSection(problem);
      const examples = examplesHtml ? `<div class="test-card"><div class="test-name">Example</div><div class="statement">${examplesHtml}</div></div>` : '';
      const complexity = problem.complexity || {};
      const complexityCard = complexity.time || complexity.space ? `
        <div class="test-card">
          <div class="test-name">Complexity</div>
          <div class="kv">
            <div><strong>Time:</strong> ${escapeHtml(complexity.time || 'Not set')}</div>
            <div><strong>Space:</strong> ${escapeHtml(complexity.space || 'Not set')}</div>
          </div>
        </div>
      ` : '';
      const answer = includeAnswer ? `
        ${problem.solution_explanation ? `<div class="test-card"><div class="test-name">Solution</div><div class="statement">${markdownLite(problem.solution_explanation)}</div></div>` : ''}
        ${complexityCard}
        <div class="test-card">
          <div class="test-name">Reference solution</div>
          <pre class="solution-code">${escapeHtml(problem.reference_solution || problem.solution || 'No reference solution yet.')}</pre>
        </div>
      ` : '';
      const tests = includeTests ? `
        <div class="test-card">
          <div class="test-name">Explicit tests</div>
          <div class="kv">
            <div><strong>Tests:</strong> ${escapeHtml(visible.length)}</div>
          </div>
          <details><summary>visible_tests</summary><pre>${escapeHtml(stringifyProblemJson(visible))}</pre></details>
        </div>
      ` : '';
      return `
        <div class="test-card">
          <div class="problem-card-title">
            <span>${escapeHtml(problem.title || problem.id || 'Untitled')}</span>
            <span class="badge">${escapeHtml(problem.difficulty || 'unknown')}</span>
          </div>
          <div class="problem-card-meta">
            <span class="tag">${escapeHtml(problem.entry_kind || 'function')}</span>
            ${checker}
            ${tags}
          </div>
        </div>
        ${constraints ? `<div class="test-card"><div class="test-name">Constraints</div><ul>${constraints}</ul></div>` : ''}
        <div class="preview-statement statement">${markdownLite(problem.statement || '')}</div>
        ${theory}
        ${examples}
        ${answer}
        ${tests}
      `;
    }

    function markdownLite(source) {
      const lines = String(source || '').replace(/\r\n/g, '\n').split('\n');
      const blocks = [];
      let i = 0;

      while (i < lines.length) {
        const line = lines[i];
        const trimmed = line.trim();
        if (!trimmed) {
          i += 1;
          continue;
        }

        if (trimmed.startsWith('```')) {
          const lang = trimmed.slice(3).trim();
          const code = [];
          i += 1;
          while (i < lines.length && !lines[i].trim().startsWith('```')) {
            code.push(lines[i]);
            i += 1;
          }
          i += i < lines.length ? 1 : 0;
          blocks.push(`<pre class="md-code"><code class="language-${escapeHtml(lang)}">${escapeHtml(code.join('\n'))}</code></pre>`);
          continue;
        }

        const oneLineDisplayMath = trimmed.match(/^\$\$(.+)\$\$$/) || trimmed.match(/^\\\[(.+)\\\]$/);
        if (oneLineDisplayMath) {
          blocks.push(renderMathBlock(oneLineDisplayMath[1].trim()));
          i += 1;
          continue;
        }

        if (trimmed === '$$' || trimmed === '\\[') {
          const closing = trimmed === '$$' ? '$$' : '\\]';
          const math = [];
          i += 1;
          while (i < lines.length && lines[i].trim() !== closing) {
            math.push(lines[i]);
            i += 1;
          }
          i += i < lines.length ? 1 : 0;
          blocks.push(renderMathBlock(math.join('\n')));
          continue;
        }

        const heading = trimmed.match(/^(#{1,4})\s+(.+)$/);
        if (heading) {
          const level = Math.min(4, heading[1].length + 1);
          blocks.push(`<h${level}>${renderInlineMarkdown(heading[2])}</h${level}>`);
          i += 1;
          continue;
        }

        if (trimmed.startsWith('> ')) {
          const quote = [];
          while (i < lines.length && lines[i].trim().startsWith('> ')) {
            quote.push(lines[i].trim().slice(2));
            i += 1;
          }
          blocks.push(`<blockquote>${quote.map(renderInlineMarkdown).join('<br>')}</blockquote>`);
          continue;
        }

        if (/^[-*]\s+/.test(trimmed)) {
          const items = [];
          while (i < lines.length && /^[-*]\s+/.test(lines[i].trim())) {
            items.push(`<li>${renderInlineMarkdown(lines[i].trim().replace(/^[-*]\s+/, ''))}</li>`);
            i += 1;
          }
          blocks.push(`<ul>${items.join('')}</ul>`);
          continue;
        }

        if (/^\d+\.\s+/.test(trimmed)) {
          const items = [];
          while (i < lines.length && /^\d+\.\s+/.test(lines[i].trim())) {
            items.push(`<li>${renderInlineMarkdown(lines[i].trim().replace(/^\d+\.\s+/, ''))}</li>`);
            i += 1;
          }
          blocks.push(`<ol>${items.join('')}</ol>`);
          continue;
        }

        if (isTableStart(lines, i)) {
          const table = [lines[i], lines[i + 1]];
          i += 2;
          while (i < lines.length && lines[i].includes('|') && lines[i].trim()) {
            table.push(lines[i]);
            i += 1;
          }
          blocks.push(renderMarkdownTable(table));
          continue;
        }

        const paragraph = [trimmed];
        i += 1;
        while (i < lines.length && lines[i].trim() && !startsMarkdownBlock(lines, i)) {
          paragraph.push(lines[i].trim());
          i += 1;
        }
        blocks.push(`<p>${renderInlineMarkdown(paragraph.join(' '))}</p>`);
      }

      return blocks.join('\n');
    }

    function startsMarkdownBlock(lines, idx) {
      const s = lines[idx].trim();
      return s.startsWith('```')
        || s === '$$'
        || s === '\\['
        || /^#{1,4}\s+/.test(s)
        || /^[-*]\s+/.test(s)
        || /^\d+\.\s+/.test(s)
        || s.startsWith('> ')
        || isTableStart(lines, idx);
    }

    function isTableStart(lines, idx) {
      if (idx + 1 >= lines.length) return false;
      if (!lines[idx].includes('|')) return false;
      return /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(lines[idx + 1]);
    }

    function renderMarkdownTable(tableLines) {
      const rows = tableLines.map(splitTableRow);
      const head = rows[0] || [];
      const body = rows.slice(2);
      const thead = `<tr>${head.map(cell => `<th>${renderInlineMarkdown(cell)}</th>`).join('')}</tr>`;
      const tbody = body.map(row => `<tr>${row.map(cell => `<td>${renderInlineMarkdown(cell)}</td>`).join('')}</tr>`).join('');
      return `<table><thead>${thead}</thead><tbody>${tbody}</tbody></table>`;
    }

    function splitTableRow(line) {
      return line.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map(cell => cell.trim());
    }

    function renderInlineMarkdown(source) {
      let text = String(source || '');
      const placeholders = [];
      const stash = html => {
        const key = `@@MD_PLACEHOLDER_${placeholders.length}@@`;
        placeholders.push([key, html]);
        return key;
      };

      text = text.replace(/`([^`]+)`/g, (_, code) => stash(`<code>${escapeHtml(code)}</code>`));
      text = text.replace(/\\\[([^\n]+?)\\\]/g, (_, tex) => stash(renderMathInline(tex)));
      text = text.replace(/\$\$([^$\n]+?)\$\$/g, (_, tex) => stash(renderMathInline(tex)));
      text = text.replace(/\\\((.+?)\\\)/g, (_, tex) => stash(renderMathInline(tex)));
      text = text.replace(/\$([^$\n]+?)\$/g, (_, tex) => stash(renderMathInline(tex)));

      let html = escapeHtml(text)
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/\*([^*]+)\*/g, '<em>$1</em>')
        .replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noreferrer">$1</a>');

      for (const [key, value] of placeholders) {
        html = html.replaceAll(key, value);
      }
      return html;
    }

    function renderMathInline(tex) {
      const clean = String(tex || '').trim();
      return `<span class="math-inline" data-tex="${escapeHtml(clean)}">\\(${escapeHtml(clean)}\\)</span>`;
    }

    function renderMathBlock(tex) {
      const clean = String(tex || '').trim();
      return `<div class="math-block" data-tex="${escapeHtml(clean)}">\\[${escapeHtml(clean)}\\]</div>`;
    }

    function renderMathFallback(root) {
      if (!root) return;
      root.querySelectorAll?.('.math-inline[data-tex], .math-block[data-tex]').forEach(node => {
        if (node.dataset.mathRendered === 'fallback') return;
        const tex = node.dataset.tex || node.textContent || '';
        node.innerHTML = simpleLatexFallback(tex);
        node.dataset.mathRendered = 'fallback';
        node.classList.add('math-fallback');
      });
    }

    function simpleLatexFallback(tex) {
      let html = escapeHtml(String(tex || '').replace(/^\\[([]/, '').replace(/\\[)\]]$/, '').trim());
      html = html
        .replace(/\\operatorname\{([^{}]+)\}/g, '$1')
        .replace(/\\mathrm\{([^{}]+)\}/g, '$1')
        .replace(/\\begin\{bmatrix\}/g, '[')
        .replace(/\\end\{bmatrix\}/g, ']')
        .replace(/\\mathbb\{R\}/g, 'ℝ')
        .replace(/\\mathbb\{N\}/g, 'ℕ')
        .replace(/\\mathbb\{Z\}/g, 'ℤ')
        .replace(/\\theta/g, 'θ')
        .replace(/\\lambda/g, 'λ')
        .replace(/\\alpha/g, 'α')
        .replace(/\\beta/g, 'β')
        .replace(/\\sigma/g, 'σ')
        .replace(/\\mu/g, 'μ')
        .replace(/\\pi/g, 'π')
        .replace(/\\bar\{([^{}]+)\}/g, (_, value) => `${value}\u0304`)
        .replace(/\\cdots/g, '⋯')
        .replace(/\\sum/g, '∑')
        .replace(/\\frac\{([^{}]+)\}\{([^{}]+)\}/g, '<span class="math-frac"><span>$1</span><span>$2</span></span>')
        .replace(/\\cdot/g, '·')
        .replace(/\\times/g, '×')
        .replace(/\\leq/g, '≤')
        .replace(/\\geq/g, '≥')
        .replace(/\\neq/g, '≠')
        .replace(/\\le/g, '≤')
        .replace(/\\ge/g, '≥')
        .replace(/\\ne/g, '≠')
        .replace(/\\leftarrow/g, '←')
        .replace(/\\to/g, '→')
        .replace(/\\in/g, '∈')
        .replace(/\s*&amp;\s*/g, ', ')
        .replace(/\\\\/g, '; ');
      html = html.replace(/\^\{([^{}]+)\}/g, (_, value) => `<sup>${mathScriptText(value)}</sup>`);
      html = html.replace(/_\{([^{}]+)\}/g, (_, value) => `<sub>${mathScriptText(value)}</sub>`);
      html = html.replace(/\^([A-Za-z0-9+\-=]+)/g, (_, value) => `<sup>${mathScriptText(value)}</sup>`);
      html = html.replace(/_([A-Za-z0-9+\-=]+)/g, (_, value) => `<sub>${mathScriptText(value)}</sub>`);
      html = html.replace(/\\([A-Za-z]+)/g, '$1');
      return html;
    }

    function mathScriptText(value) {
      return String(value || '').replace(/-/g, '−');
    }

    const pendingMathTypeset = new Set();
    let mathTypesetTimer = null;
    let mathTypesetRetries = 0;

    function typesetMath(element) {
      if (!element) return;
      pendingMathTypeset.add(element);
      scheduleMathTypeset();
    }

    function scheduleMathTypeset() {
      clearTimeout(mathTypesetTimer);
      mathTypesetTimer = setTimeout(flushMathTypeset, 40);
    }

    function flushMathTypeset() {
      if (!pendingMathTypeset.size) return;
      const targets = [...pendingMathTypeset].filter(element => element && document.body.contains(element));
      if (!targets.length) {
        pendingMathTypeset.clear();
        return;
      }
      if (!window.MathJax || !window.MathJax.typesetPromise) {
        mathTypesetRetries += 1;
        if (mathTypesetRetries >= 12) {
          pendingMathTypeset.clear();
          targets.forEach(renderMathFallback);
          mathTypesetRetries = 0;
          return;
        }
        scheduleMathTypeset();
        return;
      }
      pendingMathTypeset.clear();
      mathTypesetRetries = 0;
      try {
        window.MathJax.typesetClear?.(targets);
        window.MathJax.typesetPromise(targets).catch(() => targets.forEach(renderMathFallback));
      } catch {
        targets.forEach(renderMathFallback);
      }
    }

    function escapeHtml(value) {
      return String(value ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
    }

    function escapeJs(value) {
      return String(value ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll('\\', '\\\\')
        .replaceAll("'", "\\'")
        .replaceAll('\n', '\\n')
        .replaceAll('\r', '\\r');
    }

    function renderIoBlock(label, text) {
      const full = String(text ?? '');
      const compact = compactDisplayText(full);
      if (compact !== full) {
        return `
          <div class="io-block">
            <div class="io-label">${escapeHtml(label)}</div>
            <details class="io-details">
              <summary class="io-summary">${escapeHtml(compact)}</summary>
              <pre>${escapeHtml(full)}</pre>
            </details>
          </div>
        `;
      }
      return `
        <div class="io-block">
          <div class="io-label">${escapeHtml(label)}</div>
          <pre>${escapeHtml(full)}</pre>
        </div>
      `;
    }

    function renderValueBlock(label, value) {
      const full = formatPythonValue(value);
      const compact = formatPythonValueCompact(value);
      if (compact !== full) {
        return `
          <div class="io-block">
            <div class="io-label">${escapeHtml(label)}</div>
            <details class="io-details">
              <summary class="io-summary">${escapeHtml(compact)}</summary>
              <pre>${escapeHtml(full)}</pre>
            </details>
          </div>
        `;
      }
      return renderIoBlock(label, full);
    }

    function formatFunctionCall(problem, args, options = {}) {
      const fn = problem?.function_name || problem?.id || 'solution';
      const names = functionArgNames(problem);
      const parts = (args || []).map((arg, idx) => {
        const prefix = names[idx] ? `${names[idx]}=` : '';
        return `${prefix}${options.compact ? formatPythonValueCompact(arg, 120) : formatPythonValue(arg)}`;
      });
      const oneLine = `${fn}(${parts.join(', ')})`;
      if (options.compact) return compactDisplayText(oneLine, 220);
      if (oneLine.length <= 88 && !oneLine.includes('\n')) return oneLine;
      return `${fn}(\n${parts.map(part => indentLines(part, '  ')).join(',\n')}\n)`;
    }

    function functionArgNames(problem) {
      const fn = problem?.function_name || '';
      const code = problem?.starter_code || '';
      if (!fn || !code) return [];
      const match = code.match(new RegExp(`def\\s+${escapeRegExp(fn)}\\s*\\(([^)]*)\\)`));
      if (!match) return [];
      return match[1]
        .split(',')
        .map(part => part.trim().split('=')[0].trim())
        .filter(name => name && name !== 'self' && !name.startsWith('*'));
    }

    function formatPythonValue(value, level = 0) {
      if (value === null) return 'None';
      if (typeof value === 'boolean') return value ? 'True' : 'False';
      if (typeof value === 'number') return Number.isFinite(value) ? String(value) : reprString(String(value));
      if (typeof value === 'string') return reprString(value);

      if (Array.isArray(value)) {
        if (!value.length) return '[]';
        const items = value.map(item => formatPythonValue(item, level + 1));
        const inline = `[${items.join(', ')}]`;
        const hasNestedArray = value.some(Array.isArray);
        if (!hasNestedArray && !inline.includes('\n') && inline.length <= 72) return inline;
        const pad = '  '.repeat(level);
        const childPad = '  '.repeat(level + 1);
        return `[\n${items.map(item => childPad + item.replaceAll('\n', `\n${childPad}`)).join(',\n')}\n${pad}]`;
      }

      if (typeof value === 'object') {
        const entries = Object.entries(value);
        if (!entries.length) return '{}';
        const items = entries.map(([key, val]) => `${reprString(key)}: ${formatPythonValue(val, level + 1)}`);
        const inline = `{${items.join(', ')}}`;
        if (!inline.includes('\n') && inline.length <= 72) return inline;
        const pad = '  '.repeat(level);
        const childPad = '  '.repeat(level + 1);
        return `{\n${items.map(item => childPad + item.replaceAll('\n', `\n${childPad}`)).join(',\n')}\n${pad}}`;
      }

      return String(value);
    }

    function formatPythonValueCompact(value, maxLength = 220) {
      return compactDisplayText(formatPythonValueOneLine(value), maxLength);
    }

    function formatPythonValueOneLine(value) {
      if (value === null) return 'None';
      if (typeof value === 'boolean') return value ? 'True' : 'False';
      if (typeof value === 'number') return Number.isFinite(value) ? String(value) : reprString(String(value));
      if (typeof value === 'string') return reprString(value);
      if (Array.isArray(value)) return `[${value.map(formatPythonValueOneLine).join(', ')}]`;
      if (typeof value === 'object') {
        const entries = Object.entries(value || {});
        return `{${entries.map(([key, val]) => `${reprString(key)}: ${formatPythonValueOneLine(val)}`).join(', ')}}`;
      }
      return String(value);
    }

    function compactDisplayText(text, maxLength = 220) {
      const flat = String(text ?? '').replace(/\s+/g, ' ').trim();
      return flat.length <= maxLength ? flat : `${flat.slice(0, Math.max(0, maxLength - 1))}…`;
    }

    function formatValue(value) {
      return formatPythonValue(value);
    }

    function indentLines(text, prefix) {
      return prefix + String(text).replaceAll('\n', `\n${prefix}`);
    }

    function reprString(value) {
      return JSON.stringify(String(value));
    }

    function escapeRegExp(value) {
      return String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    function titleCase(value) {
      const text = String(value || '');
      return text ? text[0].toUpperCase() + text.slice(1) : '';
    }

    function formatTime(iso) {
      if (!iso) return '';
      const d = new Date(iso);
      if (Number.isNaN(d.getTime())) return iso;
      return d.toLocaleString();
    }

    function clampNumber(value, min, max) {
      return Math.min(max, Math.max(min, value));
    }

    function beginSplitterDrag(splitter, event) {
      splitter.classList.add('dragging');
      splitter.setPointerCapture(event.pointerId);
      document.body.style.userSelect = 'none';
      event.preventDefault();
    }

    function endSplitterDrag(splitter, event) {
      splitter.classList.remove('dragging');
      document.body.style.userSelect = '';
      if (event?.pointerId !== undefined) {
        try {
          splitter.releasePointerCapture(event.pointerId);
        } catch {
          // Pointer capture may already be released by the browser.
        }
      }
      setTimeout(() => codeMirrorEditor?.refresh(), 0);
    }

    function initMainSplitter() {
      const splitter = document.getElementById('mainSplitter');
      const layout = document.querySelector('.layout');
      if (!splitter || !layout) return;

      let dragging = false;
      splitter.addEventListener('pointerdown', event => {
        dragging = true;
        beginSplitterDrag(splitter, event);
      });

      splitter.addEventListener('pointermove', event => {
        if (!dragging) return;
        const rect = layout.getBoundingClientRect();
        const left = clampNumber(event.clientX - rect.left, 300, Math.max(300, rect.width - 380));
        layout.style.setProperty('--main-left', `${left}px`);
        setTimeout(() => codeMirrorEditor?.refresh(), 0);
      });

      const stopDragging = event => {
        if (!dragging) return;
        dragging = false;
        endSplitterDrag(splitter, event);
      };

      splitter.addEventListener('pointerup', stopDragging);
      splitter.addEventListener('pointercancel', stopDragging);
    }

    function initColumnSplitter(splitterId, containerSelector, cssVar, options = {}) {
      const splitter = document.getElementById(splitterId);
      const container = document.querySelector(containerSelector);
      if (!splitter || !container) return;
      const minLeft = options.minLeft || 320;
      const minRight = options.minRight || 320;

      let dragging = false;
      splitter.addEventListener('pointerdown', event => {
        dragging = true;
        beginSplitterDrag(splitter, event);
      });

      splitter.addEventListener('pointermove', event => {
        if (!dragging) return;
        const rect = container.getBoundingClientRect();
        if (rect.width <= 0) return;
        const maxLeft = Math.max(minLeft, rect.width - minRight);
        const left = clampNumber(event.clientX - rect.left, minLeft, maxLeft);
        container.style.setProperty(cssVar, `${left}px`);
        setTimeout(() => codeMirrorEditor?.refresh(), 0);
      });

      const stopDragging = event => {
        if (!dragging) return;
        dragging = false;
        endSplitterDrag(splitter, event);
      };

      splitter.addEventListener('pointerup', stopDragging);
      splitter.addEventListener('pointercancel', stopDragging);
    }

    function initPracticeVerticalSplitter() {
      const splitter = document.getElementById('practiceVerticalSplitter');
      const workspace = document.querySelector('.practice-workspace');
      if (!splitter || !workspace) return;

      let dragging = false;
      splitter.addEventListener('pointerdown', event => {
        dragging = true;
        beginSplitterDrag(splitter, event);
      });

      splitter.addEventListener('pointermove', event => {
        if (!dragging) return;
        const rect = workspace.getBoundingClientRect();
        if (rect.height <= 0) return;
        const actionBarHeight = workspace.querySelector('.practice-action-bar')?.getBoundingClientRect().height || 40;
        const splitterHeight = splitter.getBoundingClientRect().height || 12;
        const actionAndSplitter = actionBarHeight + splitterHeight;
        const minConsole = 120;
        const minEditor = 150;
        const maxConsole = Math.max(minConsole, rect.height - actionAndSplitter - minEditor);
        const consoleHeight = clampNumber(rect.bottom - event.clientY, minConsole, maxConsole);
        workspace.style.setProperty('--practice-console-height', `${consoleHeight}px`);
        setTimeout(() => codeMirrorEditor?.refresh(), 0);
      });

      const stopDragging = event => {
        if (!dragging) return;
        dragging = false;
        endSplitterDrag(splitter, event);
      };

      splitter.addEventListener('pointerup', stopDragging);
      splitter.addEventListener('pointercancel', stopDragging);
    }

    function initCreateVerifierSplitter() {
      const splitter = document.getElementById('createVerifierSplitter');
      const pane = document.querySelector('.create-preview-pane');
      if (!splitter || !pane) return;

      let dragging = false;
      splitter.addEventListener('pointerdown', event => {
        dragging = true;
        pane.dataset.verifierHeightTouched = 'true';
        beginSplitterDrag(splitter, event);
      });

      splitter.addEventListener('pointermove', event => {
        if (!dragging) return;
        const rect = pane.getBoundingClientRect();
        if (rect.height <= 0) return;
        const headerHeight = pane.querySelector('.create-preview-header')?.getBoundingClientRect().height || 48;
        const tabsHeight = pane.querySelector('.create-preview-tabs-bar')?.getBoundingClientRect().height || 44;
        const splitterHeight = splitter.getBoundingClientRect().height || 10;
        const minPreview = 170;
        const minVerifier = 150;
        const fixedHeight = headerHeight + tabsHeight + splitterHeight;
        const maxVerifier = Math.max(minVerifier, rect.height - fixedHeight - minPreview);
        const verifierHeight = clampNumber(rect.bottom - event.clientY, minVerifier, maxVerifier);
        pane.style.setProperty('--create-verifier-height', `${verifierHeight}px`);
      });

      const stopDragging = event => {
        if (!dragging) return;
        dragging = false;
        endSplitterDrag(splitter, event);
      };

      splitter.addEventListener('pointerup', stopDragging);
      splitter.addEventListener('pointercancel', stopDragging);
    }

    window.addEventListener('load', () => {
      initCodeEditor();
      flushMathTypeset();
    });
    window.addEventListener('beforeunload', event => {
      snapshotCurrentUiState();
      if (!hasUnsavedUiState()) return;
      event.preventDefault();
      event.returnValue = '';
      return '';
    });
    bindDirtyStateTracking();
    initMainSplitter();
    initColumnSplitter('createModuleSplitter', '.create-workspace', '--create-left', {minLeft: 320, minRight: 320});
    initColumnSplitter('manageModuleSplitter', '.manage-split', '--manage-left', {minLeft: 320, minRight: 320});
    initPracticeVerticalSplitter();
    initCreateVerifierSplitter();
    loadProblems();"""
    + PRACTICE_RUNNER_SCRIPT
)
