from __future__ import annotations

"""Stitch Foundation CSS segment for the Mnemosyne UI.

Order matters: import through mnemosyne.ui_css.APP_CSS only.
"""

STITCH_FOUNDATION_CSS = r"""    /* Stitch alignment pass: Intellectual Minimalist workspace */
    :root {
      font-family: "Geist", ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      --bg: #fcf9f4;
      --panel: #fcf9f4;
      --paper: #ffffff;
      --surface-lowest: #ffffff;
      --surface-low: #f6f3ee;
      --surface: #f0ede9;
      --surface-high: #ebe8e3;
      --surface-highest: #e5e2dd;
      --line: #c4c7c7;
      --line-soft: #e5e2dd;
      --text: #1c1c19;
      --muted: #444748;
      --subtle: #747878;
      --accent: #030303;
      --secondary: #6d5c45;
      --accepted: #51735b;
      --wrong: #ba1a1a;
      --editor: #ffffff;
      --editor-gutter: #f6f3ee;
      --editor-text: #1c1c19;
    }

    body {
      background: var(--bg);
      color: var(--text);
      font-family: "Geist", ui-sans-serif, system-ui, sans-serif;
      font-size: 15px;
      letter-spacing: 0;
    }

    h1, h2, h3, .brand, .problem-title, .catalog-title, .panel-title {
      font-family: "Literata", Georgia, serif;
    }

    code, pre, textarea.code-editor, .CodeMirror, .tag, .badge, .learning-tab, .console-tab,
    .io-summary, .console-field-value, .function-call-line, .catalog-search input {
      font-family: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }

    button {
      border-color: var(--line);
      border-radius: 4px;
      background: var(--surface-lowest);
      color: var(--text);
      font-weight: 600;
      box-shadow: none;
    }

    button:hover {
      background: var(--surface-high);
      border-color: var(--subtle);
    }

    button.primary {
      background: var(--primary, var(--accent));
      border-color: var(--primary, var(--accent));
      color: #fff;
    }

    .topbar {
      height: 56px;
      gap: 24px;
      padding: 0 24px;
      background: var(--bg);
      border-bottom: 1px solid var(--line);
    }

    .brand {
      flex-direction: row;
      align-items: center;
      gap: 10px;
      font-size: 20px;
      font-weight: 650;
      line-height: 1;
      color: var(--accent);
      letter-spacing: -0.01em;
    }

    .brand::before {
      content: "";
      width: 32px;
      height: 32px;
      border-radius: 999px;
      background: var(--accent);
      box-shadow: inset 0 0 0 8px var(--accent), inset 0 0 0 10px var(--bg);
      display: inline-block;
    }

    .brand-subtitle {
      display: none;
    }

    .top-nav {
      gap: 22px;
      padding-left: 24px;
      border-left: 1px solid var(--line);
    }

    .top-nav button {
      border-radius: 0;
      padding: 17px 0 14px;
      border-bottom: 2px solid transparent;
      color: var(--muted);
      background: transparent;
      font-weight: 500;
      font-size: 15px;
    }

    .top-nav button.active {
      color: var(--accent);
      background: transparent;
      border-bottom-color: var(--accent);
      font-weight: 700;
    }

    #problemSelect {
      min-width: 250px;
      border-radius: 4px;
      background: var(--surface-lowest);
      border-color: var(--line);
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-size: 13px;
    }

    .practice-top-actions {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    body:not([data-mode="practice"]) .practice-top-actions {
      display: none;
    }

    .badge {
      min-height: 24px;
      padding: 2px 8px;
      border-radius: 4px;
      background: var(--surface-lowest);
      border-color: var(--line);
      color: var(--muted);
      font-size: 12px;
    }

    .layout {
      grid-template-columns: minmax(360px, var(--main-left, 50%)) 1px minmax(460px, 1fr);
      height: calc(100vh - 56px);
      background: var(--bg);
    }

    .main-splitter {
      min-width: 1px;
      background: var(--line);
      border: 0;
    }

    .main-splitter:hover,
    .main-splitter.dragging {
      background: var(--accent);
    }

    .problem-pane,
    .work-pane {
      background: var(--bg);
    }

    .problem-pane {
      border-right: 0;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .learning-tabs {
      flex: 0 0 auto;
      justify-content: center;
      margin: 0;
      padding: 10px 12px;
      border: 0;
      border-bottom: 1px solid var(--line);
      border-radius: 0;
      background: var(--surface);
    }

    .learning-tabs::before {
      content: "";
      display: block;
      position: absolute;
    }

    .learning-tab {
      border-radius: 4px;
      padding: 7px 12px;
      color: var(--muted);
      font-size: 13px;
      font-weight: 500;
      background: transparent;
      border: 1px solid transparent;
    }

    .learning-tab.active {
      color: var(--accent);
      background: var(--surface-lowest);
      border-color: var(--line);
      box-shadow: none;
      font-weight: 600;
    }

    .problem-inner {
      width: 100%;
      max-width: 760px;
      margin: 0 auto;
      padding: 40px 48px 64px;
      overflow: auto;
    }

    .problem-title {
      font-size: 32px;
      line-height: 40px;
      font-weight: 650;
      margin-bottom: 16px;
      letter-spacing: -0.01em;
    }

    .meta {
      gap: 8px;
      margin-bottom: 28px;
    }

    .tag {
      border-radius: 4px;
      border: 1px solid var(--line);
      padding: 3px 8px;
      background: var(--surface-low);
      color: var(--muted);
      font-size: 12px;
      font-weight: 500;
    }

    .difficulty {
      background: rgba(109, 92, 69, 0.09);
      border-color: var(--secondary);
      color: var(--secondary);
    }

    .tag.tag-click:hover {
      background: var(--secondary-container, #f7dfc2);
      color: var(--accent);
      border-color: var(--secondary);
    }

    .statement {
      color: var(--muted);
      font-size: 16px;
      line-height: 1.65;
    }

    .statement h1,
    .statement h2,
    .statement h3 {
      font-family: "Literata", Georgia, serif;
      color: var(--text);
      font-weight: 650;
      margin: 28px 0 10px;
    }

    .statement h1:first-child,
    .statement h2:first-child,
    .statement h3:first-child {
      margin-top: 0;
    }

    .statement pre.md-code,
    .math-block,
    .test-card,
    .console-field-value,
    .io-block pre {
      border-radius: 4px;
      background: var(--surface-low);
      border: 1px solid var(--line-soft);
      box-shadow: none;
    }

    code {
      border-radius: 4px;
      background: var(--surface-high);
      border-color: var(--line-soft);
      color: var(--text);
      font-size: 0.9em;
    }

    body[data-mode="practice"] .work-tabs {
      display: none;
    }

    body[data-mode="practice"] .work-pane {
      grid-template-rows: minmax(0, 1fr);
      border-left: 0;
    }

    #codeView.view {
      padding: 0;
      background: var(--bg);
    }

    .practice-workspace {
      height: 100%;
      min-height: 0;
      grid-template-rows: minmax(0, 1fr) minmax(220px, 34%);
      gap: 0;
      background: var(--bg);
    }

    .practice-editor-card,
    .practice-console-card {
      border-radius: 0;
      border: 0;
      background: var(--surface-lowest);
    }

    .practice-editor-card {
      min-height: 0;
      border-bottom: 1px solid var(--line);
    }

    .practice-editor-toolbar,
    .practice-console-head {
      min-height: 40px;
      background: var(--surface-low);
      border-bottom: 1px solid var(--line);
      padding: 6px 12px;
    }

    .practice-editor-title {
      font-family: "Geist", ui-sans-serif, sans-serif;
      font-size: 16px;
      font-weight: 700;
    }

    .code-mark {
      color: var(--accepted);
      font-family: "JetBrains Mono", ui-monospace, monospace;
    }

    .editor-meta,
    .cursor-status,
    .status-line {
      color: var(--subtle);
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-size: 12px;
    }

    .practice-editor-toolbar .small {
      border: 0;
      background: transparent;
      color: var(--muted);
      font-size: 12px;
    }

    .practice-editor-shell {
      background: var(--surface-lowest);
    }

    .practice-editor-shell .editor-body {
      min-height: 0;
      background: var(--surface-lowest);
    }

    .editor-body.cm-enabled .CodeMirror {
      background: var(--surface-lowest);
      color: var(--text);
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-size: 14px;
      line-height: 1.55;
    }

    .editor-body.cm-enabled .CodeMirror-gutters {
      background: var(--surface-lowest);
      border-right: 1px solid var(--line-soft);
    }

    .editor-body.cm-enabled .CodeMirror-linenumber {
      color: #6f8aa0;
    }

    .editor-body.cm-enabled .CodeMirror-cursor {
      border-left-color: var(--accent);
    }

    textarea.code-editor {
      background: var(--surface-lowest);
      color: var(--text);
    }

    .editor-footer {
      background: var(--surface-lowest);
      border-top: 0;
      padding: 8px 12px 10px;
    }

    .practice-console-card {
      background: var(--surface-lowest);
    }

    .console-tabs {
      gap: 14px;
    }

    .console-tab {
      padding: 7px 0;
      font-family: "Geist", ui-sans-serif, sans-serif;
      font-size: 16px;
      border-bottom-color: transparent;
    }

    .console-tab.active {
      border-bottom-color: var(--secondary);
      color: var(--text);
    }

    .console-actions button {
      font-size: 12px;
      padding: 5px 10px;
    }

    .practice-testcases,
    #practiceResultPane,
    #practiceErrorPane {
      padding: 18px 24px;
      background: var(--surface-lowest);
    }

    .case-tab {
      border-radius: 4px;
      background: var(--surface);
      color: var(--muted);
      padding: 9px 16px;
      font-family: "Geist", ui-sans-serif, sans-serif;
      font-size: 15px;
    }

    .case-tab.active {
      background: var(--surface-highest);
      color: var(--text);
    }

    .case-tab.passed {
      background: rgba(81, 115, 91, 0.12);
      color: var(--accepted);
    }

    .case-tab.failed {
      background: var(--error-container, #ffdad6);
      color: var(--wrong);
    }

    .function-call-line,
    .console-field-label {
      color: var(--subtle);
    }

    .console-field-value {
      padding: 12px 14px;
      color: var(--text);
    }

    .result-summary-card,
    .case-card,
    .history-panel,
    .result-panel,
    .runtime-card,
    .catalog-sidebar,
    .catalog-main,
    .manager-header-card {
      border-radius: 4px;
      border-color: var(--line);
      background: var(--surface-lowest);
      box-shadow: none;
    }

    .panel-head,
    .catalog-sidebar-head {
      background: var(--surface-low);
      border-bottom-color: var(--line);
    }

    .panel-title,
    .catalog-title {
      font-weight: 650;
      color: var(--text);
    }

    body[data-mode="problems"] .view,
    body[data-mode="manage"] .view,
    body[data-mode="create"] .view,
    body[data-mode="llm"] .view {
      height: calc(100vh - 56px);
      background: var(--bg);
    }

    #catalogView.view {
      padding: 48px 24px;
    }

    .catalog-layout {
      display: block;
      max-width: 1120px;
      margin: 0 auto;
      min-height: auto;
    }

    .catalog-sidebar {
      border: 0;
      background: transparent;
      margin-bottom: 24px;
      overflow: visible;
    }

    .catalog-sidebar-head {
      display: inline-block;
      padding: 0;
      margin: 0 12px 10px 0;
      border: 0;
      background: transparent;
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      font-family: "Geist", ui-sans-serif, sans-serif;
    }

    #tagFilters {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .tag-filter {
      width: auto;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: var(--surface-high);
      padding: 6px 12px;
      gap: 10px;
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-size: 13px;
    }

    .tag-filter.active {
      background: var(--secondary-container, #f7dfc2);
      border-color: var(--accent);
      color: var(--accent);
    }

    .catalog-main {
      background: transparent;
    }

    .catalog-head {
      margin-bottom: 24px;
    }

    .catalog-title {
      font-size: 28px;
      line-height: 36px;
    }

    .catalog-search {
      max-width: 620px;
      margin-bottom: 18px;
    }

    .text-input,
    .small-textarea,
    .author-textarea,
    select,
    input[type="password"],
    input[type="number"] {
      border-radius: 4px;
      border-color: var(--line);
      background: var(--surface-lowest);
      color: var(--text);
    }

    .catalog-notice {
      background: var(--surface-low);
      border-color: var(--line);
      color: var(--muted);
      border-radius: 4px;
    }

    .problem-grid {
      gap: 0;
      border: 1px solid var(--line);
      border-radius: 4px;
      overflow: hidden;
      background: var(--surface-lowest);
    }

    .problem-card {
      border: 0;
      border-bottom: 1px solid var(--line-soft);
      border-radius: 0;
      padding: 14px 18px;
      background: var(--surface-lowest);
    }

    .problem-card:last-child {
      border-bottom: 0;
    }

    .problem-card:hover {
      background: var(--surface-high);
      border-color: var(--line-soft);
    }

    .problem-card-title {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 16px;
      margin-bottom: 8px;
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-weight: 600;
    }

    .problem-card-actions {
      opacity: 0.72;
    }

    .problem-card:hover .problem-card-actions {
      opacity: 1;
    }

    #manageView.view,
    #llmView.view {
      padding: 24px;
    }

    .manager-grid {
      gap: 24px;
    }

    .manager-header-card {
      border-radius: 4px;
      background: var(--surface-low);
    }

    .manager-three-grid {
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 24px;
      align-items: stretch;
    }

    .manager-three-grid > .runtime-card:first-child {
      grid-row: span 2;
    }

    .runtime-card.manager-pane,
    .runtime-card {
      background: var(--surface-lowest);
    }

    .manager-statement-editor,
    .manager-reference-editor,
    .author-textarea,
    .small-textarea,
    .author-output,
    .author-prompt,
    .runtime-output,
    .manager-output {
      font-family: "JetBrains Mono", ui-monospace, monospace;
      border-radius: 4px;
    }

    .manager-code-shell,
    .solution-code {
      border-radius: 4px;
      background: var(--surface-lowest);
      border-color: var(--line);
      color: var(--text);
    }

    .manager-code-toolbar {
      background: var(--surface-low);
      color: var(--muted);
      border-bottom-color: var(--line);
    }

    .author-grid {
      gap: 24px;
    }

    .llm-request-grid,
    .author-columns,
    .runtime-grid,
    .history-grid {
      gap: 16px;
    }

    @media (max-width: 900px) {
      .topbar { gap: 10px; padding: 0 14px; }
      .top-nav { gap: 12px; padding-left: 12px; }
      .top-nav button { font-size: 13px; }
      .practice-top-actions { display: none; }
      .layout { grid-template-columns: 1fr; height: auto; min-height: calc(100vh - 56px); }
      .problem-pane { min-height: 52vh; }
      .problem-inner { padding: 28px 20px 44px; }
      .manager-three-grid { grid-template-columns: 1fr; }
      .manager-three-grid > .runtime-card:first-child { grid-row: auto; }
      #catalogView.view { padding: 28px 16px; }
    }



    .material-symbols-outlined {
      font-family: "Material Symbols Outlined";
      font-weight: normal;
      font-style: normal;
      font-size: 18px;
      line-height: 1;
      letter-spacing: normal;
      text-transform: none;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      white-space: nowrap;
      word-wrap: normal;
      direction: ltr;
      -webkit-font-feature-settings: "liga";
      -webkit-font-smoothing: antialiased;
      font-variation-settings: "FILL" 0, "wght" 400, "GRAD" 0, "opsz" 24;
    }

    .brand::before { display: none; }

    .brand-icon {
      width: 32px;
      height: 32px;
      border-radius: 999px;
      background: var(--accent);
      color: #fff;
      font-size: 18px;
      font-variation-settings: "FILL" 1, "wght" 400, "GRAD" 0, "opsz" 24;
    }

    .practice-top-actions button,
    .console-tab,
    .practice-editor-toolbar .icon-button {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
    }

    .icon-button {
      width: 30px;
      height: 30px;
      padding: 0;
      border: 0;
      background: transparent;
      color: var(--muted);
    }

    .icon-button:hover {
      color: var(--accent);
      background: var(--surface-high);
    }

    .icon-button.danger:hover {
      color: var(--wrong);
      background: var(--error-container, #ffdad6);
    }

    .practice-editor-toolbar .icon-button {
      width: 28px;
      height: 28px;
      margin-left: 2px;
    }

    .console-tab .material-symbols-outlined {
      color: var(--accepted);
      font-size: 18px;
    }

    .problem-grid {
      display: block;
      margin-bottom: 14px;
    }

    .catalog-table {
      width: 100%;
      border-collapse: collapse;
      background: var(--surface-lowest);
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-size: 14px;
    }

    .catalog-table th {
      padding: 12px 16px;
      background: var(--surface-low);
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      font-family: "Geist", ui-sans-serif, sans-serif;
      font-size: 12px;
      border-bottom: 1px solid var(--line);
    }

    .catalog-table td {
      padding: 13px 16px;
      border-bottom: 1px solid var(--line-soft);
      vertical-align: middle;
    }

    .catalog-table tbody tr:last-child td {
      border-bottom: 0;
    }

    .problem-row:hover {
      background: var(--surface-high);
    }

    .catalog-id,
    .catalog-subtitle {
      color: var(--subtle);
      font-size: 12px;
    }

    .catalog-title-button {
      border: 0;
      background: transparent;
      padding: 0;
      color: var(--accent);
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-size: 14px;
      font-weight: 600;
      text-align: left;
    }

    .catalog-title-button:hover {
      background: transparent;
      text-decoration: underline;
    }

    .catalog-actions,
    .catalog-actions-head {
      text-align: right;
      white-space: nowrap;
    }

    .catalog-actions {
      opacity: 0.72;
    }

    .problem-row:hover .catalog-actions {
      opacity: 1;
    }



"""
