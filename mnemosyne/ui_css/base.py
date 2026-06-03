from __future__ import annotations

"""Base CSS segment for the Mnemosyne UI.

Order matters: import through mnemosyne.ui_css.APP_CSS only.
"""

BASE_CSS = r"""    :root {
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
    body[data-mode="problems"] .main-splitter,
    body[data-mode="manage"] .main-splitter,
    body[data-mode="create"] .main-splitter,
    body[data-mode="llm"] .main-splitter,
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
      grid-template-columns: minmax(320px, var(--main-left, 44%)) 7px minmax(420px, 1fr);
      height: calc(100vh - 54px);
    }

    .main-splitter {
      background: var(--line-soft);
      border-left: 1px solid var(--line);
      border-right: 1px solid var(--line);
      cursor: col-resize;
      min-width: 7px;
      touch-action: none;
    }

    .main-splitter:hover,
    .main-splitter.dragging {
      background: #dbe4f0;
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


    .learning-tabs {
      display: flex;
      align-items: center;
      gap: 6px;
      overflow-x: auto;
      padding: 6px;
      margin: 0 0 20px;
      border: 1px solid var(--line-soft);
      border-radius: 10px;
      background: #f8fafc;
    }

    .learning-tab {
      flex: 0 0 auto;
      border: 0;
      border-radius: 8px;
      padding: 8px 10px;
      background: transparent;
      color: var(--muted);
      font-size: 13px;
      font-weight: 760;
    }

    .learning-tab.active {
      background: #ffffff;
      color: var(--text);
      box-shadow: 0 0 0 1px var(--line);
    }

    .learning-pane[hidden] {
      display: none;
    }

    .learning-empty {
      border: 1px dashed var(--line);
      border-radius: 10px;
      padding: 14px;
      color: var(--muted);
      background: #fbfcfe;
    }

    .learning-section-kicker {
      margin: 0 0 8px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 800;
      letter-spacing: .04em;
      text-transform: uppercase;
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


    .math-fallback sup,
    .math-fallback sub {
      font-size: 0.72em;
      line-height: 0;
    }

    .math-frac {
      display: inline-grid;
      grid-template-rows: auto auto;
      align-items: center;
      text-align: center;
      vertical-align: middle;
      margin: 0 2px;
      font-size: 0.9em;
    }

    .math-frac span:first-child {
      border-bottom: 1px solid currentColor;
      padding: 0 2px 1px;
    }

    .math-frac span:last-child {
      padding: 1px 2px 0;
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

      .main-splitter {
        display: none;
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


"""
