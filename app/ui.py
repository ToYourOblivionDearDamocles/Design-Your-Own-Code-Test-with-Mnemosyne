from __future__ import annotations

APP_HTML = r'''
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Mnemosyne</title>
  <script>
    window.MathJax = {
      tex: {
        inlineMath: [['\\(', '\\)']],
        displayMath: [['\\[', '\\]']],
        processEscapes: true
      },
      options: {
        skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code']
      },
      startup: {
        typeset: false
      }
    };
  </script>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/codemirror@5/lib/codemirror.css" />
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/codemirror@5/theme/material-darker.css" />
  <script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/codemirror@5/lib/codemirror.js"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/codemirror@5/mode/python/python.js"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/codemirror@5/addon/edit/matchbrackets.js"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/codemirror@5/addon/edit/closebrackets.js"></script>
  <style>
    :root {
      color-scheme: light;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      --bg: #f5f6f8;
      --panel: #ffffff;
      --line: #d9dde5;
      --line-soft: #eaedf2;
      --text: #1f2328;
      --muted: #6b7280;
      --accent: #2563eb;
      --accepted: #047857;
      --wrong: #b42318;
      --editor: #151515;
      --editor-gutter: #202020;
      --editor-text: #f4f4f5;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
    }

    button, select, textarea {
      font: inherit;
    }

    button {
      border: 1px solid var(--line);
      background: #fff;
      color: var(--text);
      border-radius: 8px;
      padding: 7px 12px;
      cursor: pointer;
    }

    button.primary {
      background: var(--accent);
      border-color: var(--accent);
      color: white;
      font-weight: 650;
    }

    button.ghost {
      background: transparent;
    }

    button.tab {
      border: 0;
      border-radius: 0;
      padding: 12px 14px;
      background: transparent;
      color: var(--muted);
      border-bottom: 2px solid transparent;
    }

    button.tab.active {
      color: var(--text);
      border-bottom-color: var(--accent);
      font-weight: 650;
    }

    select {
      min-width: 230px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 7px 10px;
      background: white;
      color: var(--text);
    }

    .topbar {
      height: 54px;
      display: flex;
      align-items: center;
      gap: 14px;
      padding: 0 18px;
      background: var(--panel);
      border-bottom: 1px solid var(--line);
    }

    .brand {
      display: flex;
      flex-direction: column;
      gap: 1px;
      font-weight: 760;
      letter-spacing: 0;
      white-space: nowrap;
      line-height: 1.05;
    }

    .brand-subtitle {
      color: var(--muted);
      font-size: 11px;
      font-weight: 620;
    }

    .topbar-spacer {
      flex: 1;
    }

    .top-nav {
      display: flex;
      align-items: center;
      gap: 4px;
    }

    .top-nav button {
      border: 0;
      background: transparent;
      color: var(--muted);
      font-weight: 650;
      padding: 8px 10px;
    }

    .top-nav button.active {
      color: var(--accent);
      background: #eff6ff;
    }

    body[data-mode="problems"] .layout,
    body[data-mode="manage"] .layout,
    body[data-mode="create"] .layout,
    body[data-mode="llm"] .layout {
      grid-template-columns: 1fr;
    }

    body[data-mode="problems"] .problem-pane,
    body[data-mode="manage"] .problem-pane,
    body[data-mode="create"] .problem-pane,
    body[data-mode="llm"] .problem-pane,
    body[data-mode="problems"] .work-tabs,
    body[data-mode="manage"] .work-tabs,
    body[data-mode="create"] .work-tabs,
    body[data-mode="llm"] .work-tabs,
    body[data-mode="problems"] .language-pill,
    body[data-mode="manage"] .language-pill,
    body[data-mode="create"] .language-pill,
    body[data-mode="llm"] .language-pill,
    body[data-mode="problems"] #problemSelect,
    body[data-mode="manage"] #problemSelect,
    body[data-mode="create"] #problemSelect,
    body[data-mode="llm"] #problemSelect,
    body[data-mode="problems"] #syntaxBadge,
    body[data-mode="manage"] #syntaxBadge,
    body[data-mode="create"] #syntaxBadge,
    body[data-mode="llm"] #syntaxBadge {
      display: none;
    }

    body[data-mode="problems"] .work-pane,
    body[data-mode="manage"] .work-pane,
    body[data-mode="create"] .work-pane,
    body[data-mode="llm"] .work-pane {
      border-left: 0;
    }

    body[data-mode="problems"] .view,
    body[data-mode="manage"] .view,
    body[data-mode="create"] .view,
    body[data-mode="llm"] .view {
      height: calc(100vh - 54px);
    }

    .badge {
      display: inline-flex;
      align-items: center;
      min-height: 26px;
      padding: 3px 9px;
      border-radius: 999px;
      border: 1px solid var(--line);
      color: var(--muted);
      background: #fff;
      font-size: 12px;
      white-space: nowrap;
    }

    .badge.ok {
      border-color: #a7f3d0;
      color: var(--accepted);
      background: #ecfdf5;
    }

    .badge.error {
      border-color: #fecaca;
      color: var(--wrong);
      background: #fff1f2;
    }

    .layout {
      display: grid;
      grid-template-columns: minmax(360px, 44%) minmax(420px, 56%);
      height: calc(100vh - 54px);
    }

    .problem-pane,
    .work-pane {
      min-width: 0;
      min-height: 0;
      background: var(--panel);
    }

    .problem-pane {
      border-right: 1px solid var(--line);
      overflow: auto;
    }

    .problem-inner {
      max-width: 820px;
      margin: 0 auto;
      padding: 24px 28px 48px;
    }

    .problem-title {
      margin: 0 0 10px;
      font-size: 26px;
      line-height: 1.2;
      letter-spacing: 0;
    }

    .meta {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
      margin-bottom: 22px;
    }

    .tag {
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      padding: 3px 9px;
      background: #f0f7ff;
      color: #1d4ed8;
      font-size: 12px;
    }

    .tag.tag-click {
      border: 0;
      cursor: pointer;
      font-weight: 600;
    }

    .tag.tag-click:hover {
      background: #dbeafe;
      color: #1e40af;
    }

    .difficulty {
      background: #ecfdf5;
      color: var(--accepted);
    }

    .statement {
      font-size: 15px;
      line-height: 1.72;
    }

    .statement h1,
    .statement h2,
    .statement h3 {
      margin: 20px 0 8px;
      line-height: 1.25;
      letter-spacing: 0;
    }

    .statement p {
      margin: 10px 0;
    }

    .statement ul,
    .statement ol {
      margin: 8px 0 12px 22px;
      padding: 0;
    }

    .statement blockquote {
      margin: 14px 0;
      padding: 8px 12px;
      border-left: 3px solid var(--line);
      color: var(--muted);
      background: #fbfcfe;
    }

    .statement pre.md-code {
      margin: 12px 0;
      padding: 12px;
      border-radius: 8px;
      background: #f6f8fa;
      border: 1px solid var(--line-soft);
      overflow: auto;
    }

    .statement pre.md-code code {
      border: 0;
      background: transparent;
      padding: 0;
      font-size: 13px;
    }

    .statement table {
      margin: 12px 0;
      border: 1px solid var(--line-soft);
      border-radius: 8px;
      overflow: hidden;
    }

    .math-inline {
      white-space: nowrap;
    }

    .math-block {
      margin: 14px 0;
      padding: 10px 12px;
      overflow-x: auto;
      border-radius: 8px;
      background: #fbfcfe;
      border: 1px solid var(--line-soft);
    }

    code {
      background: #f1f3f5;
      border: 1px solid #e5e7eb;
      padding: 1px 5px;
      border-radius: 5px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
      font-size: 0.92em;
    }

    .section-title {
      margin: 26px 0 12px;
      font-size: 16px;
      letter-spacing: 0;
    }

    .test-list {
      display: grid;
      gap: 10px;
    }

    .dependency-list {
      display: grid;
      gap: 8px;
    }

    .dependency-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      border: 1px solid var(--line-soft);
      border-radius: 8px;
      background: #fbfcfe;
      padding: 9px 10px;
      font-size: 13px;
    }

    .install-command {
      margin-top: 8px;
      border: 1px solid #fde68a;
      background: #fffbeb;
      color: #78350f;
      border-radius: 8px;
      padding: 9px 10px;
      font-size: 13px;
    }

    .test-card {
      border: 1px solid var(--line-soft);
      border-radius: 8px;
      background: #fbfcfe;
      padding: 12px;
    }

    .test-name {
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 8px;
    }

    .kv {
      display: grid;
      gap: 6px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
      font-size: 13px;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }

    .io-grid {
      display: grid;
      gap: 8px;
    }

    .io-label {
      margin-bottom: 4px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    .io-block pre {
      border: 1px solid var(--line-soft);
      border-radius: 8px;
      background: #fff;
      padding: 8px 10px;
      white-space: pre;
      overflow: auto;
      overflow-wrap: normal;
    }

    .manager-inputs {
      display: grid;
      gap: 10px;
    }

    .manager-input-fields {
      display: grid;
      gap: 8px;
    }

    .manager-input-row {
      display: grid;
      grid-template-columns: minmax(72px, 120px) minmax(0, 1fr);
      align-items: start;
      gap: 8px;
    }

    .manager-input-name {
      padding-top: 8px;
      color: var(--text);
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
      font-size: 13px;
      font-weight: 700;
    }

    .manager-input-row textarea {
      min-height: 38px;
      resize: vertical;
    }

    .work-pane {
      display: grid;
      grid-template-rows: auto minmax(0, 1fr);
    }

    .work-tabs {
      display: flex;
      align-items: center;
      gap: 4px;
      padding: 0 14px;
      border-bottom: 1px solid var(--line);
      background: #fff;
    }

    .language-pill {
      margin-left: auto;
      color: var(--muted);
      font-size: 13px;
    }

    .view {
      min-height: 0;
      overflow: auto;
      padding: 16px;
    }

    .view[hidden] {
      display: none;
    }

    .practice-workspace {
      min-height: 100%;
      display: grid;
      grid-template-rows: minmax(360px, 1fr) minmax(250px, auto);
      gap: 12px;
    }

    .practice-editor-card,
    .practice-console-card {
      min-width: 0;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      overflow: hidden;
    }

    .practice-editor-card {
      display: grid;
      grid-template-rows: auto minmax(0, 1fr) auto;
      min-height: 430px;
    }

    .practice-editor-toolbar,
    .practice-console-head {
      min-height: 44px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 8px 12px;
      border-bottom: 1px solid var(--line-soft);
      background: #fbfcfe;
    }

    .practice-editor-title,
    .console-tabs,
    .console-actions,
    .editor-meta {
      display: flex;
      align-items: center;
      gap: 8px;
      min-width: 0;
    }

    .practice-editor-title {
      font-weight: 750;
    }

    .code-mark {
      color: var(--accepted);
      font-weight: 800;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
    }

    .editor-meta {
      color: var(--muted);
      font-size: 12px;
      margin-left: auto;
    }

    .editor-meta-dot {
      color: #c5cbd3;
    }

    .practice-editor-shell {
      border: 0;
      border-radius: 0;
      box-shadow: none;
    }

    .practice-editor-shell .editor-body {
      height: 100%;
      min-height: 300px;
    }

    .editor-body.cm-enabled {
      display: block;
    }

    .editor-body.cm-enabled .line-numbers {
      display: none;
    }

    .editor-body.cm-enabled .CodeMirror {
      width: 100%;
      height: 100%;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
      font-size: 14px;
      line-height: 1.5;
      background: var(--editor);
    }

    .editor-body.cm-enabled .CodeMirror-gutters {
      background: var(--editor-gutter);
      border-right: 1px solid #303030;
    }

    .editor-body.cm-enabled .CodeMirror-linenumber {
      color: #8b8b8b;
    }

    .editor-footer {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      align-items: center;
      gap: 10px;
      padding: 8px 12px;
      border-top: 1px solid var(--line-soft);
      background: #fff;
    }

    .cursor-status {
      color: var(--muted);
      font-size: 12px;
      white-space: nowrap;
    }

    .console-tab {
      border: 0;
      border-radius: 0;
      padding: 8px 3px;
      background: transparent;
      color: var(--muted);
      font-weight: 700;
      border-bottom: 2px solid transparent;
    }

    .console-tab.active {
      color: var(--text);
      border-bottom-color: var(--accent);
    }

    .practice-console-pane[hidden] {
      display: none;
    }

    .practice-testcases {
      padding: 12px;
    }

    .case-tabs {
      display: flex;
      align-items: center;
      gap: 8px;
      overflow-x: auto;
      padding-bottom: 8px;
      margin-bottom: 4px;
    }

    .case-tab {
      flex: 0 0 auto;
      border: 0;
      border-radius: 8px;
      padding: 8px 12px;
      background: #f3f4f6;
      color: var(--muted);
      font-weight: 750;
    }

    .case-tab.active {
      background: #eef4ff;
      color: #1d4ed8;
    }

    .case-tab.passed {
      color: var(--accepted);
      background: #ecfdf5;
    }

    .case-tab.failed {
      color: var(--wrong);
      background: #fff1f2;
    }

    .practice-case-body {
      display: grid;
      gap: 10px;
    }

    .function-call-line {
      color: var(--muted);
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
      font-size: 13px;
      overflow-wrap: anywhere;
    }

    .console-field {
      display: grid;
      gap: 5px;
    }

    .console-field-label {
      color: var(--muted);
      font-size: 12px;
      font-weight: 750;
    }

    .console-field-value {
      border: 1px solid transparent;
      border-radius: 8px;
      background: #f5f6f8;
      padding: 10px 12px;
      overflow: auto;
    }

    .result-summary-card {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      border: 1px solid var(--line-soft);
      border-radius: 8px;
      padding: 12px;
      background: #fbfcfe;
      margin-bottom: 12px;
    }

    .result-summary-card.accepted {
      border-color: #bbf7d0;
      background: #f0fdf4;
    }

    .result-summary-card.failed {
      border-color: #fecaca;
      background: #fff1f2;
    }

    .result-title {
      font-size: 18px;
      font-weight: 800;
      letter-spacing: 0;
    }

    .result-subtitle {
      margin-top: 3px;
      color: var(--muted);
      font-size: 12px;
    }

    .result-case-strip {
      display: flex;
      align-items: center;
      gap: 8px;
      overflow-x: auto;
      padding-bottom: 6px;
      margin-bottom: 8px;
    }

    .editor-shell {
      border: 1px solid #2b2b2b;
      border-radius: 8px;
      overflow: hidden;
      background: var(--editor);
      box-shadow: 0 1px 2px rgba(0, 0, 0, 0.07);
    }

    .editor-header {
      height: 38px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 10px 0 14px;
      background: #242424;
      color: #d4d4d8;
      border-bottom: 1px solid #303030;
      font-size: 13px;
    }

    .editor-header button {
      padding: 4px 9px;
      border-color: #3f3f46;
      background: #2f2f2f;
      color: #e5e7eb;
      font-size: 12px;
    }

    .editor-body {
      display: grid;
      grid-template-columns: 54px minmax(0, 1fr);
      height: min(52vh, 560px);
      min-height: 320px;
    }

    .line-numbers {
      overflow: hidden;
      padding: 12px 0;
      background: var(--editor-gutter);
      color: #8b8b8b;
      border-right: 1px solid #303030;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
      font-size: 14px;
      line-height: 1.5;
      text-align: right;
      user-select: none;
    }

    .line-numbers .line {
      height: 21px;
      padding-right: 12px;
    }

    .line-numbers .line.error-line {
      color: #fecaca;
      background: #4a1d1d;
      font-weight: 700;
    }

    textarea.code-editor {
      width: 100%;
      height: 100%;
      border: 0;
      outline: 0;
      resize: none;
      padding: 12px 14px;
      background: var(--editor);
      color: var(--editor-text);
      caret-color: #ffffff;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
      font-size: 14px;
      line-height: 1.5;
      tab-size: 4;
      white-space: pre;
      overflow: auto;
    }

    .diagnostic {
      margin: 10px 0 12px;
      border: 1px solid var(--line);
      background: #fff;
      border-radius: 8px;
      padding: 10px 12px;
      color: var(--muted);
      font-size: 13px;
      min-height: 42px;
    }

    .editor-footer .diagnostic {
      margin: 0;
      min-height: 0;
      padding: 0;
      border: 0;
      background: transparent;
      color: var(--muted);
    }

    .editor-footer .diagnostic.ok {
      color: var(--accepted);
    }

    .editor-footer .diagnostic.error {
      color: var(--wrong);
    }

    .diagnostic.ok {
      border-color: #bbf7d0;
      background: #f0fdf4;
      color: var(--accepted);
    }

    .diagnostic.error {
      border-color: #fecaca;
      background: #fff1f2;
      color: var(--wrong);
    }

    .diagnostic pre {
      margin: 8px 0 0;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      color: #7f1d1d;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
    }

    .editor-footer .diagnostic pre {
      margin-top: 5px;
      max-height: 78px;
      overflow: auto;
    }

    .actions {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 14px;
      flex-wrap: wrap;
    }

    .status-line {
      min-height: 28px;
      color: var(--muted);
      font-size: 13px;
    }

    .result-panel,
    .history-panel {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      overflow: hidden;
    }

    .panel-head {
      min-height: 42px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      padding: 10px 12px;
      border-bottom: 1px solid var(--line-soft);
      background: #fbfcfe;
    }

    .panel-title {
      margin: 0;
      font-size: 14px;
      letter-spacing: 0;
    }

    .panel-body {
      padding: 12px;
    }

    .empty {
      color: var(--muted);
      font-size: 13px;
    }

    .validation-messages {
      display: grid;
      gap: 8px;
      margin-bottom: 12px;
    }

    .validation-message {
      border-radius: 8px;
      padding: 10px 12px;
      font-size: 13px;
      line-height: 1.45;
    }

    .validation-message.error {
      border: 1px solid #fecaca;
      background: #fff1f2;
      color: var(--wrong);
    }

    .validation-message.warning {
      border: 1px solid #fde68a;
      background: #fffbeb;
      color: #78350f;
    }

    .validation-message-title {
      font-weight: 700;
      margin-bottom: 6px;
    }

    .validation-message ul {
      margin: 0;
      padding-left: 18px;
    }

    .summary {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }

    .status-text {
      font-weight: 750;
    }

    .status-text.accepted {
      color: var(--accepted);
    }

    .status-text.wrong {
      color: var(--wrong);
    }

    .case-list {
      display: grid;
      gap: 10px;
      margin-top: 12px;
    }

    .case-card {
      border: 1px solid var(--line-soft);
      border-radius: 8px;
      padding: 10px;
      background: #fff;
    }

    .case-card.failed {
      border-color: #fecaca;
      background: #fff7f7;
    }

    .case-card.passed {
      border-color: #bbf7d0;
      background: #f8fffb;
    }

    .case-title {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
      margin-bottom: 8px;
      font-size: 13px;
      font-weight: 650;
    }

    .case-title-left {
      display: flex;
      align-items: center;
      gap: 8px;
      min-width: 0;
    }

    .case-dot {
      width: 9px;
      height: 9px;
      border-radius: 999px;
      background: var(--line);
      flex: 0 0 auto;
    }

    .case-card.passed .case-dot {
      background: var(--accepted);
    }

    .case-card.failed .case-dot {
      background: var(--wrong);
    }

    pre {
      margin: 0;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
      font-size: 13px;
      line-height: 1.45;
    }

    details {
      margin-top: 10px;
    }

    details summary {
      cursor: pointer;
      color: var(--muted);
      font-size: 13px;
    }

    .io-details {
      margin-top: 0;
    }

    .io-summary {
      border: 1px solid var(--line-soft);
      border-radius: 8px;
      background: #fff;
      padding: 8px 10px;
      color: var(--text);
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
      overflow-wrap: anywhere;
    }

    .io-details[open] .io-summary {
      border-bottom-left-radius: 0;
      border-bottom-right-radius: 0;
    }

    .history-grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 14px;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }

    th,
    td {
      border-bottom: 1px solid var(--line-soft);
      padding: 8px;
      text-align: left;
      vertical-align: top;
    }

    th {
      color: var(--muted);
      font-weight: 650;
      background: #fbfcfe;
    }

    tr:last-child td {
      border-bottom: 0;
    }

    .small {
      padding: 4px 8px;
      font-size: 12px;
    }

    .detail-box {
      max-height: 360px;
      overflow: auto;
    }

    .solution-grid {
      display: grid;
      gap: 14px;
    }

    .solution-code {
      border: 1px solid #2b2b2b;
      border-radius: 8px;
      background: var(--editor);
      color: var(--editor-text);
      padding: 14px;
      overflow: auto;
    }

    .catalog-layout {
      display: grid;
      grid-template-columns: 210px minmax(0, 1fr);
      gap: 14px;
      min-height: 100%;
    }

    .catalog-sidebar,
    .catalog-main {
      min-width: 0;
    }

    .catalog-sidebar {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      overflow: hidden;
      align-self: start;
    }

    .catalog-sidebar-head {
      padding: 10px 12px;
      border-bottom: 1px solid var(--line-soft);
      background: #fbfcfe;
      font-size: 13px;
      font-weight: 650;
    }

    .tag-filter {
      width: 100%;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      border: 0;
      border-radius: 0;
      border-bottom: 1px solid var(--line-soft);
      padding: 9px 12px;
      text-align: left;
      background: #fff;
      color: var(--text);
    }

    .tag-filter:last-child {
      border-bottom: 0;
    }

    .tag-filter.active {
      background: #eff6ff;
      color: #1d4ed8;
      font-weight: 700;
    }

    .tag-filter-count {
      color: var(--muted);
      font-size: 12px;
    }

    .catalog-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 12px;
    }

    .catalog-search {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 8px;
      margin-bottom: 12px;
    }

    .catalog-notice {
      margin-bottom: 12px;
      border: 1px solid #bfdbfe;
      border-radius: 8px;
      background: #eff6ff;
      color: #1e3a8a;
      padding: 9px 12px;
      font-size: 13px;
    }

    .catalog-title {
      margin: 0;
      font-size: 18px;
      letter-spacing: 0;
    }

    .problem-grid {
      display: grid;
      gap: 10px;
      margin-bottom: 14px;
    }

    .problem-card {
      width: 100%;
      display: block;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      padding: 12px;
      color: var(--text);
      text-align: left;
    }

    .problem-card:hover {
      border-color: #93c5fd;
      background: #fbfdff;
    }

    .problem-card-title {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 8px;
      font-weight: 750;
    }

    .problem-card-actions {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      flex-shrink: 0;
    }

    .problem-card-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }

    .manager-grid {
      display: grid;
      gap: 14px;
      align-items: start;
    }

    .manager-header-card {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
    }

    .manager-title {
      display: grid;
      gap: 3px;
      min-width: 0;
    }

    .manager-three-grid {
      display: grid;
      grid-template-columns: minmax(300px, 0.9fr) minmax(340px, 1fr) minmax(340px, 1fr);
      gap: 14px;
      align-items: start;
    }

    .manager-pane {
      min-width: 0;
    }

    .manager-tools {
      display: grid;
      gap: 14px;
    }

    .manager-tool-tabs {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 10px 12px 0;
      background: #fff;
    }

    .manager-tool-tabs button {
      padding: 5px 9px;
      font-size: 12px;
    }

    .manager-tool-tabs button.active {
      border-color: #bfdbfe;
      background: #eff6ff;
      color: #1d4ed8;
      font-weight: 700;
    }

    .manager-pane-section[hidden] {
      display: none;
    }

    .manager-json-textarea {
      min-height: 360px;
    }

    .manager-preview {
      display: grid;
      gap: 12px;
    }

    .manager-statement-editor,
    .manager-reference-editor {
      min-height: 340px;
      resize: vertical;
    }

    .manager-code-shell {
      border: 1px solid #2b2b2b;
      border-radius: 8px;
      overflow: hidden;
      background: var(--editor);
    }

    .manager-code-toolbar {
      height: 34px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      padding: 0 10px;
      border-bottom: 1px solid #303030;
      background: #242424;
      color: #d4d4d8;
      font-size: 12px;
    }

    .manager-code-shell .manager-reference-editor {
      display: block;
      width: 100%;
      height: 370px;
      min-height: 370px;
      border: 0;
      border-radius: 0;
      resize: vertical;
    }

    .manager-test-list {
      display: grid;
      gap: 10px;
      max-height: 520px;
      overflow: auto;
      padding-right: 2px;
    }

    .manager-test-editor {
      display: grid;
      gap: 8px;
      background: #fff;
    }

    .manager-test-editor textarea {
      min-height: 44px;
    }

    .manager-test-section {
      display: grid;
      gap: 8px;
    }

    .manager-test-section-title {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 750;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }

    .manager-test-grid {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 8px;
    }

    .manager-test-name-input {
      width: 100%;
      border: 0;
      border-bottom: 1px solid transparent;
      padding: 2px 0;
      background: transparent;
      color: var(--text);
      font-weight: 750;
    }

    .manager-test-name-input:focus {
      outline: 0;
      border-bottom-color: var(--accent);
    }

    .manager-output {
      max-height: 420px;
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      padding: 12px;
      color: var(--text);
      white-space: pre-wrap;
      font-size: 13px;
    }

    .manager-output .case-list {
      margin-top: 0;
    }

    .tag-editor {
      display: grid;
      gap: 10px;
    }

    .tag-editor-row {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 8px;
      align-items: center;
    }

    .tag-help {
      color: var(--muted);
      font-size: 12px;
    }

    .form-grid {
      display: grid;
      gap: 10px;
    }

    .form-grid label {
      display: grid;
      gap: 5px;
      color: var(--muted);
      font-size: 13px;
    }

    .text-input,
    .small-textarea {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 8px 10px;
      background: #fff;
      color: var(--text);
      font: inherit;
    }

    .small-textarea {
      min-height: 74px;
      resize: vertical;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
      font-size: 13px;
      line-height: 1.4;
    }

    .runtime-grid {
      display: grid;
      gap: 14px;
    }

    .runtime-card {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      overflow: hidden;
    }

    .runtime-row {
      display: grid;
      grid-template-columns: minmax(140px, 1fr) minmax(110px, auto);
      gap: 10px;
      align-items: center;
      padding: 9px 12px;
      border-bottom: 1px solid var(--line-soft);
      font-size: 13px;
    }

    .runtime-row:last-child {
      border-bottom: 0;
    }

    .runtime-package {
      min-width: 0;
      overflow-wrap: anywhere;
    }

    .runtime-actions {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }

    .draft-deps-bar {
      display: grid;
      grid-template-columns: auto minmax(0, 1fr) auto;
      align-items: center;
      gap: 12px;
      margin-top: 10px;
      padding: 10px;
      border: 1px solid #bfdbfe;
      border-radius: 8px;
      background: #eff6ff;
    }

    .draft-deps-bar.flush {
      margin-top: 0;
    }

    .dependency-icon {
      width: 34px;
      height: 34px;
      display: grid;
      place-items: center;
      border-radius: 8px;
      background: #dbeafe;
      color: #1d4ed8;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
      font-size: 12px;
      font-weight: 800;
    }

    .dependency-copy {
      min-width: 0;
      display: grid;
      gap: 2px;
    }

    .dependency-title {
      font-size: 13px;
      font-weight: 800;
      color: #1e3a8a;
    }

    .dependency-subtitle {
      color: #476391;
      font-size: 12px;
      line-height: 1.35;
    }

    .dependency-actions {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 8px;
      flex-wrap: wrap;
    }

    .runtime-output {
      max-height: 260px;
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #111827;
      color: #e5e7eb;
      padding: 12px;
    }

    .author-grid {
      display: grid;
      gap: 14px;
    }

    .author-columns {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(300px, 0.9fr) minmax(260px, 0.7fr);
      gap: 14px;
    }

    .author-textarea {
      width: 100%;
      min-height: 460px;
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      background: #fff;
      color: var(--text);
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
      font-size: 13px;
      line-height: 1.45;
    }

    .author-prompt {
      max-height: 380px;
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfcfe;
      padding: 12px;
    }

    .author-output {
      max-height: 260px;
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #111827;
      color: #e5e7eb;
      padding: 12px;
    }

    .llm-request-grid {
      display: grid;
      gap: 10px;
    }

    .llm-controls {
      display: grid;
      grid-template-columns: 150px minmax(0, 1fr) 90px auto auto;
      gap: 8px;
      align-items: end;
    }

    .llm-key-controls {
      display: grid;
      grid-template-columns: 150px minmax(0, 1fr) auto;
      gap: 8px;
      align-items: end;
    }

    .llm-controls label {
      display: grid;
      gap: 5px;
      color: var(--muted);
      font-size: 13px;
    }

    .llm-key-controls label {
      display: grid;
      gap: 5px;
      color: var(--muted);
      font-size: 13px;
    }

    .llm-attachment-bar {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 8px;
      align-items: center;
      border: 1px solid var(--line-soft);
      border-radius: 8px;
      background: #fafafa;
      padding: 8px;
    }

    .llm-attachment-picker {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      min-width: 0;
    }

    .llm-attachment-picker input {
      max-width: 280px;
      font-size: 13px;
    }

    .llm-attachment-list {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 6px;
    }

    .llm-attachment-chip {
      display: inline-flex;
      align-items: center;
      max-width: 240px;
      gap: 6px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: #fff;
      padding: 4px 8px;
      color: var(--muted);
      font-size: 12px;
    }

    .llm-attachment-chip strong {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      color: var(--text);
      font-weight: 600;
    }

    .llm-provider-hint {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }

    .llm-result-tabs {
      border-top: 1px solid var(--line-soft);
    }

    .llm-result-pane[hidden] {
      display: none;
    }

    .number-input {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 8px 10px;
      background: #fff;
      color: var(--text);
      font: inherit;
    }

    .llm-draft-list {
      display: grid;
      gap: 8px;
      margin-top: 10px;
    }

    .author-file {
      max-width: 260px;
      font-size: 13px;
    }

    .author-file-wrap {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      min-width: 0;
    }

    .author-file-name {
      max-width: 180px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      color: var(--muted);
      font-size: 12px;
    }

    .checkbox-row {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      color: var(--muted);
      font-size: 13px;
    }

    .preview-box {
      display: grid;
      gap: 12px;
    }

    .preview-statement {
      max-height: 320px;
      overflow: auto;
      border: 1px solid var(--line-soft);
      border-radius: 8px;
      padding: 12px;
      background: #fff;
    }

    @media (max-width: 900px) {
      .topbar {
        height: auto;
        min-height: 54px;
        flex-wrap: wrap;
        padding: 10px 12px;
      }

      select {
        min-width: 0;
        flex: 1;
      }

      .layout {
        display: block;
        height: auto;
      }

      .problem-pane,
      .work-pane {
        border-right: 0;
      }

      .problem-pane {
        border-bottom: 1px solid var(--line);
      }

      .problem-inner {
        padding: 20px 16px 28px;
      }

      .view {
        padding: 12px;
      }

      .editor-body {
        height: 420px;
      }

      .practice-workspace {
        grid-template-rows: auto auto;
      }

      .practice-editor-card {
        min-height: 520px;
      }

      .practice-editor-toolbar,
      .practice-console-head,
      .editor-footer {
        align-items: stretch;
        flex-direction: column;
      }

      .editor-footer {
        display: grid;
        grid-template-columns: 1fr;
      }

      .console-actions {
        width: 100%;
        flex-wrap: wrap;
      }

      .draft-deps-bar {
        grid-template-columns: 1fr;
      }

      .dependency-actions {
        justify-content: flex-start;
      }

      .catalog-layout {
        grid-template-columns: 1fr;
      }

      .manager-grid {
        grid-template-columns: 1fr;
      }

      .manager-test-grid {
        grid-template-columns: 1fr;
      }

      .manager-splitter {
        display: none;
      }

      .author-columns {
        grid-template-columns: 1fr;
      }

      .llm-controls {
        grid-template-columns: 1fr;
      }

      .llm-key-controls {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body data-mode="practice">
  <header class="topbar">
    <div class="brand">
      <span>Mnemosyne</span>
      <span class="brand-subtitle">Recall, Rebuild, Test Yourself</span>
    </div>
    <nav class="top-nav">
      <button id="practiceModeTab" class="active" onclick="setAppMode('practice')">Practice</button>
      <button id="problemsModeTab" onclick="setAppMode('problems')">Problems</button>
      <button id="manageModeTab" onclick="setAppMode('manage')">Manage</button>
      <button id="llmModeTab" onclick="setAppMode('llm')">Create through LLM</button>
      <button id="createModeTab" onclick="setAppMode('create')">Create</button>
    </nav>
    <select id="problemSelect" aria-label="Problem"></select>
    <div class="topbar-spacer"></div>
    <span id="syntaxBadge" class="badge">Python</span>
  </header>

  <main class="layout">
    <section class="problem-pane">
      <div class="problem-inner">
        <h1 id="title" class="problem-title"></h1>
        <div id="meta" class="meta"></div>
        <div id="statement" class="statement"></div>
        <h2 class="section-title">Examples</h2>
        <div id="visibleTests" class="test-list"></div>
        <h2 class="section-title">Runtime</h2>
        <div id="dependencyStatus" class="dependency-list"></div>
      </div>
    </section>

    <section class="work-pane">
      <div class="work-tabs">
        <button id="codeTab" class="tab active" onclick="setView('code')">Code</button>
        <button id="manageTab" class="tab" onclick="setAppMode('manage')" hidden>Manage</button>
        <button id="solutionTab" class="tab" onclick="setView('solution')">Solution</button>
        <button id="runtimeTab" class="tab" onclick="setView('runtime')">Runtime</button>
        <button id="historyTab" class="tab" onclick="setView('history')">Submissions</button>
        <div class="language-pill">Python 3</div>
      </div>

      <div id="catalogView" class="view" hidden>
        <div class="catalog-layout">
          <aside class="catalog-sidebar">
            <div class="catalog-sidebar-head">Tags</div>
            <div id="tagFilters"></div>
          </aside>
          <div class="catalog-main">
            <div class="catalog-head">
              <h2 id="catalogTitle" class="catalog-title">All problems</h2>
              <span id="catalogCount" class="badge">0 problems</span>
            </div>
            <div class="catalog-search">
              <input id="catalogSearch" class="text-input" placeholder="Search title, id, tag, difficulty..." oninput="setCatalogSearch(this.value)" />
              <button class="small" onclick="clearCatalogSearch()">Clear</button>
            </div>
            <div id="catalogNotice" class="catalog-notice" hidden></div>
            <div id="problemCatalog" class="problem-grid"></div>
          </div>
        </div>
      </div>

      <div id="llmView" class="view" hidden>
        <div class="author-grid">
          <div class="runtime-card">
            <div class="panel-head">
              <h2 class="panel-title">Create through LLM</h2>
              <span id="llmStatus" class="badge">Checking</span>
            </div>
            <div class="panel-body">
              <div class="llm-request-grid">
                <textarea id="llmProblemRequest" class="small-textarea" spellcheck="false" placeholder="Create a medium NumPy problem about linear regression gradient descent with displayed $$...$$ math and allclose tests."></textarea>
                <div class="llm-attachment-bar">
                  <div>
                    <span class="llm-attachment-picker">
                      <input id="llmAttachmentInput" type="file" multiple accept=".pdf,.md,.markdown,.txt,.json,.csv,.tsv,.py,.yaml,.yml,image/*,application/pdf,text/markdown,text/plain,application/json" />
                      <span class="empty">Optional materials: PDF, markdown/text, or images.</span>
                    </span>
                    <div id="llmAttachmentList" class="llm-attachment-list"></div>
                  </div>
                  <button class="small" onclick="clearLlmAttachments()">Clear files</button>
                </div>
                <div class="llm-key-controls">
                  <label>
                    API key
                    <input id="llmApiKey" class="text-input" type="password" autocomplete="off" placeholder="Paste key here if not set in shell" oninput="handleLlmApiKeyInput(this)" />
                  </label>
                  <div class="empty">Kept only until this page is refreshed.</div>
                  <button onclick="clearLlmApiKey()">Clear key</button>
                </div>
                <div class="llm-controls">
                  <label>
                    Provider
                    <select id="llmProvider" onchange="handleLlmProviderChange('llmProvider', 'llmModel')"></select>
                  </label>
                  <label>
                    Model
                    <input id="llmModel" class="text-input" list="llmModelOptions" placeholder="gemini-2.5-flash" />
                    <datalist id="llmModelOptions"></datalist>
                  </label>
                  <label>
                    Problems
                    <input id="llmProblemCount" class="number-input" type="number" min="1" max="10" value="1" title="How many separate problems to generate. More than 1 is harder for small/free models." />
                  </label>
                  <label>
                    Timeout
                    <input id="llmTimeoutSeconds" class="number-input" type="number" min="10" max="600" value="180" title="Seconds per model request. PDF/image inputs often need 180s or more." />
                  </label>
                  <button class="primary" onclick="generateLlmProblemDraft()">Generate</button>
                  <button onclick="clearLlmDraft()">Clear</button>
                </div>
                <div id="llmProviderHint" class="llm-provider-hint"></div>
                <pre id="llmOutput" class="author-output">No LLM request yet.</pre>
              </div>
            </div>
          </div>

          <div class="runtime-card">
            <div class="panel-head">
              <h2 class="panel-title">Generated draft</h2>
              <div class="runtime-actions">
                <span id="llmDecisionStatus" class="badge">Waiting</span>
                <button class="small" onclick="validateLlmDraft()">Check</button>
                <button class="small" onclick="sendLlmDraftToCreate()">Edit in Create</button>
                <button class="small primary" onclick="createLlmDraftProblem()">Add to library</button>
              </div>
            </div>
            <div class="manager-tool-tabs llm-result-tabs">
              <button id="llmPreviewResultTab" class="active" onclick="setLlmResultView('preview')">Preview</button>
              <button id="llmReportResultTab" onclick="setLlmResultView('report')">Verifier report</button>
              <button id="llmJsonResultTab" onclick="setLlmResultView('json')">Raw JSON</button>
            </div>
            <div class="panel-body">
              <div class="draft-deps-bar flush">
                <div class="dependency-icon">pip</div>
                <div class="dependency-copy">
                  <div class="dependency-title">Draft dependencies</div>
                  <div class="dependency-subtitle">Install required packages before checking reference solutions.</div>
                </div>
                <div class="dependency-actions">
                  <span id="llmDepsStatus" class="badge">Not checked</span>
                  <button class="small primary" onclick="installLlmDraftDependencies()">Install</button>
                </div>
              </div>
            </div>
            <div id="llmResultPreviewPane" class="panel-body preview-box llm-result-pane">
              <div class="runtime-actions">
                <span id="llmPreviewStatus" class="badge">No draft</span>
              </div>
              <div id="llmPreview">
                <div class="empty">Generate a draft to preview the problem, solution, and tests.</div>
              </div>
            </div>
            <div id="llmResultReportPane" class="panel-body llm-result-pane" hidden>
              <pre id="llmDecisionOutput" class="author-output">Generated drafts stay here until you add them to the library.</pre>
            </div>
            <div id="llmResultJsonPane" class="panel-body llm-result-pane" hidden>
              <textarea id="llmDraftJson" class="author-textarea" spellcheck="false"></textarea>
              <div class="actions" style="margin-top: 10px; margin-bottom: 0;">
                <label class="checkbox-row">
                  <input id="llmOverwrite" type="checkbox" />
                  overwrite existing problem id
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div id="authorView" class="view" hidden>
        <div class="author-grid">
          <div class="author-columns">
            <div class="runtime-card">
              <div class="panel-head">
                <h2 class="panel-title">Problem JSON</h2>
                <div class="runtime-actions">
                  <span class="author-file-wrap">
                    <input id="authorFile" class="author-file" type="file" accept=".json,application/json" />
                    <span id="authorFileName" class="author-file-name">No file loaded</span>
                  </span>
                  <button class="small" onclick="loadAuthorTemplate()">Template</button>
                  <button class="small" onclick="cleanAuthorJson()">Clean</button>
                  <button class="small" onclick="clearAuthorInput()">Clear</button>
                  <button class="small" onclick="validateAuthorProblem()">Check</button>
                  <button class="small primary" onclick="createAuthorProblem()">Add to library</button>
                </div>
              </div>
              <div class="panel-body">
                <textarea id="authorJson" class="author-textarea" spellcheck="false"></textarea>
                <div class="actions" style="margin-top: 10px; margin-bottom: 0;">
                  <label class="checkbox-row">
                    <input id="authorOverwrite" type="checkbox" />
                    overwrite existing problem id
                  </label>
                </div>
                <div class="draft-deps-bar">
                  <div class="dependency-icon">pip</div>
                  <div class="dependency-copy">
                    <div class="dependency-title">Draft dependencies</div>
                    <div class="dependency-subtitle">Install packages declared in this JSON before adding or validating package-based problems.</div>
                  </div>
                  <div class="dependency-actions">
                    <span id="authorDepsStatus" class="badge">Not checked</span>
                    <button class="small primary" onclick="installAuthorDependencies()">Install</button>
                  </div>
                </div>
              </div>
            </div>

            <div class="runtime-card">
              <div class="panel-head">
                <h2 class="panel-title">Preview before adding</h2>
                <span id="authorPreviewStatus" class="badge">Not checked</span>
              </div>
              <div id="authorPreview" class="panel-body preview-box">
                <div class="empty">Validate the JSON to preview the problem, solution, and tests.</div>
              </div>
            </div>

            <div class="runtime-card">
              <div class="panel-head">
                <h2 class="panel-title">LLM prompt</h2>
                <div class="runtime-actions">
                  <button class="small" onclick="copyAuthorPrompt()">Copy prompt</button>
                  <button class="small" onclick="copyAuthorSchema()">Copy API schema</button>
                </div>
              </div>
              <div class="panel-body">
                <pre id="authorPrompt" class="author-prompt">Loading prompt...</pre>
              </div>
            </div>
          </div>

          <div class="runtime-card">
            <div class="panel-head">
              <h2 class="panel-title">Authoring result</h2>
              <span id="authorStatus" class="badge">Idle</span>
            </div>
            <div class="panel-body">
              <pre id="authorOutput" class="author-output">Paste JSON or import a .json file.</pre>
            </div>
          </div>
        </div>
      </div>

      <div id="codeView" class="view">
        <div class="practice-workspace">
          <section class="practice-editor-card">
            <div class="practice-editor-toolbar">
              <div class="practice-editor-title">
                <span class="code-mark">&lt;/&gt;</span>
                <span>Code</span>
              </div>
              <div class="editor-meta">
                <span>Python 3</span>
                <span class="editor-meta-dot">•</span>
                <span>Local</span>
              </div>
              <button class="small" onclick="validateCode({quiet: false})">Check syntax</button>
            </div>
            <div class="editor-shell practice-editor-shell">
              <div class="editor-body">
                <div id="lineNumbers" class="line-numbers"></div>
                <textarea id="code" class="code-editor" spellcheck="false" autocomplete="off" autocorrect="off" autocapitalize="off"></textarea>
              </div>
            </div>
            <div class="editor-footer">
              <div id="diagnostic" class="diagnostic">Ready.</div>
              <div id="cursorStatus" class="cursor-status">Ln 1, Col 1</div>
            </div>
          </section>

          <section class="practice-console-card">
            <div class="practice-console-head">
              <div class="console-tabs">
                <button id="practiceTestsTab" class="console-tab active" onclick="setPracticeConsoleView('tests')">Testcase</button>
                <button id="practiceResultTab" class="console-tab" onclick="setPracticeConsoleView('result')">Test Result</button>
              </div>
              <div class="console-actions">
                <button onclick="submitCode('run')">Run visible tests</button>
                <button class="primary" onclick="submitCode('submit')">Submit hidden tests</button>
                <span id="status" class="status-line"></span>
              </div>
            </div>
            <div id="practiceTestsPane" class="practice-console-pane">
              <div id="practiceTestcases" class="practice-testcases">
                <div class="empty">Load a problem to see visible tests.</div>
              </div>
            </div>
            <div id="practiceResultPane" class="practice-console-pane panel-body" hidden>
              <div class="summary" style="margin-bottom: 10px;">
                <span id="resultMeta" class="badge">No submission</span>
              </div>
              <div id="result">
                <div class="empty">Run your code to see test results.</div>
              </div>
            </div>
          </section>
          </div>
      </div>

      <div id="manageView" class="view" hidden>
        <div id="managerPanel" class="manager-grid" hidden>
          <div class="manager-header-card">
            <div class="manager-title">
              <h2 id="managerProblemTitle" class="panel-title">Manage problem</h2>
              <div id="managerProblemMeta" class="problem-card-meta"></div>
            </div>
            <div class="runtime-actions">
              <span id="managerStatus" class="badge">Select a problem</span>
              <button class="small" onclick="validateManagedProblem()">Check</button>
              <button class="small" onclick="runManagedReference()">Run reference</button>
              <button class="small primary" onclick="saveManagedProblem()">Save</button>
              <button class="small" onclick="openManagerJsonEditor()">Raw JSON</button>
              <button class="small" onclick="practiceManagedProblem()">Practice</button>
              <button class="small" onclick="deleteManagedProblem()">Delete</button>
            </div>
          </div>

          <div class="manager-three-grid">
            <div class="runtime-card manager-pane">
              <div class="panel-head">
                <h2 class="panel-title">Problem statement</h2>
                <span class="badge">Markdown</span>
              </div>
              <div class="panel-body">
                <textarea id="managerStatement" class="author-textarea manager-statement-editor" spellcheck="false" oninput="syncManagerStatementPreview()"></textarea>
                <div class="test-card">
                  <div class="test-name">Preview</div>
                  <div id="managerStatementPreview" class="statement"></div>
                </div>
              </div>
            </div>

            <div class="runtime-card manager-pane">
              <div class="panel-head">
                <h2 class="panel-title">Reference solution</h2>
                <span class="badge">Python</span>
              </div>
              <div class="panel-body">
                <div class="manager-code-shell">
                  <div class="manager-code-toolbar">
                    <span>reference_solution.py</span>
                    <span>Python 3</span>
                  </div>
                  <textarea id="managerReferenceSolution" class="code-editor manager-reference-editor" spellcheck="false" autocomplete="off" autocorrect="off" autocapitalize="off"></textarea>
                </div>
              </div>
            </div>

            <div class="runtime-card manager-pane">
              <div class="panel-head">
                <h2 class="panel-title">Test cases</h2>
                <div class="runtime-actions">
                  <button class="small" onclick="refreshManagedTestOutputs()">Refresh outputs</button>
                </div>
              </div>
              <div class="panel-body manager-preview">
                <div id="managerTestList" class="manager-test-list"></div>
                <div class="test-card">
                  <div class="test-name">Add test case</div>
                  <div class="form-grid">
                    <label>
                      Test type
                      <select id="managerTestGroup">
                        <option value="visible_tests">Visible example</option>
                        <option value="hidden_tests">Hidden test</option>
                      </select>
                    </label>
                    <label>
                      Name
                      <input id="managerTestName" class="text-input" placeholder="optional" />
                    </label>
                    <div id="managerFunctionTestBox" class="manager-inputs">
                      <div>
                        <div class="io-label">Input</div>
                        <div id="managerInputFields" class="manager-input-fields"></div>
                      </div>
                      <div class="io-block">
                        <div class="io-label">Generated output</div>
                        <pre id="managerGeneratedOutput" class="empty">Output will be generated when you add the test.</pre>
                      </div>
                    </div>
                    <textarea id="managerTestArgs" hidden>[]</textarea>
                    <textarea id="managerTestExpected" hidden>null</textarea>
                    <label id="managerCodeLabel" hidden>
                      Unit test code
                      <textarea id="managerTestCode" class="small-textarea" spellcheck="false">from user_solution import Solution</textarea>
                    </label>
                    <button class="small primary" onclick="addManagedTestCase()">Add test</button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="runtime-card">
            <div class="panel-head">
              <h2 class="panel-title">Advanced tools</h2>
              <div class="manager-tool-tabs" style="padding: 0; background: transparent;">
                <button id="managerTagsToolTab" class="active" onclick="setManagerToolView('tags')">Tags</button>
                <button id="managerLlmToolTab" onclick="setManagerToolView('llm')">LLM</button>
                <button id="managerJsonToolTab" onclick="setManagerToolView('json')">JSON</button>
                <button id="managerPreviewToolTab" onclick="setManagerToolView('preview')">Preview</button>
              </div>
            </div>
            <div class="panel-body manager-preview">
              <div id="managerTagsPane" class="manager-pane-section">
                <div class="tag-editor">
                  <div class="tag-help">Comma-separated tags. Spaces inside a tag are saved as underscores.</div>
                  <div class="tag-editor-row">
                    <input id="managerTagInput" class="text-input" placeholder="python, array, oop" />
                    <button class="small primary" onclick="saveManagerTags()">Save tags</button>
                  </div>
                </div>
              </div>

              <div id="managerLlmPane" class="manager-pane-section" hidden>
                <div class="form-grid">
                  <label>
                    Request
                    <textarea id="managerLlmRequest" class="small-textarea" spellcheck="false" placeholder="Make the statement clearer, add one edge case, or generate hidden tests for negative values."></textarea>
                  </label>
                  <div class="llm-key-controls">
                    <label>
                      API key
                      <input id="managerLlmApiKey" class="text-input" type="password" autocomplete="off" placeholder="Paste key here if not set in shell" oninput="handleLlmApiKeyInput(this)" />
                    </label>
                    <div class="empty">Kept only until this page is refreshed.</div>
                    <button class="small" onclick="clearLlmApiKey()">Clear key</button>
                  </div>
                  <div class="llm-controls">
                    <label>
                      Provider
                      <select id="managerLlmProvider" onchange="handleLlmProviderChange('managerLlmProvider', 'managerLlmModel')"></select>
                    </label>
                    <label>
                      Model
                      <input id="managerLlmModel" class="text-input" list="managerLlmModelOptions" placeholder="gemini-2.5-flash" />
                      <datalist id="managerLlmModelOptions"></datalist>
                    </label>
                    <label>
                      Count
                      <input id="managerLlmTestCount" class="number-input" type="number" min="1" max="8" value="3" />
                    </label>
                    <button class="small primary" onclick="draftManagedProblemEdit()">Draft edit</button>
                    <button class="small" onclick="draftManagedTests()">Draft tests</button>
                  </div>
                  <div class="tag-editor-row">
                    <select id="managerLlmTestGroup">
                      <option value="hidden_tests">Hidden tests</option>
                      <option value="visible_tests">Visible examples</option>
                    </select>
                    <button id="managerApplyLlmTests" class="small primary" onclick="applyManagedLlmTests()" hidden>Add drafted tests</button>
                  </div>
                  <pre id="managerLlmOutput" class="author-output">No LLM draft yet.</pre>
                </div>
              </div>

              <div id="managerJsonPane" class="manager-pane-section" hidden>
                <textarea id="managerJson" class="author-textarea manager-json-textarea" spellcheck="false"></textarea>
              </div>

              <div id="managerPreviewPane" class="manager-pane-section" hidden>
                <div id="managerPreview" class="preview-box"></div>
              </div>

              <div id="managerOutput" class="manager-output">Open Manage to edit the current problem.</div>
            </div>
          </div>
        </div>
      </div>

      <div id="solutionView" class="view" hidden>
        <div class="solution-grid">
          <div class="history-panel">
            <div class="panel-head">
              <h2 class="panel-title">Reference solution</h2>
              <button class="small" onclick="loadSolution({force: true})">Refresh</button>
            </div>
            <div id="solutionBody" class="panel-body">
              <div class="empty">Open this tab to load the reference solution.</div>
            </div>
          </div>
        </div>
      </div>

      <div id="runtimeView" class="view" hidden>
        <div class="runtime-grid">
          <div class="runtime-card">
            <div class="panel-head">
              <h2 class="panel-title">Python environment</h2>
              <button class="small" onclick="loadRuntimeStatus()">Refresh</button>
            </div>
            <div id="runtimeEnv" class="panel-body">
              <div class="empty">Loading runtime...</div>
            </div>
          </div>

          <div id="runtimeGroups" class="runtime-grid"></div>

          <div class="runtime-card">
            <div class="panel-head">
              <h2 class="panel-title">Install output</h2>
              <span id="runtimeInstallStatus" class="badge">Idle</span>
            </div>
            <div class="panel-body">
              <pre id="runtimeOutput" class="runtime-output">No install has been run from this page.</pre>
            </div>
          </div>
        </div>
      </div>

      <div id="historyView" class="view" hidden>
        <div class="history-grid">
          <div class="history-panel">
            <div class="panel-head">
              <h2 class="panel-title">Current problem submission history</h2>
              <button class="small" onclick="loadCurrentHistory()">Refresh</button>
            </div>
            <div class="panel-body"><table id="currentHistoryTable"></table></div>
          </div>

          <div class="history-panel">
            <div class="panel-head">
              <h2 class="panel-title">Wrong problems</h2>
              <button class="small" onclick="loadWrongProblems()">Refresh</button>
            </div>
            <div class="panel-body"><table id="wrongProblemsTable"></table></div>
          </div>

          <div class="history-panel">
            <div class="panel-head">
              <h2 class="panel-title">All submissions</h2>
              <button class="small" onclick="loadAllHistory()">Refresh</button>
            </div>
            <div class="panel-body"><table id="allHistoryTable"></table></div>
          </div>

          <div class="history-panel">
            <div class="panel-head">
              <h2 class="panel-title">Submission detail</h2>
            </div>
            <div class="panel-body detail-box">
              <pre id="submissionDetail">Click Detail on a submission.</pre>
            </div>
          </div>
        </div>
      </div>
    </section>
  </main>

  <script>
    let currentProblem = null;
    let currentSyntax = {ok: true};
    let checkTimer = null;
    let checkCounter = 0;
    let solutionLoadedFor = null;
    let allProblems = [];
    let tagSummaries = [];
    let activeCatalogTag = '';
    let catalogSearchQuery = '';
    let runtimeState = null;
    let authorPromptLoaded = false;
    let authorTemplateLoaded = false;
    let authorSchemaCache = null;
    let managerSelectedProblemId = null;
    let managerProblem = null;
    let managerToolView = 'tags';
    let llmState = null;
    let llmSessionApiKey = '';
    let llmResultView = 'preview';
    let llmAttachmentFiles = [];
    let managerLlmTestDrafts = [];
    let managerLlmTestGroup = 'hidden_tests';
    let activePracticeCaseIndex = 0;
    let practiceConsoleView = 'tests';
    let codeMirrorEditor = null;
    let loadProblemRequestId = 0;
    try {
      sessionStorage.removeItem('local_leetcode_llm_api_key');
      sessionStorage.removeItem('mnemosyne_llm_api_key');
    } catch {}

    function setAppMode(mode) {
      document.body.dataset.mode = mode;
      document.getElementById('practiceModeTab').classList.toggle('active', mode === 'practice');
      document.getElementById('problemsModeTab').classList.toggle('active', mode === 'problems');
      document.getElementById('manageModeTab').classList.toggle('active', mode === 'manage');
      document.getElementById('llmModeTab').classList.toggle('active', mode === 'llm');
      document.getElementById('createModeTab').classList.toggle('active', mode === 'create');

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
        if (currentProblem) {
          loadManagerForCurrentProblem();
        } else if (allProblems.length) {
          selectManagerProblem(allProblems[0].id);
        }
        return;
      }

      if (mode === 'llm') {
        setView('llm');
        loadLlmPanel();
        return;
      }

      if (mode === 'create') {
        setView('author');
        loadAuthoringPanel();
      }
    }

    async function loadProblems() {
      await refreshProblemIndex();
      if (allProblems.length) await loadProblem(allProblems[0].id);
      await loadAllHistory();
      await loadWrongProblems();
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
      const requestId = ++loadProblemRequestId;
      const res = await fetch(`/api/problems/${encodeURIComponent(problemId)}`);
      const loadedProblem = await res.json();
      if (requestId !== loadProblemRequestId) return;
      currentProblem = loadedProblem;
      document.getElementById('problemSelect').value = currentProblem.id;
      document.getElementById('title').textContent = currentProblem.title;
      document.getElementById('meta').innerHTML = renderMeta(currentProblem);
      document.getElementById('statement').innerHTML = markdownLite(currentProblem.statement || '');
      typesetMath(document.getElementById('statement'));
      renderVisibleTests();
      activePracticeCaseIndex = 0;
      renderPracticeTestcases();
      renderDependencyStatus();
      if (!document.getElementById('runtimeView').hidden) {
        await loadRuntimeStatus();
      }
      setCodeValue(currentProblem.starter_code || '');
      document.getElementById('status').textContent = '';
      document.getElementById('resultMeta').className = 'badge';
      document.getElementById('resultMeta').textContent = 'No submission';
      document.getElementById('result').innerHTML = '<div class="empty">Run your code to see test results.</div>';
      document.getElementById('submissionDetail').textContent = 'Click Detail on a submission.';
      document.getElementById('solutionBody').innerHTML = '<div class="empty">Open this tab to load the reference solution.</div>';
      solutionLoadedFor = null;
      updateLineNumbers();
      updateCursorStatus();
      setPracticeConsoleView('tests');
      await validateCode({quiet: true});
      await loadCurrentHistory();
      if (!document.getElementById('manageView').hidden) {
        await selectManagerProblem(problemId);
      }
    }

    function renderMeta(problem) {
      const tags = [
        `<span class="tag difficulty">${escapeHtml(problem.difficulty || 'unknown')}</span>`,
        `<span class="tag">${escapeHtml(problem.entry_kind || 'function')}</span>`,
        ...(problem.tags || []).map(t => renderClickableTag(t)),
        `<button type="button" class="small" onclick="openCatalogProblemManager('${escapeJs(problem.id)}', event)">Manage</button>`
      ];
      return tags.join('');
    }

    function renderVisibleTests() {
      const box = document.getElementById('visibleTests');
      const tests = currentProblem?.visible_tests || [];
      if (!tests.length) {
        box.innerHTML = '<div class="empty">No visible tests.</div>';
        return;
      }
      box.innerHTML = tests.map((t, idx) => {
        const name = t.name || `Example ${idx + 1}`;
        if (currentProblem.entry_kind === 'function') {
          const input = formatFunctionCall(currentProblem, t.args || []);
          return `
            <div class="test-card">
              <div class="test-name">${escapeHtml(name)}</div>
              <div class="io-grid">
                ${renderIoBlock('Input', input)}
                ${renderValueBlock('Expected', t.expected)}
              </div>
            </div>
          `;
        }
        return `
          <div class="test-card">
            <div class="test-name">${escapeHtml(name)}</div>
            ${renderIoBlock('Test code', t.code || '')}
          </div>
        `;
      }).join('');
    }

    function setPracticeConsoleView(view) {
      practiceConsoleView = view;
      const testsPane = document.getElementById('practiceTestsPane');
      const resultPane = document.getElementById('practiceResultPane');
      const testsTab = document.getElementById('practiceTestsTab');
      const resultTab = document.getElementById('practiceResultTab');
      if (!testsPane || !resultPane || !testsTab || !resultTab) return;
      testsPane.hidden = view !== 'tests';
      resultPane.hidden = view !== 'result';
      testsTab.classList.toggle('active', view === 'tests');
      resultTab.classList.toggle('active', view === 'result');
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
        box.innerHTML = '<div class="empty">No visible tests for this problem.</div>';
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
      const installAction = (status.missing || []).length
        ? `<div class="actions" style="margin-top: 10px; margin-bottom: 0;">
             <button class="small primary" onclick="openRuntimeAndInstallCurrent()">Install current dependencies</button>
             <button class="small" onclick="setView('runtime')">Open Runtime</button>
           </div>`
        : '';
      box.innerHTML = rows + install + installAction;
    }

    function renderCatalog() {
      renderTagFilters();
      renderProblemCatalog();
    }

    function renderTagFilters() {
      const box = document.getElementById('tagFilters');
      const total = allProblems.length;
      const rows = [
        {tag: '', label: 'All', count: total},
        ...tagSummaries.map(item => ({tag: item.tag, label: item.tag, count: item.count}))
      ];

      box.innerHTML = rows.map(item => {
        const active = item.tag === activeCatalogTag ? ' active' : '';
        return `
          <button class="tag-filter${active}" onclick="selectCatalogTag('${escapeJs(item.tag)}')">
            <span>${escapeHtml(item.label)}</span>
            <span class="tag-filter-count">${escapeHtml(item.count)}</span>
          </button>
        `;
      }).join('');
    }

    function renderProblemCatalog() {
      const tagged = activeCatalogTag
        ? allProblems.filter(problem => (problem.tags || []).includes(activeCatalogTag))
        : allProblems;
      const list = catalogSearchQuery
        ? tagged.filter(problem => problemMatchesCatalogSearch(problem, catalogSearchQuery))
        : tagged;

      const title = activeCatalogTag ? `Tag: ${activeCatalogTag}` : 'All problems';
      document.getElementById('catalogTitle').textContent = title;
      document.getElementById('catalogCount').textContent = `${list.length} problem${list.length === 1 ? '' : 's'}`;
      renderCatalogSearchState();
      renderCatalogNotice(list.length);

      const box = document.getElementById('problemCatalog');
      if (!list.length) {
        box.innerHTML = '<div class="empty">No problems match this filter.</div>';
        return;
      }

      box.innerHTML = list.map(problem => {
        const tags = (problem.tags || []).map(tag => renderClickableTag(tag)).join('');
        return `
          <div class="problem-card">
            <div class="problem-card-title">
              <span>${escapeHtml(problem.title)}</span>
              <span class="problem-card-actions">
                <span class="badge">${escapeHtml(problem.difficulty || 'unknown')}</span>
                <button class="small primary" onclick="openCatalogProblem('${escapeJs(problem.id)}')">Practice</button>
                <button class="small" onclick="openCatalogProblemManager('${escapeJs(problem.id)}', event)">Manage</button>
                <button class="small" onclick="editCatalogProblemTags('${escapeJs(problem.id)}', event)">Edit tags</button>
                <button class="small" onclick="deleteCatalogProblem('${escapeJs(problem.id)}', event)">Delete</button>
              </span>
            </div>
            <div class="problem-card-meta">
              <span class="tag">${escapeHtml(problem.entry_kind || 'function')}</span>
              ${tags}
            </div>
          </div>
        `;
      }).join('');
    }

    function renderCatalogSearchState() {
      const input = document.getElementById('catalogSearch');
      if (input && input.value !== catalogSearchQuery) {
        input.value = catalogSearchQuery;
      }
    }

    function renderCatalogNotice(count) {
      const box = document.getElementById('catalogNotice');
      const search = catalogSearchQuery ? ` matching <strong>${escapeHtml(catalogSearchQuery)}</strong>` : '';
      if (!activeCatalogTag) {
        box.hidden = false;
        box.innerHTML = catalogSearchQuery
          ? `Showing <strong>${escapeHtml(count)}</strong> problem${count === 1 ? '' : 's'}${search}. Clear search to see all problems.`
          : 'Click any tag to filter the problem list, or search by title, id, difficulty, type, or tag.';
        return;
      }
      box.hidden = false;
      box.innerHTML = `Showing <strong>${escapeHtml(count)}</strong> problem${count === 1 ? '' : 's'} tagged <strong>${escapeHtml(activeCatalogTag)}</strong>${search}. Click <strong>All</strong> to clear the tag filter.`;
    }

    function selectCatalogTag(tag) {
      activeCatalogTag = tag;
      renderCatalog();
    }

    async function openCatalogProblem(problemId) {
      await loadProblem(problemId);
      setAppMode('practice');
      setView('code');
    }

    async function openCatalogProblemManager(problemId, event = null) {
      if (event) event.stopPropagation();
      await loadProblem(problemId);
      await selectManagerProblem(problemId);
      setAppMode('manage');
    }

    function setCatalogSearch(value) {
      catalogSearchQuery = String(value || '').trim().toLowerCase();
      renderProblemCatalog();
    }

    function clearCatalogSearch() {
      catalogSearchQuery = '';
      renderProblemCatalog();
    }

    function problemMatchesCatalogSearch(problem, query) {
      const haystack = [
        problem.id,
        problem.slug,
        problem.title,
        problem.difficulty,
        problem.entry_kind,
        ...(problem.tags || []),
      ].join(' ').toLowerCase();
      return query.split(/\s+/).filter(Boolean).every(term => haystack.includes(term));
    }

    function renderClickableTag(tag) {
      return `<button type="button" class="tag tag-click" onclick="openTag('${escapeJs(tag)}', event)">${escapeHtml(tag)}</button>`;
    }

    function openTag(tag, event = null) {
      if (event) event.stopPropagation();
      activeCatalogTag = tag;
      setAppMode('problems');
      renderCatalog();
    }

    async function deleteCatalogProblem(problemId, event) {
      event.stopPropagation();
      if (!confirm(`Delete problem "${problemId}"? This removes it from the local problem bank.`)) return;
      const res = await fetch(`/api/problems/${encodeURIComponent(problemId)}`, {method: 'DELETE'});
      const result = await res.json();
      await refreshProblemIndex();
      if (result.ok && result.deleted && currentProblem?.id === problemId) {
        if (allProblems.length) {
          await loadProblem(allProblems[0].id);
        } else {
          currentProblem = null;
          document.getElementById('problemSelect').innerHTML = '';
          document.getElementById('title').textContent = '';
          document.getElementById('meta').innerHTML = '';
          document.getElementById('statement').innerHTML = '<div class="empty">No problems left.</div>';
          document.getElementById('visibleTests').innerHTML = '';
          document.getElementById('dependencyStatus').innerHTML = '';
        }
      }
      renderCatalogDeleteResult(result, problemId);
    }

    function renderCatalogDeleteResult(result, problemId) {
      const box = document.getElementById('catalogNotice');
      box.hidden = false;
      if (result.ok && result.deleted) {
        box.innerHTML = `Deleted <strong>${escapeHtml(problemId)}</strong>.`;
        return;
      }
      const message = result.errors?.length ? result.errors.join(' ') : 'Could not delete problem.';
      box.innerHTML = `<span class="status-text wrong">${escapeHtml(message)}</span>`;
    }

    async function editCatalogProblemTags(problemId, event) {
      event.stopPropagation();
      const summary = allProblems.find(problem => problem.id === problemId);
      const current = (summary?.tags || []).join(', ');
      const input = prompt('Edit tags for this problem. Use commas between tags.', current);
      if (input === null) return;
      const tags = parseTagsInput(input);
      const result = await saveProblemTags(problemId, tags);
      if (result.ok && result.saved) {
        await refreshProblemIndex();
        if (currentProblem?.id === problemId) {
          await loadProblem(problemId);
        }
      }
      renderCatalogTagSaveResult(result, problemId);
    }

    function renderCatalogTagSaveResult(result, problemId) {
      const box = document.getElementById('catalogNotice');
      box.hidden = false;
      if (result.ok && result.saved) {
        box.innerHTML = `Tags saved for <strong>${escapeHtml(problemId)}</strong>.`;
        return;
      }
      const message = result.errors?.length ? result.errors.join(' ') : 'Could not save tags.';
      box.innerHTML = `<span class="status-text wrong">${escapeHtml(message)}</span>`;
    }

    function parseTagsInput(input) {
      const seen = new Set();
      const tags = String(input || '')
        .split(/[,\n]+/)
        .map(tag => tag.trim().toLowerCase().replace(/\s+/g, '_'))
        .filter(Boolean)
        .filter(tag => {
          if (seen.has(tag)) return false;
          seen.add(tag);
          return true;
        });
      return tags;
    }

    async function saveProblemTags(problemId, tags) {
      const res = await fetch(`/api/problems/${encodeURIComponent(problemId)}/raw`);
      const data = await res.json();
      const problem = data.problem;
      if (!problem) {
        return {ok: false, saved: false, errors: ['Problem not found.']};
      }
      problem.tags = tags;
      return await postJson(`/api/problems/${encodeURIComponent(problemId)}`, {
        content: stringifyProblemJson(problem)
      }, 'PUT');
    }

    async function loadManagerForCurrentProblem() {
      if (!currentProblem) {
        document.getElementById('managerPanel').hidden = true;
        return;
      }
      if (managerSelectedProblemId === currentProblem.id && managerProblem) {
        document.getElementById('managerPanel').hidden = false;
        renderManagerProblem();
        return;
      }
      await selectManagerProblem(currentProblem.id);
    }

    async function selectManagerProblem(problemId) {
      managerSelectedProblemId = problemId;
      const res = await fetch(`/api/problems/${encodeURIComponent(problemId)}/raw`);
      const data = await res.json();
      managerProblem = data.problem;
      managerLlmTestDrafts = [];
      document.getElementById('managerApplyLlmTests').hidden = true;
      document.getElementById('managerPanel').hidden = false;
      document.getElementById('managerJson').value = stringifyProblemJson(managerProblem);
      renderManagerProblem();
      setManagerStatus('Loaded', true);
    }

    function renderManagerProblem() {
      if (!managerProblem) return;
      document.getElementById('managerProblemTitle').textContent = `${managerProblem.title || managerProblem.id} (${managerProblem.difficulty || 'unknown'})`;
      document.getElementById('managerProblemMeta').innerHTML = [
        `<span class="tag">${escapeHtml(managerProblem.id || '')}</span>`,
        `<span class="tag">${escapeHtml(managerProblem.entry_kind || 'function')}</span>`,
        ...(managerProblem.tags || []).map(tag => `<span class="tag">${escapeHtml(tag)}</span>`)
      ].join('');
      document.getElementById('managerStatement').value = managerProblem.statement || '';
      document.getElementById('managerReferenceSolution').value = managerProblem.reference_solution || managerProblem.solution || '';
      document.getElementById('managerJson').value = stringifyProblemJson(managerProblem);
      syncManagerStatementPreview();
      renderManagerTestList();
      document.getElementById('managerPreview').innerHTML = renderProblemPreview(managerProblem, {includeAnswer: true, includeTests: true});
      document.getElementById('managerTagInput').value = (managerProblem.tags || []).join(', ');
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
      managerProblem.statement = document.getElementById('managerStatement').value;
      managerProblem.reference_solution = document.getElementById('managerReferenceSolution').value;
      syncManagerTestsFromEditors();
    }

    function syncManagerStatementPreview() {
      const preview = document.getElementById('managerStatementPreview');
      if (!preview) return;
      preview.innerHTML = markdownLite(document.getElementById('managerStatement')?.value || '');
      typesetMath(preview);
    }

    function renderManagerTestList() {
      const box = document.getElementById('managerTestList');
      if (!box || !managerProblem) return;
      const groups = [
        ['visible_tests', 'Visible examples'],
        ['hidden_tests', 'Hidden tests'],
      ];
      const cards = [];
      for (const [group, label] of groups) {
        const tests = Array.isArray(managerProblem[group]) ? managerProblem[group] : [];
        cards.push(`
          <div class="manager-test-section-title">
            <span>${escapeHtml(label)}</span>
            <span>${escapeHtml(tests.length)} case${tests.length === 1 ? '' : 's'}</span>
          </div>
        `);
        if (!tests.length) {
          cards.push(`<div class="empty">${label}: no tests.</div>`);
          continue;
        }
        tests.forEach((test, idx) => {
          const name = test?.name || `${group}_${idx + 1}`;
          if (managerProblem.entry_kind === 'unit_tests') {
            cards.push(`
              <div class="test-card manager-test-editor">
                <div class="case-title">
                  <input class="manager-test-name-input" data-manager-test-group="${group}" data-manager-test-index="${idx}" data-manager-test-field="name" spellcheck="false" value="${escapeHtml(name)}" />
                  <span class="badge">code</span>
                </div>
                <textarea class="small-textarea" data-manager-test-group="${group}" data-manager-test-index="${idx}" data-manager-test-field="code" spellcheck="false">${escapeHtml(test.code || '')}</textarea>
              </div>
            `);
            return;
          }
          cards.push(`
            <div class="test-card manager-test-editor">
              <div class="case-title">
                <input class="manager-test-name-input" data-manager-test-group="${group}" data-manager-test-index="${idx}" data-manager-test-field="name" spellcheck="false" value="${escapeHtml(name)}" />
                <span class="badge">input/output</span>
              </div>
              <div class="manager-test-grid">
                <label>
                  Input args
                  <textarea class="small-textarea" data-manager-test-group="${group}" data-manager-test-index="${idx}" data-manager-test-field="args" spellcheck="false">${escapeHtml(stringifyProblemJson(test.args || []))}</textarea>
                </label>
                <label>
                  Output
                  <textarea class="small-textarea" data-manager-test-group="${group}" data-manager-test-index="${idx}" data-manager-test-field="expected" spellcheck="false">${escapeHtml(stringifyProblemJson(test.expected))}</textarea>
                </label>
              </div>
            </div>
          `);
        });
      }
      box.innerHTML = cards.join('');
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
        try {
          managerProblem[group][idx][key] = JSON.parse(field.value.trim() || (key === 'args' ? '[]' : 'null'));
        } catch (e) {
          throw new Error(`${group}[${idx}].${key} must be valid JSON.`);
        }
      }
    }

    async function refreshManagedTestOutputs() {
      if (!managerSelectedProblemId || !managerProblem) return;
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
      for (const group of ['visible_tests', 'hidden_tests']) {
        for (const test of managerProblem[group] || []) {
          if (test && Array.isArray(test.args)) delete test.expected;
        }
      }
      syncManagerJsonFromProblem();
      const result = await postJson('/api/authoring/validate', {content: document.getElementById('managerJson').value});
      renderManagerResult(result, result.ok ? 'Outputs refreshed' : 'Needs fixes');
      if (result.problem) {
        managerProblem = result.problem;
        renderManagerProblem();
      }
      return result;
    }

    async function saveManagerTags() {
      if (!managerSelectedProblemId) return;
      const tags = parseTagsInput(document.getElementById('managerTagInput').value);
      try {
        syncManagerProblemFromEditors();
      } catch (e) {
        renderManagerResult({ok: false, errors: [`Problem edit is invalid: ${e.message}`], warnings: []}, 'Needs fixes');
        return;
      }
      managerProblem.tags = tags;
      syncManagerJsonFromProblem();
      const result = await postJson(`/api/problems/${encodeURIComponent(managerSelectedProblemId)}`, {
        content: document.getElementById('managerJson').value
      }, 'PUT');
      renderManagerResult(result, result.saved ? 'Tags saved' : 'Not saved');
      if (result.ok && result.saved) {
        managerProblem = result.problem;
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
        const value = sample === undefined ? 'null' : JSON.stringify(sample);
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
      let content;
      try {
        content = managerContentFromEditors();
      } catch (e) {
        renderManagerResult({ok: false, errors: [`Problem edit is invalid: ${e.message}`], warnings: []}, 'Needs fixes');
        return {ok: false};
      }
      const result = await postJson('/api/authoring/validate', {content});
      renderManagerResult(result, result.ok ? 'Checked' : 'Needs fixes');
      if (result.problem) {
        managerProblem = result.problem;
        renderManagerProblem();
      }
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
      return result;
    }

    async function saveManagedProblem() {
      if (!managerSelectedProblemId) return;
      let content;
      try {
        content = managerContentFromEditors();
      } catch (e) {
        renderManagerResult({ok: false, errors: [`Problem edit is invalid: ${e.message}`], warnings: []}, 'Needs fixes');
        return;
      }
      const result = await postJson(`/api/problems/${encodeURIComponent(managerSelectedProblemId)}`, {content}, 'PUT');
        renderManagerResult(result, result.saved ? 'Saved' : 'Not saved');
      if (result.ok && result.saved) {
        managerProblem = result.problem;
        document.getElementById('managerJson').value = stringifyProblemJson(managerProblem);
        renderManagerProblem();
        await refreshProblemIndex();
        if (currentProblem?.id === managerSelectedProblemId) {
          await loadProblem(managerSelectedProblemId);
        }
      }
    }

    async function deleteManagedProblem() {
      if (!managerSelectedProblemId) return;
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
      if (!managerSelectedProblemId || !managerProblem) return;
      const group = document.getElementById('managerTestGroup').value;
      const name = document.getElementById('managerTestName').value.trim() || 'new test';
      let testCase = {name};
      try {
        if (managerProblem.entry_kind === 'unit_tests') {
          testCase.code = document.getElementById('managerTestCode').value;
        } else {
          testCase.args = collectManagerInputArgs();
          setManagerStatus('Generating output...', null);
          const result = await postJson(`/api/problems/${encodeURIComponent(managerSelectedProblemId)}/tests/generated`, {
            group,
            name,
            args: testCase.args
          });
          if (result.ok && result.saved) {
            showManagerGeneratedOutput(result.test_case.expected);
            renderManagerResult(result, 'Test added');
            await selectManagerProblem(managerSelectedProblemId);
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

      const result = await postJson(`/api/problems/${encodeURIComponent(managerSelectedProblemId)}/tests`, {group, test_case: testCase});
      renderManagerResult(result, result.saved ? 'Test added' : 'Not saved');
      if (result.ok && result.saved) {
        await selectManagerProblem(managerSelectedProblemId);
        await refreshProblemIndex();
      }
    }

    async function draftManagedProblemEdit() {
      if (!managerSelectedProblemId || !managerProblem) return;
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
      }
    }

    async function draftManagedTests() {
      if (!managerSelectedProblemId || !managerProblem) return;
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
    }

    async function applyManagedLlmTests() {
      if (!managerSelectedProblemId || !managerLlmTestDrafts.length) return;
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
      if (result.errors?.length) lines.push(`errors:\n- ${result.errors.join('\n- ')}`);
      if (result.warnings?.length) lines.push(`warnings:\n- ${result.warnings.join('\n- ')}`);
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
      if (!managerSelectedProblemId) return;
      await loadProblem(managerSelectedProblemId);
      setAppMode('practice');
      setView('code');
    }

    function renderManagerResult(result, status) {
      setManagerStatus(status, Boolean(result.ok));
      const lines = [];
      if (result.path) lines.push(`path: ${result.path}`);
      if (result.errors?.length) lines.push(`errors:\n- ${result.errors.join('\n- ')}`);
      if (result.warnings?.length) lines.push(`warnings:\n- ${result.warnings.join('\n- ')}`);
      if (!lines.length) lines.push(JSON.stringify(result, null, 2));
      document.getElementById('managerOutput').textContent = lines.join('\n\n');
    }

    function renderManagerRunResult(result) {
      const judge = result.result || {};
      const ok = Boolean(result.ok);
      setManagerStatus(judge.status || (ok ? 'Accepted' : 'Run failed'), ok);
      const tests = judge.tests || [];
      const cards = tests.map((test, idx) => renderRunCaseCard(test, idx, managerProblem, 'submit')).join('');
      const messages = [];
      if (result.errors?.length) messages.push(`errors:\n- ${result.errors.join('\n- ')}`);
      if (result.warnings?.length) messages.push(`warnings:\n- ${result.warnings.join('\n- ')}`);
      if (judge.error) messages.push(`runtime:\n${judge.error}`);
      document.getElementById('managerOutput').innerHTML = `
        <div class="result-summary-card ${ok ? 'accepted' : 'failed'}">
          <div>
            <div class="result-title status-text ${ok ? 'accepted' : 'wrong'}">${escapeHtml(judge.status || (ok ? 'Accepted' : 'Run failed'))}</div>
            <div class="result-subtitle">Reference solution · visible + hidden tests</div>
          </div>
          <span class="badge ${ok ? 'ok' : 'error'}">${escapeHtml(judge.passed ?? 0)}/${escapeHtml(judge.total ?? tests.length)} passed</span>
        </div>
        <div class="case-list">${cards || '<div class="empty">No test result details returned.</div>'}</div>
        ${messages.length ? `<pre style="margin-top: 12px;">${escapeHtml(messages.join('\n\n'))}</pre>` : ''}
      `;
    }

    function renderRunCaseCard(test, idx, problem = currentProblem, mode = 'run') {
      const passed = Boolean(test.passed);
      const bits = [];
      const source = testSourceForIndex(problem, idx, mode);
      if (source?.args) bits.push(renderIoBlock('Input', formatFunctionCall(problem, source.args, {compact: true})));
      if (source?.code) bits.push(renderIoBlock('Test code', source.code));
      if ('expected' in test) bits.push(renderValueBlock('Expected', test.expected));
      if ('actual' in test) bits.push(renderValueBlock('Actual', test.actual));
      if (test.error) bits.push(renderIoBlock('Traceback', test.error));
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
      const visible = Array.isArray(problem.visible_tests) ? problem.visible_tests : [];
      const hidden = Array.isArray(problem.hidden_tests) ? problem.hidden_tests : [];
      const tests = mode === 'submit' ? visible.concat(hidden) : visible;
      return tests[idx] || null;
    }

    function setManagerStatus(text, ok = null) {
      const status = document.getElementById('managerStatus');
      status.className = ok === null ? 'badge' : ok ? 'badge ok' : 'badge error';
      status.textContent = text;
    }

    async function loadAuthoringPanel() {
      if (!authorPromptLoaded) {
        const promptRes = await fetch('/api/authoring/prompt');
        const data = await promptRes.json();
        document.getElementById('authorPrompt').textContent = data.prompt || '';
        authorPromptLoaded = true;
      }
      if (!authorTemplateLoaded && !document.getElementById('authorJson').value.trim()) {
        await loadAuthorTemplate();
      }
    }

    async function loadLlmPanel() {
      await loadLlmStatus();
    }

    async function loadAuthorTemplate() {
      const res = await fetch('/api/authoring/template');
      const data = await res.json();
      document.getElementById('authorJson').value = stringifyProblemJson(data.template || {});
      authorTemplateLoaded = true;
      resetAuthorFilePicker();
      resetAuthorPreview('Validate the JSON to preview the problem, solution, and tests.');
        setAuthorStatus('Template loaded.', true);
    }

    async function loadLlmStatus() {
      if (llmState) {
        renderLlmStatus();
        return llmState;
      }
      try {
        const res = await fetch('/api/llm/status');
        llmState = await res.json();
      } catch {
        llmState = {configured: false, message: 'LLM status unavailable.'};
      }
      renderLlmStatus();
      return llmState;
    }

    function renderLlmStatus() {
      const status = document.getElementById('llmStatus');
      if (!status || !llmState) return;
      renderLlmProviderSelects();
      const provider = currentSelectedProvider();
      const ready = isProviderReady(provider);
      status.className = ready ? 'badge ok' : 'badge error';
      status.textContent = ready
        ? `Ready: ${provider?.label || provider?.id || 'provider'}`
        : providerNeedsSessionKey(provider)
          ? `${provider?.label || provider?.id || 'Provider'} needs key`
          : 'Needs provider';
      const output = document.getElementById('llmOutput');
      if (output && output.textContent === 'No LLM request yet.' && !ready) {
        output.textContent = llmState.message || 'Choose a configured provider.';
      }
      renderLlmProviderHint(provider);
    }

    function renderLlmProviderHint(provider) {
      const hint = document.getElementById('llmProviderHint');
      if (!hint) return;
      const profile = provider?.profile || {};
      const bits = [];
      if (profile.strategy) bits.push(`Strategy: ${profile.strategy}`);
      if (profile.supports_multimodal_attachments) bits.push('PDF/image attachments supported');
      if (profile.max_recommended_count) bits.push(`Recommended batch: up to ${profile.max_recommended_count}, generated one at a time`);
      if (profile.notes) bits.push(profile.notes);
      hint.textContent = bits.join(' · ');
    }

    function renderLlmProviderSelects() {
      const providers = llmState?.providers || [];
      const selected = preferredLlmProviderId(llmState?.default_provider || llmState?.provider || 'ollama');
      ['llmProvider', 'managerLlmProvider'].forEach(id => {
        const select = document.getElementById(id);
        if (!select) return;
        const previous = select.value || selected;
        select.innerHTML = providers.map(provider => {
          const label = providerOptionLabel(provider);
          return `<option value="${escapeHtml(provider.id)}">${escapeHtml(label)}</option>`;
        }).join('');
        select.value = providers.some(provider => provider.id === previous) ? previous : selected;
      });
      renderLlmModelSelect('llmProvider', 'llmModel');
      renderLlmModelSelect('managerLlmProvider', 'managerLlmModel');
      loadLlmApiKeyInputs();
    }

    function providerOptionLabel(provider) {
      const label = provider?.label || provider?.id || 'Provider';
      if (isProviderReady(provider)) return label;
      if (providerNeedsSessionKey(provider)) return `${label} (enter key)`;
      return `${label} (not ready)`;
    }

    function preferredLlmProviderId(fallback) {
      const providers = llmState?.providers || [];
      if (currentSessionApiKey() && providers.some(provider => provider.id === 'gemini')) {
        const fallbackProvider = providers.find(provider => provider.id === fallback);
        if (!fallbackProvider?.configured || fallback === 'ollama') return 'gemini';
      }
      return fallback;
    }

    function currentSelectedProvider() {
      const selected = document.getElementById('llmProvider')?.value || llmState?.provider || llmState?.default_provider;
      return (llmState?.providers || []).find(provider => provider.id === selected) || null;
    }

    function providerNeedsSessionKey(provider) {
      return Boolean(provider?.accepts_session_key && !provider.configured && !currentSessionApiKey());
    }

    function isProviderReady(provider) {
      if (!provider) return false;
      if (provider.configured) return true;
      if (!provider.accepts_session_key || !currentSessionApiKey()) return false;
      if (provider.id === 'openai_compatible') return Boolean(provider.base_url);
      return true;
    }

    function currentSessionApiKey() {
      return (document.getElementById('llmApiKey')?.value
        || document.getElementById('managerLlmApiKey')?.value
        || llmSessionApiKey
        || '').trim();
    }

    function loadLlmApiKeyInputs() {
      const key = llmSessionApiKey || '';
      ['llmApiKey', 'managerLlmApiKey'].forEach(id => {
        const input = document.getElementById(id);
        if (input && !input.value) input.value = key;
      });
    }

    function handleLlmApiKeyInput(input) {
      const value = input.value.trim();
      if (value) {
        llmSessionApiKey = value;
        syncLlmApiKeyInputs(value);
        preferSessionKeyProvider();
      } else {
        llmSessionApiKey = '';
        syncLlmApiKeyInputs('');
      }
      renderLlmStatus();
    }

    function preferSessionKeyProvider() {
      ['llmProvider', 'managerLlmProvider'].forEach(id => {
        const select = document.getElementById(id);
        if (!select || select.value !== 'ollama') return;
        const providers = llmState?.providers || [];
        const configuredDefault = providers.find(provider => provider.id === llmState?.provider && provider.accepts_session_key);
        const firstKeyProvider = configuredDefault || providers.find(provider => provider.accepts_session_key);
        if (firstKeyProvider && [...select.options].some(option => option.value === firstKeyProvider.id)) {
          select.value = firstKeyProvider.id;
        }
      });
      renderLlmModelSelect('llmProvider', 'llmModel', {force: true});
      renderLlmModelSelect('managerLlmProvider', 'managerLlmModel', {force: true});
    }

    function currentLlmApiKey() {
      const focused = document.activeElement?.id;
      const primary = focused === 'managerLlmApiKey' || focused === 'llmApiKey'
        ? document.getElementById(focused)
        : null;
      const value = (
        primary?.value
        || document.getElementById('llmApiKey')?.value
        || document.getElementById('managerLlmApiKey')?.value
        || llmSessionApiKey
        || ''
      ).trim();
      if (value) {
        llmSessionApiKey = value;
        syncLlmApiKeyInputs(value);
      }
      return value || null;
    }

    function syncLlmApiKeyInputs(value) {
      ['llmApiKey', 'managerLlmApiKey'].forEach(id => {
        const input = document.getElementById(id);
        if (input && input.value !== value) input.value = value;
      });
    }

    function clearLlmApiKey() {
      llmSessionApiKey = '';
      syncLlmApiKeyInputs('');
      setLlmOutput('API key cleared from this page.');
      renderLlmStatus();
    }

    function renderLlmModelSelect(providerSelectId, modelSelectId, {force = false} = {}) {
      const select = document.getElementById(providerSelectId);
      const modelSelect = document.getElementById(modelSelectId);
      if (!select || !modelSelect) return;
      const provider = (llmState?.providers || []).find(item => item.id === select.value);
      const previous = modelSelect.value;
      const options = llmModelOptions(provider);
      const optionMarkup = options.map(option => (
        `<option value="${escapeHtml(option.value)}" label="${escapeHtml(option.label)}"></option>`
      )).join('');
      const listId = modelSelect.getAttribute('list');
      const datalist = listId ? document.getElementById(listId) : null;
      if (datalist) {
        datalist.innerHTML = optionMarkup;
      } else {
        modelSelect.innerHTML = options.map(option => (
          `<option value="${escapeHtml(option.value)}">${escapeHtml(option.label)}</option>`
        )).join('');
      }
      const preferred = provider?.default_model || options[0]?.value || '';
      const canKeepPrevious = previous && (datalist || options.some(option => option.value === previous));
      if (!force && canKeepPrevious) {
        modelSelect.value = previous;
      } else if (preferred && options.some(option => option.value === preferred)) {
        modelSelect.value = preferred;
      } else if (options[0]) {
        modelSelect.value = options[0].value;
      } else {
        modelSelect.value = '';
      }
    }

    function llmModelOptions(provider) {
      if (!provider) return [{value: '', label: 'Default model'}];
      if (provider.available_models?.length) {
        return provider.available_models.map(model => ({value: model, label: geminiModelLabel(model)}));
      }
      if (provider.id === 'openai') {
        const defaults = [provider.default_model, 'gpt-4.1-mini', 'gpt-4.1'].filter(Boolean);
        return dedupe(defaults).map(model => ({value: model, label: model}));
      }
      if (provider.default_model) {
        return [{value: provider.default_model, label: provider.default_model}];
      }
      return [{value: '', label: 'Use environment default'}];
    }

    function geminiModelLabel(model) {
      if (typeof model !== 'string') return String(model || '');
      if (!model.startsWith('gemini-')) return model;
      return model
        .replace(/^gemini-/, 'Gemini ')
        .replaceAll('-', ' ')
        .replace(/\b\w/g, char => char.toUpperCase());
    }

    function dedupe(values) {
      const seen = new Set();
      return values.filter(value => {
        if (seen.has(value)) return false;
        seen.add(value);
        return true;
      });
    }

    function handleLlmProviderChange(providerSelectId, modelInputId) {
      renderLlmModelSelect(providerSelectId, modelInputId, {force: true});
      renderLlmStatus();
    }

    function selectedLlmModel(modelSelectId) {
      const value = document.getElementById(modelSelectId)?.value || '';
      return value.trim() || null;
    }

    async function validateAuthorProblem() {
      const result = await postAuthoring('/api/authoring/validate');
      renderAuthorResult(result, 'Validated');
      renderAuthorPreview(result);
      syncAuthorJsonFromResult(result);
      setDraftDependencyStatus('authorDepsStatus', 'Not installed', null);
      return result;
    }

    async function createAuthorProblem() {
      const result = await postAuthoring('/api/authoring/problems');
      renderAuthorResult(result, result.created ? 'Created' : 'Not created');
      renderAuthorPreview(result);
      syncAuthorJsonFromResult(result);
      if (result.ok && result.created_count) {
        await refreshProblemIndex();
        const problemId = result.problem_id || result.results?.find(item => item.created)?.problem_id;
        if (problemId) await loadProblem(problemId);
      }
      return result;
    }

    async function installAuthorDependencies() {
      const content = document.getElementById('authorJson').value;
      setAuthorStatus('Installing...', null);
      setDraftDependencyStatus('authorDepsStatus', 'Installing...', null);
      document.getElementById('authorOutput').textContent = 'Checking draft dependencies...';
      const result = await postJson('/api/authoring/install-dependencies', {content});
      setAuthorStatus(result.ok ? 'Dependencies ready' : 'Install failed', Boolean(result.ok));
      setDraftDependencyStatus('authorDepsStatus', result.ok ? 'Ready' : 'Failed', Boolean(result.ok));
      document.getElementById('authorOutput').textContent = formatDependencyInstallResult(result);
      if (result.problem || result.problems?.length) {
        renderAuthorPreview({...result, ok: result.validation_ok && result.ok, errors: result.validation_errors || []});
      }
      return result;
    }

    function handleLlmAttachmentChange(input) {
      llmAttachmentFiles = Array.from(input.files || []);
      renderLlmAttachmentList();
    }

    function clearLlmAttachments() {
      llmAttachmentFiles = [];
      const input = document.getElementById('llmAttachmentInput');
      if (input) input.value = '';
      renderLlmAttachmentList();
    }

    function renderLlmAttachmentList() {
      const box = document.getElementById('llmAttachmentList');
      if (!box) return;
      if (!llmAttachmentFiles.length) {
        box.innerHTML = '';
        return;
      }
      box.innerHTML = llmAttachmentFiles.map(file => `
        <span class="llm-attachment-chip" title="${escapeHtml(file.name)}">
          <strong>${escapeHtml(file.name)}</strong>
          <span>${escapeHtml(attachmentKindLabel(file))}</span>
          <span>${escapeHtml(formatFileSize(file.size))}</span>
        </span>
      `).join('');
    }

    function attachmentKindLabel(file) {
      const name = file.name.toLowerCase();
      const type = (file.type || '').toLowerCase();
      if (type.startsWith('image/')) return 'image';
      if (type === 'application/pdf' || name.endsWith('.pdf')) return 'pdf';
      return 'text';
    }

    function formatFileSize(size) {
      if (!Number.isFinite(size)) return '';
      if (size < 1024) return `${size} B`;
      if (size < 1024 * 1024) return `${Math.round(size / 1024)} KB`;
      return `${(size / (1024 * 1024)).toFixed(1)} MB`;
    }

    function isTextAttachment(file) {
      const name = file.name.toLowerCase();
      const type = (file.type || '').toLowerCase();
      return type.startsWith('text/')
        || ['application/json', 'application/x-yaml', 'application/yaml'].includes(type)
        || ['.md', '.markdown', '.txt', '.json', '.csv', '.tsv', '.py', '.yaml', '.yml'].some(ext => name.endsWith(ext));
    }

    function readFileAsText(file) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result || ''));
        reader.onerror = () => reject(new Error(`Could not read ${file.name}.`));
        reader.readAsText(file);
      });
    }

    function readFileAsDataUrl(file) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result || ''));
        reader.onerror = () => reject(new Error(`Could not read ${file.name}.`));
        reader.readAsDataURL(file);
      });
    }

    async function collectLlmAttachments() {
      const attachments = [];
      for (const file of llmAttachmentFiles) {
        if (file.size > 8 * 1024 * 1024) {
          throw new Error(`${file.name} is larger than 8 MB.`);
        }
        const base = {
          name: file.name,
          mime_type: file.type || attachmentMimeFromName(file.name),
          size_bytes: file.size
        };
        if (isTextAttachment(file)) {
          attachments.push({...base, text: await readFileAsText(file)});
        } else {
          const dataUrl = await readFileAsDataUrl(file);
          attachments.push({...base, content_base64: dataUrl.split(',', 2)[1] || ''});
        }
      }
      return attachments;
    }

    function attachmentMimeFromName(name) {
      const lower = name.toLowerCase();
      if (lower.endsWith('.pdf')) return 'application/pdf';
      if (lower.endsWith('.png')) return 'image/png';
      if (lower.endsWith('.jpg') || lower.endsWith('.jpeg')) return 'image/jpeg';
      if (lower.endsWith('.webp')) return 'image/webp';
      if (lower.endsWith('.gif')) return 'image/gif';
      if (lower.endsWith('.md') || lower.endsWith('.markdown')) return 'text/markdown';
      if (lower.endsWith('.json')) return 'application/json';
      if (lower.endsWith('.csv')) return 'text/csv';
      if (lower.endsWith('.py')) return 'text/x-python';
      return 'application/octet-stream';
    }

    async function generateLlmProblemDraft() {
      await loadLlmStatus();
      const request = document.getElementById('llmProblemRequest').value;
      const provider = document.getElementById('llmProvider').value;
      const api_key = currentLlmApiKey();
      const count = Number(document.getElementById('llmProblemCount').value || 1);
      const timeout_seconds = Number(document.getElementById('llmTimeoutSeconds')?.value || 180);
      const model = selectedLlmModel('llmModel');
      setLlmDecisionStatus('Generating...', null);
      setLlmOutput(llmAttachmentFiles.length ? 'Reading attachments...' : 'Calling model...');
      let attachments = [];
      try {
        attachments = await collectLlmAttachments();
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        const result = {ok: false, errors: [message], warnings: [], problems: [], problem: null, content: ''};
        renderLlmDraftResult(result, 'Attachment failed');
        return result;
      }
      setLlmOutput(attachments.length ? `Calling model with ${attachments.length} attachment(s)...` : 'Calling model...');
      const result = await postJson('/api/llm/author/problems', {request, provider, api_key, count, model, max_attempts: 3, attachments, timeout_seconds});
      renderLlmDraftResult(result, result.ok ? 'Draft ready' : 'Needs fixes');
      return result;
    }

    async function validateLlmDraft() {
      const content = document.getElementById('llmDraftJson').value;
      const result = await postJson('/api/authoring/validate', {content});
      renderLlmDraftResult(result, result.ok ? 'Valid' : 'Needs fixes');
      setDraftDependencyStatus('llmDepsStatus', 'Not installed', null);
      return result;
    }

    async function createLlmDraftProblem() {
      const content = document.getElementById('llmDraftJson').value;
      const overwrite = document.getElementById('llmOverwrite').checked;
      const result = await postJson('/api/authoring/problems', {content, overwrite});
      renderLlmDraftResult(result, result.created ? 'Created' : 'Not created');
      if (result.ok && result.created_count) {
        await refreshProblemIndex();
        const problemId = result.problem_id || result.results?.find(item => item.created)?.problem_id;
        if (problemId) await loadProblem(problemId);
      }
      return result;
    }

    async function installLlmDraftDependencies() {
      const content = document.getElementById('llmDraftJson').value;
      setLlmDecisionStatus('Installing...', null);
      setDraftDependencyStatus('llmDepsStatus', 'Installing...', null);
      setLlmOutput('Checking draft dependencies...');
      const result = await postJson('/api/authoring/install-dependencies', {content});
      const text = formatDependencyInstallResult(result);
      setLlmOutput(text);
      document.getElementById('llmDecisionOutput').textContent = text;
      setLlmDecisionStatus(result.ok ? 'Dependencies ready' : 'Install failed', Boolean(result.ok));
      setDraftDependencyStatus('llmDepsStatus', result.ok ? 'Ready' : 'Failed', Boolean(result.ok));
      if (result.problem || result.problems?.length) {
        renderLlmPreview({...result, ok: result.validation_ok && result.ok, errors: result.validation_errors || []});
      }
      setLlmResultView('report');
      return result;
    }

    function renderLlmDraftResult(result, statusText) {
      setLlmOutput(formatLlmResult(result));
      setLlmDecisionStatus(Boolean(result.ok) ? statusText : 'Needs fixes', Boolean(result.ok));
      document.getElementById('llmDecisionOutput').textContent = formatLlmResult(result);
      renderLlmPreview(result);
      const content = result.content || problemContentFromResult(result);
      if (content) {
        document.getElementById('llmDraftJson').value = content;
      }
      setLlmResultView(result.problems?.length || result.problem ? 'preview' : 'report');
    }

    function renderLlmPreview(result) {
      renderDraftPreview('llmPreview', 'llmPreviewStatus', result);
    }

    function setLlmResultView(view) {
      llmResultView = view;
      ['preview', 'report', 'json'].forEach(name => {
        const tab = document.getElementById(`llm${titleCase(name)}ResultTab`);
        const pane = document.getElementById(`llmResult${titleCase(name)}Pane`);
        if (tab) tab.classList.toggle('active', name === view);
        if (pane) pane.hidden = name !== view;
      });
    }

    function problemContentFromResult(result) {
      const problems = result?.problems?.length ? result.problems : result?.problem ? [result.problem] : [];
      if (!problems.length) return '';
      return stringifyProblemJson(problems.length === 1 ? problems[0] : problems);
    }

    function clearLlmDraft() {
      document.getElementById('llmProblemRequest').value = '';
      document.getElementById('llmDraftJson').value = '';
      clearLlmAttachments();
      setLlmOutput('No LLM request yet.');
      setLlmDecisionStatus('Waiting', null);
      document.getElementById('llmDecisionOutput').textContent = 'Generated drafts stay here until you add them to the library.';
      const status = document.getElementById('llmPreviewStatus');
      status.className = 'badge';
      status.textContent = 'No draft';
      document.getElementById('llmPreview').innerHTML = '<div class="empty">Generate a draft to preview the problem, solution, and tests.</div>';
      setDraftDependencyStatus('llmDepsStatus', 'Not checked', null);
      setLlmResultView('preview');
    }

    function sendLlmDraftToCreate() {
      const content = document.getElementById('llmDraftJson').value;
      document.getElementById('authorJson').value = content;
      resetAuthorFilePicker();
      resetAuthorPreview('Validate the JSON to preview the problem, solution, and tests.');
      setAppMode('create');
      setAuthorStatus('Draft copied.', true);
    }

    function setLlmDecisionStatus(text, ok = null) {
      const status = document.getElementById('llmDecisionStatus');
      status.className = ok === null ? 'badge' : ok ? 'badge ok' : 'badge error';
      status.textContent = text;
    }

    function setLlmOutput(text) {
      document.getElementById('llmOutput').textContent = text;
    }

    function setDraftDependencyStatus(id, text, ok = null) {
      const status = document.getElementById(id);
      if (!status) return;
      status.className = ok === null ? 'badge' : ok ? 'badge ok' : 'badge error';
      status.textContent = text;
    }

    function formatLlmResult(result) {
      const lines = [];
      if (result.message) lines.push(result.message);
      if (result.attachments?.length) {
        lines.push(`attachments:\n${result.attachments.map(item => `- ${item.name} (${item.kind || 'file'}, ${item.mime_type || 'unknown'})`).join('\n')}`);
      }
      if (result.agent_plan?.summary) {
        const briefs = result.agent_plan.problem_briefs?.length
          ? `\nbriefs:\n${result.agent_plan.problem_briefs.map((brief, idx) => `- ${idx + 1}. ${brief.title || brief.id_hint || 'problem brief'}`).join('\n')}`
          : '';
        lines.push(`agent source digest:\n${result.agent_plan.summary}${briefs}`);
      }
      if (result.errors?.length) lines.push(`errors:\n- ${result.errors.join('\n- ')}`);
      if (result.warnings?.length) lines.push(`warnings:\n- ${result.warnings.join('\n- ')}`);
      const topRepairHints = formatRepairHints(result.repair_hints);
      if (topRepairHints) lines.push(`repair hints:\n${topRepairHints}`);
      if (result.attempts?.length) {
        lines.push(`attempts:\n${result.attempts.map((attempt, idx) => {
          const label = attempt.ok ? 'ok' : 'failed';
          const errors = attempt.errors?.length ? `: ${attempt.errors.join('; ')}` : '';
          const hints = formatRepairHints(attempt.repair_hints, {compact: true});
          const hintText = hints ? `\n  hints:\n${hints}` : '';
          const prefix = attempt.problem_index ? `problem ${attempt.problem_index}, attempt ${idx + 1}` : `${idx + 1}`;
          return `- ${prefix}: ${label}${errors}${hintText}`;
        }).join('\n')}`);
      }
      if (result.problem_results?.length) {
        lines.push(`problem results:\n${result.problem_results.map(item => {
          const mark = item.ok ? 'ready' : 'failed';
          const title = item.problem_id ? ` ${item.problem_id}` : '';
          const errors = item.errors?.length ? `: ${item.errors.join('; ')}` : '';
          const hints = formatRepairHints(item.repair_hints, {compact: true});
          const hintText = hints ? `\n  hints:\n${hints}` : '';
          return `- ${item.index}:${title} ${mark} (${item.attempts || 0} attempt${item.attempts === 1 ? '' : 's'})${errors}${hintText}`;
        }).join('\n')}`);
      }
      if (typeof result.count === 'number') lines.push(`draft problems: ${result.count}`);
      if (typeof result.requested_count === 'number') lines.push(`requested problems: ${result.requested_count}`);
      return lines.join('\n\n') || JSON.stringify(result, null, 2);
    }

    function formatDependencyInstallResult(result) {
      const lines = [];
      if (result.message) lines.push(result.message);
      if (result.installed?.length) lines.push(`packages:\n- ${result.installed.join('\n- ')}`);
      const status = result.dependency_status;
      if (status?.requirements?.length) {
        const rows = status.requirements.map(req => {
          const mark = req.installed ? 'installed' : 'missing';
          const version = req.installed_version ? ` ${req.installed_version}` : '';
          return `- ${req.pip || req.package}: ${mark}${version}`;
        });
        lines.push(`dependencies:\n${rows.join('\n')}`);
      } else if (result.ok) {
        lines.push('dependencies: no package requirements found');
      }
      if (result.validation_errors?.length) lines.push(`draft validation still has errors:\n- ${result.validation_errors.join('\n- ')}`);
      if (result.errors?.length) lines.push(`errors:\n- ${result.errors.join('\n- ')}`);
      if (result.warnings?.length) lines.push(`warnings:\n- ${result.warnings.join('\n- ')}`);
      if (result.stdout) lines.push(`stdout:\n${result.stdout}`);
      if (result.stderr) lines.push(`stderr:\n${result.stderr}`);
      if (result.detail) lines.push(`error:\n${result.detail}`);
      return lines.join('\n\n') || JSON.stringify(result, null, 2);
    }

    function formatRepairHints(hints, options = {}) {
      if (!Array.isArray(hints) || !hints.length) return '';
      const prefix = options.compact ? '  -' : '-';
      return hints.map(hint => {
        if (!hint || typeof hint !== 'object') return `${prefix} ${hint}`;
        const code = hint.code ? `[${hint.code}] ` : '';
        const action = hint.action || hint.problem || JSON.stringify(hint);
        return `${prefix} ${code}${action}`;
      }).join('\n');
    }

    async function postAuthoring(url) {
      const content = document.getElementById('authorJson').value;
      const overwrite = document.getElementById('authorOverwrite').checked;
      return await postJson(url, {content, overwrite});
    }

    async function postJson(url, payload, method = 'POST') {
      const res = await fetch(url, {
        method,
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
      });
      return await res.json();
    }

    function renderAuthorResult(result, action) {
      const ok = Boolean(result.ok);
      setAuthorStatus(ok ? action : 'Needs fixes', ok);
      const lines = [];
      if (result.problem_id) lines.push(`problem_id: ${result.problem_id}`);
      if (typeof result.created_count === 'number' && typeof result.total === 'number') {
        lines.push(`created: ${result.created_count}/${result.total}`);
      }
      if (result.path) lines.push(`path: ${result.path}`);
      if (result.results?.length) {
        const rows = result.results.map(item => {
          const label = item.problem_id || item.problem?.id || 'unknown';
          const mark = item.created ? 'created' : 'not created';
          const detail = item.errors?.length ? ` (${item.errors.join('; ')})` : '';
          return `- ${label}: ${mark}${detail}`;
        });
        lines.push(`results:\n${rows.join('\n')}`);
      }
      if (result.errors?.length) lines.push(`errors:\n- ${result.errors.join('\n- ')}`);
      if (result.warnings?.length) lines.push(`warnings:\n- ${result.warnings.join('\n- ')}`);
      const repairHints = formatRepairHints(result.repair_hints);
      if (repairHints) lines.push(`repair hints:\n${repairHints}`);
      if (!result.errors?.length && !result.warnings?.length && !result.path) {
        lines.push(JSON.stringify(result, null, 2));
      }
      document.getElementById('authorOutput').textContent = lines.join('\n\n') || 'OK';
    }

    function renderAuthorPreview(result) {
      renderDraftPreview('authorPreview', 'authorPreviewStatus', result);
    }

    function renderDraftPreview(boxId, statusId, result) {
      const box = document.getElementById('authorPreview');
      const status = document.getElementById('authorPreviewStatus');
      const targetBox = document.getElementById(boxId) || box;
      const targetStatus = document.getElementById(statusId) || status;
      const problems = result.problems?.length ? result.problems : result.problem ? [result.problem] : [];
      const messages = renderValidationMessages(result);
      if (!problems.length) {
        targetStatus.className = 'badge error';
        targetStatus.textContent = 'No preview';
        targetBox.innerHTML = messages || '<div class="empty">No valid problem JSON to preview yet.</div>';
        return;
      }
      targetStatus.className = result.ok ? 'badge ok' : 'badge error';
      targetStatus.textContent = result.ok
        ? problems.length === 1 ? 'Ready to add' : `${problems.length} ready to add`
        : 'Needs fixes';
      targetBox.innerHTML = messages + problems.map((problem, idx) => `
        <div class="test-card">
          <div class="test-name">Problem ${idx + 1}</div>
          ${renderProblemPreview(problem, {includeAnswer: true, includeTests: true})}
        </div>
      `).join('');
      typesetMath(targetBox);
    }

    function renderValidationMessages(result) {
      const blocks = [];
      if (result.errors?.length) {
        blocks.push(`
          <div class="validation-message error">
            <div class="validation-message-title">Validation errors</div>
            <ul>${result.errors.map(error => `<li>${escapeHtml(error)}</li>`).join('')}</ul>
          </div>
        `);
      }
      if (result.warnings?.length) {
        blocks.push(`
          <div class="validation-message warning">
            <div class="validation-message-title">Warnings</div>
            <ul>${result.warnings.map(warning => `<li>${escapeHtml(warning)}</li>`).join('')}</ul>
          </div>
        `);
      }
      if (result.repair_hints?.length) {
        blocks.push(`
          <div class="validation-message warning">
            <div class="validation-message-title">Repair hints</div>
            <ul>${result.repair_hints.map(hint => `<li>${escapeHtml(hint.action || hint.problem || hint.code || JSON.stringify(hint))}</li>`).join('')}</ul>
          </div>
        `);
      }
      return blocks.length ? `<div class="validation-messages">${blocks.join('')}</div>` : '';
    }

    function syncAuthorJsonFromResult(result) {
      const problems = result?.problems?.length ? result.problems : result?.problem ? [result.problem] : [];
      if (!problems.length) return;
      document.getElementById('authorJson').value = stringifyProblemJson(problems.length === 1 ? problems[0] : problems);
      resetAuthorFilePicker();
    }

    function resetAuthorPreview(message) {
      const status = document.getElementById('authorPreviewStatus');
      const box = document.getElementById('authorPreview');
      status.className = 'badge';
      status.textContent = 'Not checked';
      box.innerHTML = `<div class="empty">${escapeHtml(message)}</div>`;
    }

    function resetAuthorFilePicker() {
      const input = document.getElementById('authorFile');
      if (input) input.value = '';
      const name = document.getElementById('authorFileName');
      if (name) name.textContent = 'No file loaded';
    }

    function clearAuthorInput() {
      document.getElementById('authorJson').value = '';
      authorTemplateLoaded = false;
      resetAuthorFilePicker();
      resetAuthorPreview('Paste JSON or import a .json file.');
      document.getElementById('authorOutput').textContent = 'Paste JSON or import a .json file.';
      setAuthorStatus('Cleared.', null);
      setDraftDependencyStatus('authorDepsStatus', 'Not checked', null);
    }

    function cleanAuthorJson() {
      const editor = document.getElementById('authorJson');
      const before = editor.value;
      const after = cleanModelJsonText(before);
      editor.value = after;
      resetAuthorFilePicker();
      resetAuthorPreview('Validate the cleaned JSON to preview it.');
      setAuthorStatus(after === before ? 'No cleanup needed.' : 'Cleaned JSON text.', true);
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

    function renderProblemPreview(problem, {includeAnswer = false, includeTests = false} = {}) {
      const tags = (problem.tags || []).map(t => renderClickableTag(t)).join('');
      const visible = problem.visible_tests || [];
      const hidden = problem.hidden_tests || [];
      const constraints = (problem.constraints || []).map(c => `<li>${escapeHtml(c)}</li>`).join('');
      const checker = problem.checker ? `<span class="tag">checker: ${escapeHtml(problem.checker.type || 'exact')}</span>` : '';
      const answer = includeAnswer ? `
        <div class="test-card">
          <div class="test-name">Reference solution</div>
          <pre>${escapeHtml(problem.reference_solution || problem.solution || '')}</pre>
        </div>
        ${problem.solution_explanation ? `<div class="test-card"><div class="test-name">Explanation</div><div class="statement">${markdownLite(problem.solution_explanation)}</div></div>` : ''}
      ` : '';
      const tests = includeTests ? `
        <div class="test-card">
          <div class="test-name">Tests</div>
          <div class="kv">
            <div><strong>Visible:</strong> ${escapeHtml(visible.length)}</div>
            <div><strong>Hidden:</strong> ${escapeHtml(hidden.length)}</div>
          </div>
          <details><summary>visible_tests</summary><pre>${escapeHtml(stringifyProblemJson(visible))}</pre></details>
          <details><summary>hidden_tests</summary><pre>${escapeHtml(stringifyProblemJson(hidden))}</pre></details>
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
        ${answer}
        ${tests}
      `;
    }

    function setAuthorStatus(text, ok = null) {
      const status = document.getElementById('authorStatus');
      status.className = ok === null ? 'badge' : ok ? 'badge ok' : 'badge error';
      status.textContent = text;
    }

    async function copyAuthorPrompt() {
      const text = document.getElementById('authorPrompt').textContent;
      try {
        await navigator.clipboard.writeText(text);
        setAuthorStatus('Prompt copied.', true);
      } catch {
        setAuthorStatus('Copy failed.', false);
      }
    }

    async function copyAuthorSchema() {
      try {
        if (!authorSchemaCache) {
          const res = await fetch('/api/authoring/schema');
          const data = await res.json();
          authorSchemaCache = data.schema || {};
        }
        await navigator.clipboard.writeText(JSON.stringify(authorSchemaCache, null, 2));
        setAuthorStatus('API schema copied.', true);
      } catch {
        setAuthorStatus('Schema copy failed.', false);
      }
    }

    async function loadRuntimeStatus() {
      const query = currentProblem ? `?problem_id=${encodeURIComponent(currentProblem.id)}` : '';
      const res = await fetch(`/api/runtime${query}`);
      runtimeState = await res.json();
      renderRuntimeStatus();
    }

    function renderRuntimeStatus() {
      if (!runtimeState) return;
      const python = runtimeState.python || {};
      document.getElementById('runtimeEnv').innerHTML = `
        <div class="runtime-row">
          <span class="runtime-package">Python</span>
          <span class="badge ok">${escapeHtml(python.version || '')}</span>
        </div>
        <div class="runtime-row">
          <span class="runtime-package">Virtualenv</span>
          <span class="badge ${python.in_virtualenv ? 'ok' : 'error'}">${python.in_virtualenv ? 'Active' : 'Not detected'}</span>
        </div>
        <div class="runtime-row">
          <span class="runtime-package">Executable</span>
          <code>${escapeHtml(python.executable || '')}</code>
        </div>
      `;

      const groups = runtimeState.groups || {};
      document.getElementById('runtimeGroups').innerHTML = [
        renderRuntimeGroup('base', groups.base),
        renderRuntimeGroup('current_problem', groups.current_problem),
        renderRuntimeGroup('optional_ml', groups.optional_ml),
      ].join('');
    }

    function renderRuntimeGroup(scope, group) {
      if (!group) return '';
      const requirements = group.requirements || [];
      const missing = group.missing || [];
      const ok = missing.length === 0;
      const titleExtra = group.problem ? `: ${escapeHtml(group.problem.title)}` : '';
      const installButton = runtimeInstallButton(scope, missing.length);
      const rows = requirements.length
        ? requirements.map(req => {
          const installed = Boolean(req.installed);
          const version = req.installed_version ? ` ${req.installed_version}` : '';
          return `
            <div class="runtime-row">
              <span class="runtime-package"><code>${escapeHtml(req.pip || req.package)}</code></span>
              <span class="badge ${installed ? 'ok' : 'error'}">${installed ? `Installed${escapeHtml(version)}` : 'Missing'}</span>
            </div>
          `;
        }).join('')
        : '<div class="runtime-row"><span class="runtime-package">No extra packages</span><span class="badge ok">Ready</span></div>';

      const command = group.install_command
        ? `<div class="install-command"><strong>Command:</strong> <code>${escapeHtml(group.install_command)}</code></div>`
        : '';

      return `
        <div class="runtime-card">
          <div class="panel-head">
            <h2 class="panel-title">${escapeHtml(group.label || scope)}${titleExtra}</h2>
            <div class="runtime-actions">
              <span class="badge ${ok ? 'ok' : 'error'}">${ok ? 'Ready' : `${missing.length} missing`}</span>
              ${installButton}
            </div>
          </div>
          <div>${rows}</div>
          ${command ? `<div class="panel-body">${command}</div>` : ''}
        </div>
      `;
    }

    function runtimeInstallButton(scope, missingCount) {
      if (!missingCount || scope === 'base') return '';
      if (scope === 'current_problem') {
        return '<button class="small primary" onclick="installRuntimePackages(\'current_problem\')">Install current dependencies</button>';
      }
      if (scope === 'optional_ml') {
        return '<button class="small primary" onclick="installRuntimePackages(\'optional_ml\')">Install ML stack</button>';
      }
      return '';
    }

    async function openRuntimeAndInstallCurrent() {
      setView('runtime');
      await loadRuntimeStatus();
      await installRuntimePackages('current_problem');
    }

    async function installRuntimePackages(scope) {
      const payload = {scope};
      if (scope === 'current_problem') {
        if (!currentProblem) return;
        payload.problem_id = currentProblem.id;
      }

      document.getElementById('runtimeInstallStatus').className = 'badge';
      document.getElementById('runtimeInstallStatus').textContent = 'Installing...';
      document.getElementById('runtimeOutput').textContent = 'Running pip install...';

      const res = await fetch('/api/runtime/install', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      runtimeState = data.status || runtimeState;
      const ok = Boolean(data.ok);
      document.getElementById('runtimeInstallStatus').className = ok ? 'badge ok' : 'badge error';
      document.getElementById('runtimeInstallStatus').textContent = data.message || (ok ? 'Installed' : 'Failed');
      document.getElementById('runtimeOutput').textContent = [
        data.message || '',
        data.installed?.length ? `Packages: ${data.installed.join(', ')}` : '',
        data.stdout ? `stdout:\n${data.stdout}` : '',
        data.stderr ? `stderr:\n${data.stderr}` : '',
        data.detail ? `error:\n${data.detail}` : ''
      ].filter(Boolean).join('\n\n') || 'No output.';

      renderRuntimeStatus();
      if (currentProblem) {
        const problemId = currentProblem.id;
        const problemRes = await fetch(`/api/problems/${encodeURIComponent(problemId)}`);
        currentProblem = await problemRes.json();
        renderDependencyStatus();
      }
    }

    function setView(view) {
      const catalogView = document.getElementById('catalogView');
      const llmView = document.getElementById('llmView');
      const authorView = document.getElementById('authorView');
      const codeView = document.getElementById('codeView');
      const manageView = document.getElementById('manageView');
      const solutionView = document.getElementById('solutionView');
      const runtimeView = document.getElementById('runtimeView');
      const historyView = document.getElementById('historyView');
      const codeTab = document.getElementById('codeTab');
      const manageTab = document.getElementById('manageTab');
      const solutionTab = document.getElementById('solutionTab');
      const runtimeTab = document.getElementById('runtimeTab');
      const historyTab = document.getElementById('historyTab');
      const showCatalog = view === 'catalog';
      const showLlm = view === 'llm';
      const showAuthor = view === 'author';
      const showManage = view === 'manage';
      const showHistory = view === 'history';
      const showSolution = view === 'solution';
      const showRuntime = view === 'runtime';
      catalogView.hidden = !showCatalog;
      llmView.hidden = !showLlm;
      authorView.hidden = !showAuthor;
      codeView.hidden = showCatalog || showLlm || showAuthor || showManage || showHistory || showSolution || showRuntime;
      manageView.hidden = !showManage;
      solutionView.hidden = !showSolution;
      runtimeView.hidden = !showRuntime;
      historyView.hidden = !showHistory;
      codeTab.classList.toggle('active', !showCatalog && !showLlm && !showAuthor && !showManage && !showHistory && !showSolution && !showRuntime);
      manageTab.classList.toggle('active', showManage);
      solutionTab.classList.toggle('active', showSolution);
      runtimeTab.classList.toggle('active', showRuntime);
      historyTab.classList.toggle('active', showHistory);
      if (showCatalog) {
        renderCatalog();
      }
      if (showAuthor) {
        loadAuthoringPanel();
      }
      if (showLlm) {
        loadLlmPanel();
      }
      if (showSolution) {
        loadSolution();
      }
      if (showRuntime) {
        loadRuntimeStatus();
      }
      if (showManage) {
        loadManagerForCurrentProblem();
      }
      if (showHistory) {
        loadCurrentHistory();
        loadAllHistory();
        loadWrongProblems();
      }
      if (!showCatalog && !showLlm && !showAuthor && !showManage && !showHistory && !showSolution && !showRuntime) {
        setTimeout(() => codeMirrorEditor?.refresh(), 0);
      }
    }

    async function loadSolution({force = false} = {}) {
      if (!currentProblem) return;
      if (!force && solutionLoadedFor === currentProblem.id) return;
      const body = document.getElementById('solutionBody');
      body.innerHTML = '<div class="empty">Loading solution...</div>';
      const res = await fetch(`/api/problems/${encodeURIComponent(currentProblem.id)}/solution`);
      const data = await res.json();
      solutionLoadedFor = currentProblem.id;

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

      body.innerHTML = `
        ${explanation}
        ${complexityHtml}
        ${solution}
      `;
      typesetMath(body);
    }

    async function submitCode(mode) {
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
      document.getElementById('resultMeta').textContent = mode === 'run' ? 'Running visible tests' : 'Submitting';
      document.getElementById('result').innerHTML = '<div class="empty">Running tests...</div>';
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
        <div class="summary">
          <span class="status-text wrong">Compile Error</span>
          <span class="badge error">${escapeHtml(data.error_type || 'SyntaxError')}</span>
        </div>
        <div class="case-list">
          <div class="case-card failed">
            <div class="case-title">
              <div class="case-title-left">
                <span class="case-dot"></span>
                <span>Line ${escapeHtml(data.line || '?')}</span>
              </div>
              <span class="status-text wrong">failed</span>
            </div>
            <pre>${escapeHtml(data.message || 'Invalid Python syntax')}${data.text ? '\n\n' + escapeHtml(data.text) : ''}</pre>
          </div>
        </div>
      `;
    }

    function renderResult(data, mode = 'run') {
      const accepted = data.status === 'Accepted';
      const resultMeta = document.getElementById('resultMeta');
      resultMeta.className = accepted ? 'badge ok' : 'badge error';
      resultMeta.textContent = `#${data.submission_id} ${data.passed}/${data.total}`;

      const tests = data.tests || [];
      const cards = tests.map((t, idx) => {
        return renderRunCaseCard(t, idx, currentProblem, mode);
      }).join('');
      const caseStrip = tests.length ? `
        <div class="result-case-strip">
          ${tests.map((test, idx) => `
            <span class="case-tab ${test.passed ? 'passed' : 'failed'}">Case ${idx + 1}</span>
          `).join('')}
        </div>
      ` : '';

      const dependencyStatus = data.metadata?.dependency_status || null;
      const installCommand = dependencyStatus?.install_command || '';
      const errorTitle = data.status === 'Missing Dependencies' ? 'Missing dependencies' : 'Runtime error';
      const installLine = installCommand ? `\n\nInstall command:\n${installCommand}` : '';
      const errorBlock = data.error ? `
        <div class="case-card failed">
          <div class="case-title"><span>${escapeHtml(errorTitle)}</span><span class="status-text wrong">failed</span></div>
          <pre>${escapeHtml(data.error + installLine)}</pre>
        </div>
      ` : '';

      const rawOutput = [data.stdout ? ['stdout', data.stdout] : null, data.stderr ? ['stderr', data.stderr] : null]
        .filter(Boolean)
        .map(([name, text]) => `<details><summary>${name}</summary><pre>${escapeHtml(text)}</pre></details>`)
        .join('');

      document.getElementById('result').innerHTML = `
        <div class="result-summary-card ${accepted ? 'accepted' : 'failed'}">
          <div>
            <div class="result-title status-text ${accepted ? 'accepted' : 'wrong'}">${escapeHtml(data.status)}</div>
            <div class="result-subtitle">${mode === 'run' ? 'Visible tests' : 'Visible + hidden tests'} · submission #${escapeHtml(data.submission_id || '')}</div>
          </div>
          <span class="badge ${accepted ? 'ok' : 'error'}">${escapeHtml(data.passed)}/${escapeHtml(data.total)} passed</span>
        </div>
        ${caseStrip}
        <div class="case-list">${cards || errorBlock || '<div class="empty">No test details returned.</div>'}${cards ? errorBlock : ''}</div>
        ${rawOutput}
      `;
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
            <td><button class="small" onclick="loadSubmissionDetail(${escapeHtml(r.id)})">Detail</button></td>
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
            <td><button class="small" onclick="loadSubmissionDetail(${escapeHtml(r.latest_submission_id)})">Latest</button></td>
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

    function initCodeEditor() {
      if (codeMirrorEditor || !window.CodeMirror || !codeEl()) return;
      codeMirrorEditor = window.CodeMirror.fromTextArea(codeEl(), {
        mode: 'python',
        theme: 'material-darker',
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
        updateLineNumbers();
        updateCursorStatus();
        queueCheck();
      });
      codeMirrorEditor.on('cursorActivity', updateCursorStatus);
      codeMirrorEditor.on('focus', updateCursorStatus);
      setTimeout(() => codeMirrorEditor?.refresh(), 0);
      updateCursorStatus();
    }

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

    document.addEventListener('input', e => {
      if (e.target && e.target.id === 'code') {
        updateLineNumbers();
        updateCursorStatus();
        queueCheck();
      }
      if (e.target && e.target.matches('[data-manager-input-index]')) {
        resetManagerGeneratedOutput();
        syncManagerArgsFromFields();
      }
    });

    document.addEventListener('scroll', e => {
      if (e.target && e.target.id === 'code') {
        document.getElementById('lineNumbers').scrollTop = e.target.scrollTop;
      }
    }, true);

    document.addEventListener('keyup', e => {
      if (e.target && e.target.id === 'code') updateCursorStatus();
    });

    document.addEventListener('click', e => {
      if (e.target && e.target.id === 'code') updateCursorStatus();
    });

    document.addEventListener('change', e => {
      if (!e.target) return;
      if (e.target.id === 'llmAttachmentInput') {
        handleLlmAttachmentChange(e.target);
        return;
      }
      if (e.target.id !== 'authorFile') return;
      const file = e.target.files && e.target.files[0];
      if (!file) return;
      document.getElementById('authorFileName').textContent = file.name;
      const reader = new FileReader();
      reader.onload = () => {
        document.getElementById('authorJson').value = String(reader.result || '');
        resetAuthorPreview('Validate the uploaded JSON to preview it.');
        setAuthorStatus(`Loaded ${file.name}`, true);
        e.target.value = '';
      };
      reader.onerror = () => {
        resetAuthorFilePicker();
        setAuthorStatus('File load failed.', false);
      };
      reader.readAsText(file);
    });

    document.addEventListener('keydown', e => {
      if (!e.target || e.target.id !== 'code') return;
      if (e.key === 'Tab') {
        e.preventDefault();
        const el = e.target;
        const start = el.selectionStart;
        const end = el.selectionEnd;
        el.value = el.value.slice(0, start) + '    ' + el.value.slice(end);
        el.selectionStart = el.selectionEnd = start + 4;
        updateLineNumbers(currentSyntax?.ok ? null : currentSyntax.line);
        queueCheck();
      }
    });

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

        if (trimmed === '$$' || trimmed === '\\[') {
          const closing = trimmed === '$$' ? '$$' : '\\]';
          const math = [];
          i += 1;
          while (i < lines.length && lines[i].trim() !== closing) {
            math.push(lines[i]);
            i += 1;
          }
          i += i < lines.length ? 1 : 0;
          blocks.push(`<div class="math-block">\\[${escapeHtml(math.join('\n'))}\\]</div>`);
          continue;
        }

        if (isTableStart(lines, i)) {
          const tableLines = [lines[i], lines[i + 1]];
          i += 2;
          while (i < lines.length && lines[i].includes('|') && lines[i].trim()) {
            tableLines.push(lines[i]);
            i += 1;
          }
          blocks.push(renderMarkdownTable(tableLines));
          continue;
        }

        const heading = trimmed.match(/^(#{1,4})\s+(.+)$/);
        if (heading) {
          const level = Math.min(heading[1].length + 1, 4);
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

        const unordered = trimmed.match(/^[-*]\s+(.+)$/);
        if (unordered) {
          const items = [];
          while (i < lines.length) {
            const item = lines[i].trim().match(/^[-*]\s+(.+)$/);
            if (!item) break;
            items.push(`<li>${renderInlineMarkdown(item[1])}</li>`);
            i += 1;
          }
          blocks.push(`<ul>${items.join('')}</ul>`);
          continue;
        }

        const ordered = trimmed.match(/^\d+\.\s+(.+)$/);
        if (ordered) {
          const items = [];
          while (i < lines.length) {
            const item = lines[i].trim().match(/^\d+\.\s+(.+)$/);
            if (!item) break;
            items.push(`<li>${renderInlineMarkdown(item[1])}</li>`);
            i += 1;
          }
          blocks.push(`<ol>${items.join('')}</ol>`);
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

      return blocks.join('');
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
      text = text.replace(/\\\[([^\n]+?)\\\]/g, (_, tex) => stash(`<span class="math-inline">\\(${escapeHtml(tex)}\\)</span>`));
      text = text.replace(/\$\$([^$\n]+?)\$\$/g, (_, tex) => stash(`<span class="math-inline">\\(${escapeHtml(tex)}\\)</span>`));
      text = text.replace(/\\\((.+?)\\\)/g, (_, tex) => stash(`<span class="math-inline">\\(${escapeHtml(tex)}\\)</span>`));
      text = text.replace(/\$([^$\n]+?)\$/g, (_, tex) => stash(`<span class="math-inline">\\(${escapeHtml(tex)}\\)</span>`));

      let html = escapeHtml(text)
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/\*([^*]+)\*/g, '<em>$1</em>')
        .replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noreferrer">$1</a>');

      for (const [key, value] of placeholders) {
        html = html.replaceAll(key, value);
      }
      return html;
    }

    function typesetMath(element) {
      if (!element || !window.MathJax || !window.MathJax.typesetPromise) return;
      window.MathJax.typesetPromise([element]).catch(() => {});
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

    function initManagerSplitter() {
      const splitter = document.getElementById('managerSplitter');
      const panel = document.getElementById('managerPanel');
      if (!splitter || !panel) return;

      let dragging = false;
      splitter.addEventListener('pointerdown', event => {
        dragging = true;
        splitter.classList.add('dragging');
        splitter.setPointerCapture(event.pointerId);
        document.body.style.userSelect = 'none';
      });

      splitter.addEventListener('pointermove', event => {
        if (!dragging) return;
        const rect = panel.getBoundingClientRect();
        const minLeft = 320;
        const maxLeft = Math.max(minLeft, rect.width - 320);
        const left = Math.min(maxLeft, Math.max(minLeft, event.clientX - rect.left));
        panel.style.setProperty('--manager-left', `${left}px`);
      });

      const stopDragging = event => {
        if (!dragging) return;
        dragging = false;
        splitter.classList.remove('dragging');
        document.body.style.userSelect = '';
        if (event?.pointerId !== undefined) {
          try {
            splitter.releasePointerCapture(event.pointerId);
          } catch {
            // Pointer capture may already be released by the browser.
          }
        }
      };

      splitter.addEventListener('pointerup', stopDragging);
      splitter.addEventListener('pointercancel', stopDragging);
    }

    window.addEventListener('load', initCodeEditor);
    initManagerSplitter();
    loadProblems();
  </script>
</body>
</html>
'''
