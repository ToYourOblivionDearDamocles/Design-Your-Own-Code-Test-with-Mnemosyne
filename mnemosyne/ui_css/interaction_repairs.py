from __future__ import annotations

"""Interaction Repairs CSS segment for the Mnemosyne UI.

Order matters: import through mnemosyne.ui_css.APP_CSS only.
"""

INTERACTION_REPAIRS_CSS = r"""    /* Interaction repair: no duplicate Practice title, real Manage edit/preview, horizontal case add. */
    [hidden] {
      display: none !important;
    }

    .practice-console-head .console-title-group {
      flex: 1;
      justify-content: flex-start;
    }

    .practice-console-head .console-tabs {
      gap: 18px;
    }

    .manager-mode-toggle button {
      min-height: 26px;
      padding: 3px 9px;
      border: 0;
      border-radius: 4px;
      background: transparent;
      color: var(--muted);
      font-size: 11px;
      line-height: 16px;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      box-shadow: none;
    }

    .manager-mode-toggle button.active {
      background: var(--surface-highest);
      border: 1px solid var(--line);
      color: var(--accent);
      font-weight: 700;
    }

    .manage-workspace:not(.manager-preview-mode) .manager-live-preview {
      display: none;
    }

    .manage-workspace:not(.manager-preview-mode) .manager-learning-pane {
      grid-template-rows: minmax(0, 1fr);
    }

    .manage-workspace:not(.manager-preview-mode) .manager-solution-pane {
      grid-template-rows: minmax(120px, 0.36fr) auto minmax(260px, 1fr);
    }

    .manage-workspace:not(.manager-preview-mode) .manager-solution-preview {
      display: none !important;
    }

    .manage-workspace:not(.manager-preview-mode) .solution-code-shell {
      display: flex !important;
      flex-direction: column;
      min-height: 260px;
    }

    .manage-workspace:not(.manager-preview-mode) .solution-code-shell .manager-reference-editor {
      display: block !important;
      flex: 1 1 auto;
      min-height: 220px;
      height: auto;
      caret-color: #1f1a16;
      color: var(--text);
    }

    .manage-workspace:not(.manager-preview-mode) .solution-code-shell .manager-reference-editor:focus {
      box-shadow: inset 3px 0 0 #1f1a16;
      outline: 1px solid rgba(49, 48, 45, 0.18);
      outline-offset: -1px;
    }

    .manage-workspace.manager-preview-mode .manager-learning-editor,
    .manage-workspace.manager-preview-mode .solution-code-shell {
      display: none;
    }

    .manage-workspace.manager-preview-mode .manager-learning-pane,
    .manage-workspace.manager-preview-mode .manager-solution-pane {
      grid-template-rows: minmax(0, 1fr);
    }

    .manage-workspace.manager-preview-mode .manager-live-preview {
      display: block;
      height: 100%;
    }

    .manager-case-tabs {
      overflow-x: auto;
      padding-right: 4px;
    }

    .manager-case-tabs .manager-add-case-tab {
      width: 30px;
      min-width: 30px;
      padding: 0;
      margin-left: 2px;
      color: var(--muted);
    }

    .manager-case-tabs .manager-add-case-tab .material-symbols-outlined {
      width: 16px;
      height: 16px;
      font-size: 16px;
    }

    .add-test-card {
      margin-top: 10px;
    }

    .add-test-card .compact-form-grid {
      display: grid;
      grid-template-columns: minmax(160px, 0.35fr) minmax(0, 1fr);
      align-items: start;
    }

    .add-test-card #managerFunctionTestBox,
    .add-test-card #managerCodeLabel,
    .add-test-card button {
      grid-column: 1 / -1;
    }

    .add-test-card button {
      justify-self: end;
      min-width: 112px;
    }


    /* Usability repair: scrollable panes and draggable splitters for learning workspaces. */
    .layout,
    .work-pane,
    #codeView,
    .practice-workspace,
    .create-workspace,
    .manage-workspace,
    .manage-split {
      min-height: 0;
    }

    .work-pane {
      overflow: hidden;
    }

    #codeView {
      height: 100%;
      padding: 0 !important;
      overflow: hidden !important;
    }

    .practice-workspace {
      height: 100%;
      min-height: 0;
      display: grid;
      grid-template-rows: 40px minmax(150px, 1fr) 7px minmax(140px, var(--practice-console-height, 34%)) !important;
      gap: 0 !important;
      overflow: hidden;
    }

    .practice-editor-card {
      min-height: 0;
      overflow: hidden;
      display: grid;
      grid-template-rows: auto minmax(0, 1fr) auto;
    }

    .practice-editor-shell,
    .practice-editor-shell .editor-body {
      min-height: 0;
      height: 100%;
      overflow: hidden;
    }

    .editor-body.cm-enabled .CodeMirror {
      height: 100%;
    }

    .practice-console-card {
      min-height: 0;
      overflow: hidden;
      display: grid;
      grid-template-rows: auto minmax(0, 1fr);
    }

    .practice-console-pane {
      min-height: 0;
      overflow: auto;
    }

    .practice-testcases,
    #practiceResultPane,
    #practiceErrorPane {
      min-height: 0;
      overflow: visible;
    }

    .vertical-splitter {
      min-height: 7px;
      height: 7px;
      background: var(--line-soft);
      border-top: 1px solid var(--line);
      border-bottom: 1px solid var(--line);
      cursor: row-resize;
      touch-action: none;
    }

    .vertical-splitter:hover,
    .vertical-splitter.dragging,
    .module-splitter:hover,
    .module-splitter.dragging {
      background: #d7dde6;
    }

    .module-splitter {
      width: 7px;
      min-width: 7px;
      background: var(--line-soft);
      border-left: 1px solid var(--line);
      border-right: 1px solid var(--line);
      cursor: col-resize;
      touch-action: none;
    }

    .create-workspace {
      grid-template-columns: minmax(320px, var(--create-left, 50%)) 7px minmax(320px, 1fr) !important;
      overflow: hidden;
    }

    .manage-split {
      grid-template-columns: minmax(320px, var(--manage-left, 50%)) 7px minmax(320px, 1fr) !important;
      overflow: hidden;
    }

    .create-chat-pane,
    .create-preview-pane,
    .manage-editor-pane,
    .manage-right-pane {
      min-height: 0;
      overflow: hidden;
    }

    .create-chat-scroll,
    .create-preview-scroll,
    .verifier-body,
    .manage-editor-canvas,
    .manage-right-pane {
      min-height: 0;
      overflow: auto;
    }

    .manager-learning-pane,
    .manager-live-preview,
    .manager-learning-editor,
    .manager-code-shell,
    .manager-reference-editor {
      min-height: 0;
    }

    @media (max-width: 1100px) {
      .create-workspace,
      .manage-split {
        grid-template-columns: 1fr !important;
      }

      .module-splitter {
        display: none;
      }
    }


    /* Manage inline tag editing and compact testcase JSON fields. */
    .manager-inline-tag-editor {
      display: flex;
      align-items: center;
      gap: 6px;
      flex: 1 1 260px;
      min-width: min(100%, 260px);
    }

    .manager-inline-tag-editor .text-input {
      flex: 1;
      min-width: 0;
      height: 28px;
      min-height: 28px;
      font-size: 12px;
      font-family: "JetBrains Mono", ui-monospace, monospace;
    }

    .tag-save-button {
      height: 28px;
      min-height: 28px;
      padding: 0 8px;
      border: 1px solid var(--line);
      background: var(--surface);
      color: var(--text);
      font-size: 10px;
      letter-spacing: 0.08em;
    }

    .tag-save-button .material-symbols-outlined {
      width: 15px;
      height: 15px;
      font-size: 15px;
    }

    .manager-case-card .small-textarea[wrap="off"],
    .manager-input-row textarea {
      min-height: 38px;
      white-space: pre;
      overflow-x: auto;
      resize: vertical;
    }

    .manager-case-card .small-textarea[wrap="off"] {
      line-height: 18px;
    }





    .manager-refresh-output-button {
      min-height: 26px;
      height: 26px;
      padding: 3px 8px;
      gap: 4px;
      font-size: 10px;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }

    .manager-refresh-output-button .material-symbols-outlined {
      width: 15px;
      height: 15px;
      font-size: 15px;
    }



    .leetcode-examples {
      margin-top: 22px;
    }

    .leetcode-example-card .test-name {
      color: var(--text);
      font-size: 14px;
      font-weight: 800;
    }

    .leetcode-io-grid .io-label {
      color: var(--text);
    }

    .small-textarea.stale-output,
    .manager-case-card .small-textarea.stale-output {
      border-color: #f59e0b;
      background: #fffbeb;
    }

    .manager-output-notice {
      margin: 0 12px 8px;
      border: 1px solid #fde68a;
      border-radius: 4px;
      background: #fffbeb;
      color: #78350f;
      padding: 7px 9px;
      font-size: 12px;
      line-height: 1.35;
    }

    /* Manage must expose the complete solution module: explanation, complexity, and code. */
    .manager-complexity-editor {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
      min-height: 0;
    }

    .manager-create-button.active {
      background: var(--ink);
      color: var(--surface-lowest);
      border-color: var(--ink);
    }

    .manager-complexity-editor label {
      display: grid;
      gap: 4px;
      color: var(--muted);
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }

    .manager-complexity-editor .text-input {
      height: 28px;
      min-height: 28px;
      padding: 4px 8px;
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-size: 12px;
      line-height: 18px;
      text-transform: none;
      letter-spacing: 0;
    }

    .manager-solution-preview {
      display: grid;
      gap: 10px;
      overflow: auto;
    }

    .manager-solution-preview .solution-code,
    #managerPreview .solution-code {
      margin: 0;
      max-height: none;
      white-space: pre;
      overflow: auto;
    }

    .manager-complexity-preview {
      border: 1px solid var(--line-soft);
      border-radius: 4px;
      background: var(--surface-lowest);
      padding: 8px;
    }

    .manage-workspace:not(.manager-preview-mode) .manager-complexity-editor {
      display: grid;
    }

    .manage-workspace.manager-preview-mode .manager-complexity-editor {
      display: none;
    }

    /* Final Practice result polish: result panes must scroll independently. */
    #practiceTestsPane,
    #practiceResultPane,
    #practiceErrorPane {
      min-height: 0 !important;
      height: 100% !important;
      max-height: 100% !important;
      overflow: auto !important;
      overscroll-behavior: contain;
    }

    #practiceResultPane,
    #practiceErrorPane {
      scrollbar-gutter: stable;
    }

    #practiceResultPane #result,
    #practiceErrorPane #practiceError {
      min-height: 0;
      padding-bottom: 36px;
    }

    #practiceResultPane .case-list,
    #practiceResultPane .runtime-detail-card,
    #practiceResultPane .raw-output-details,
    #practiceErrorPane .case-list,
    #practiceErrorPane .runtime-detail-card,
    #managerOutput .case-list,
    #managerOutput .runtime-detail-card {
      min-height: 0;
    }

    #practiceResultPane .case-card pre,
    #practiceResultPane .runtime-detail-card pre,
    #practiceResultPane .raw-output-details pre,
    #practiceErrorPane .case-card pre,
    #practiceErrorPane .runtime-detail-card pre,
    .manager-message-block {
      max-height: none;
      overflow: auto;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }

    /* Stable draggable dividers: quiet hover-only handles with wider hit areas. */
    body[data-mode="practice"] .layout,
    .practice-workspace,
    .create-workspace,
    .manage-split {
      --splitter-size: 10px;
      --splitter-track: transparent;
      --splitter-line: #31302d;
      --splitter-line-active: #31302d;
    }

    body[data-mode="practice"] .layout {
      grid-template-columns: minmax(360px, var(--main-left, 50%)) var(--splitter-size) minmax(460px, 1fr) !important;
    }

    .practice-workspace {
      grid-template-rows: 40px minmax(150px, 1fr) var(--splitter-size) minmax(140px, var(--practice-console-height, 34%)) !important;
    }

    .create-workspace {
      grid-template-columns: minmax(320px, var(--create-left, 50%)) var(--splitter-size) minmax(320px, 1fr) !important;
    }

    .manage-split {
      grid-template-columns: minmax(320px, var(--manage-left, 50%)) var(--splitter-size) minmax(320px, 1fr) !important;
    }

    .main-splitter,
    .module-splitter,
    .vertical-splitter {
      position: relative;
      border: 0 !important;
      touch-action: none;
      z-index: 8;
      flex: 0 0 var(--splitter-size);
      transition: background 120ms ease, box-shadow 120ms ease;
    }

    .main-splitter,
    .module-splitter {
      width: var(--splitter-size) !important;
      min-width: var(--splitter-size) !important;
      cursor: col-resize;
      background: linear-gradient(
        90deg,
        var(--splitter-track) 0 3px,
        var(--splitter-line) 3px 7px,
        var(--splitter-track) 7px 100%
      ) !important;
      box-shadow: inset 1px 0 0 var(--line-soft), inset -1px 0 0 var(--line-soft);
    }

    .vertical-splitter {
      height: var(--splitter-size) !important;
      min-height: var(--splitter-size) !important;
      cursor: row-resize;
      background: linear-gradient(
        180deg,
        var(--splitter-track) 0 3px,
        var(--splitter-line) 3px 7px,
        var(--splitter-track) 7px 100%
      ) !important;
      box-shadow: inset 0 1px 0 var(--line-soft), inset 0 -1px 0 var(--line-soft);
    }

    .main-splitter:hover,
    .main-splitter.dragging,
    .module-splitter:hover,
    .module-splitter.dragging {
      background: linear-gradient(
        90deg,
        transparent 0 2px,
        var(--splitter-line-active) 2px 8px,
        transparent 8px 100%
      ) !important;
    }

    .vertical-splitter:hover,
    .vertical-splitter.dragging {
      background: linear-gradient(
        180deg,
        transparent 0 2px,
        var(--splitter-line-active) 2px 8px,
        transparent 8px 100%
      ) !important;
    }

    .main-splitter.dragging,
    .module-splitter.dragging,
    .vertical-splitter.dragging {
      box-shadow: 0 0 0 2px rgba(168, 117, 36, 0.16);
    }

    @media (max-width: 1100px) {
      .create-workspace,
      .manage-split {
        grid-template-columns: 1fr !important;
      }

      .module-splitter {
        display: none;
      }
    }


    /* Color-only semantic pass aligned with stitch_reference.
       Feedback should guide, not punish: calm light states, dark serious errors, quiet notices. */
    :root {
      --accepted: #6d5c45;
      --wrong: #31302d;
      --feedback-ok-bg: #fcf9f4;
      --feedback-ok-border: #dac3a8;
      --feedback-ok-text: #6d5c45;
      --feedback-error-bg: #31302d;
      --feedback-error-border: #1d1d1d;
      --feedback-error-text: #f3f0eb;
      --feedback-error-soft-bg: #ebe8e3;
      --feedback-error-soft-border: #31302d;
      --feedback-error-soft-text: #31302d;
      --feedback-warning-bg: #f7dfc2;
      --feedback-warning-border: #dac3a8;
      --feedback-warning-text: #54442f;
      --feedback-info-bg: #f6f3ee;
      --feedback-info-border: #c4c7c7;
      --feedback-info-text: #444748;
    }

    .badge.ok,
    .dependency-row .badge.ok,
    #resultMeta.badge.ok,
    #syntaxBadge.badge.ok,
    #runtimeInstallStatus.badge.ok {
      border-color: var(--feedback-ok-border) !important;
      background: var(--feedback-ok-bg) !important;
      color: var(--feedback-ok-text) !important;
    }

    .badge.error,
    .dependency-row .badge.error,
    #resultMeta.badge.error,
    #syntaxBadge.badge.error,
    #runtimeInstallStatus.badge.error {
      border-color: var(--feedback-error-border) !important;
      background: var(--feedback-error-bg) !important;
      color: var(--feedback-error-text) !important;
    }

    .status-text.accepted,
    .editor-footer .diagnostic.ok,
    .diagnostic.ok,
    .case-tab.passed,
    .console-tab .material-symbols-outlined,
    .code-mark {
      color: var(--feedback-ok-text) !important;
    }

    .status-text.wrong,
    .editor-footer .diagnostic.error,
    .diagnostic.error,
    .case-tab.failed,
    .danger-text {
      color: var(--feedback-error-soft-text) !important;
    }

    .result-summary-card.accepted,
    .case-card.passed,
    .diagnostic.ok,
    .case-tab.passed {
      border-color: var(--feedback-ok-border) !important;
      background: var(--feedback-ok-bg) !important;
    }

    .result-summary-card.failed,
    .case-card.failed,
    .diagnostic.error,
    .validation-message.error {
      border-color: var(--feedback-error-soft-border) !important;
      background: var(--feedback-error-soft-bg) !important;
      color: var(--feedback-error-soft-text) !important;
    }

    .result-summary-card.failed .badge.error,
    .case-card.failed .badge.error,
    .validation-message.error .badge.error {
      background: var(--feedback-error-bg) !important;
      color: var(--feedback-error-text) !important;
      border-color: var(--feedback-error-border) !important;
    }

    .diagnostic pre,
    .case-card.failed pre,
    .validation-message.error pre {
      color: var(--feedback-error-soft-text) !important;
    }

    .case-card.passed .case-dot {
      background: var(--feedback-ok-border) !important;
    }

    .case-card.failed .case-dot {
      background: var(--feedback-error-bg) !important;
    }

    .validation-message.warning,
    .manager-output-notice,
    .small-textarea.stale-output,
    .manager-case-card .small-textarea.stale-output {
      border-color: var(--feedback-warning-border) !important;
      background: var(--feedback-warning-bg) !important;
      color: var(--feedback-warning-text) !important;
    }

    .catalog-notice,
    .validation-message {
      border-color: var(--feedback-info-border);
      background: var(--feedback-info-bg);
      color: var(--feedback-info-text);
    }

    .icon-button.danger:hover,
    button.danger:hover,
    .danger-text:hover {
      color: var(--feedback-error-text) !important;
      background: var(--feedback-error-bg) !important;
    }

    body[data-mode="practice"] .layout,
    .practice-workspace,
    .create-workspace,
    .manage-split {
      --splitter-size: 10px;
      --splitter-track: transparent;
      --splitter-line: #31302d;
      --splitter-line-active: #31302d;
    }

    .main-splitter,
    .module-splitter,
    .vertical-splitter {
      background: transparent !important;
      box-shadow: none !important;
    }

    .main-splitter:hover,
    .main-splitter.dragging,
    .module-splitter:hover,
    .module-splitter.dragging {
      background: linear-gradient(
        90deg,
        transparent 0 4px,
        var(--splitter-line-active) 4px 6px,
        transparent 6px 100%
      ) !important;
      box-shadow: inset 0 0 0 1px rgba(49, 48, 45, 0.05) !important;
    }

    .vertical-splitter:hover,
    .vertical-splitter.dragging {
      background: linear-gradient(
        180deg,
        transparent 0 4px,
        var(--splitter-line-active) 4px 6px,
        transparent 6px 100%
      ) !important;
      box-shadow: inset 0 0 0 1px rgba(49, 48, 45, 0.05) !important;
    }


    /* Create Direct JSON fixed-loop workflow. */
    .stitch-create-view[data-create-mode="direct"] .create-model-bar {
      display: none;
    }

    .stitch-create-view[data-create-mode="direct"] .llm-provider-hint {
      display: none;
    }

    .direct-json-instruction-bubble {
      max-width: 92%;
      border-left-color: var(--feedback-warning-border);
    }


    .stitch-create-view .bubble-kicker {
      justify-content: space-between;
      align-items: center;
      gap: 12px;
    }

    .stitch-create-view .bubble-title,
    .stitch-create-view .copy-chip {
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }

    .stitch-create-view .copy-chip {
      min-height: 24px;
      padding: 2px 8px;
      border: 1px solid var(--line);
      border-radius: 5px;
      background: var(--surface-lowest);
      color: var(--muted);
      font-size: 10px;
      font-family: "JetBrains Mono", ui-monospace, monospace;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }

    .stitch-create-view .copy-chip:hover,
    .stitch-create-view .copy-chip.copied {
      background: var(--surface-highest);
      color: var(--accent);
      border-color: var(--accent-soft);
    }

    .stitch-create-view .copy-chip .material-symbols-outlined {
      font-size: 15px;
    }

    .stitch-create-view .chat-output.prompt-preview {
      max-height: 220px;
      overflow: hidden;
    }

    .stitch-create-view .new-chat-button,
    .stitch-create-view .direct-json-button {
      min-height: 30px;
      padding: 4px 9px;
      border-radius: 6px;
      font-size: 11px;
      line-height: 1.1;
      font-family: "JetBrains Mono", ui-monospace, monospace;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }

    .stitch-create-view .new-chat-button {
      background: var(--surface-lowest);
      color: var(--feedback-info-text);
      border-color: var(--feedback-info-border);
    }

    .stitch-create-view .new-chat-button:hover {
      background: var(--feedback-info-bg);
      color: var(--accent);
    }

    .stitch-create-view .direct-json-button {
      background: var(--surface-lowest);
      color: var(--feedback-warning-text);
      border-color: var(--feedback-warning-border);
    }

    .stitch-create-view .direct-json-button:hover {
      background: var(--feedback-warning-bg);
      color: var(--accent);
    }

    .stitch-create-view .direct-json-button.active {
      background: var(--accent);
      border-color: var(--accent);
      color: var(--surface-lowest);
    }

    .create-problem-heading {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 16px;
      padding-bottom: 14px;
      margin-bottom: 16px;
      border-bottom: 1px solid var(--line);
    }

    .create-problem-heading .problem-title {
      margin: 0 0 10px;
      font-size: clamp(24px, 3vw, 34px);
      line-height: 1.12;
    }

    .create-problem-preview + .create-problem-preview {
      margin-top: 30px;
      padding-top: 24px;
      border-top: 1px solid var(--line);
    }

    .create-verifier-panel .verifier-body {
      min-height: 88px;
    }


    .stitch-create-view .direct-submission-row button {
      width: auto !important;
      min-width: 0 !important;
      height: 30px !important;
      min-height: 30px !important;
      padding: 4px 9px !important;
    }

    .stitch-create-view .direct-submission-row button span:not(.material-symbols-outlined) {
      display: inline !important;
    }

    .stitch-create-view .create-verifier-panel {
      flex: 0 0 42px !important;
      min-height: 42px !important;
      max-height: 42px !important;
    }

    .stitch-create-view[data-verifier-open="true"] .create-verifier-panel {
      flex: 0 0 clamp(230px, 36%, 420px) !important;
      min-height: 230px !important;
      max-height: 44% !important;
    }


    /* Create verifier: visible, Manage-like, and vertically resizable. */
    .stitch-create-view .create-preview-pane {
      --create-verifier-height: 260px;
    }

    .stitch-create-view .create-verifier-splitter {
      flex: 0 0 var(--splitter-size, 10px) !important;
      height: var(--splitter-size, 10px) !important;
      min-height: var(--splitter-size, 10px) !important;
      background: transparent !important;
      border: 0 !important;
      cursor: row-resize;
      touch-action: none;
    }

    .stitch-create-view .create-verifier-splitter:hover,
    .stitch-create-view .create-verifier-splitter.dragging {
      background: linear-gradient(
        180deg,
        transparent 0 4px,
        var(--splitter-line-active) 4px 6px,
        transparent 6px 100%
      ) !important;
    }

    .stitch-create-view .create-verifier-panel,
    .stitch-create-view[data-verifier-open="true"] .create-verifier-panel {
      flex: 0 0 var(--create-verifier-height) !important;
      min-height: 150px !important;
      max-height: 52% !important;
      border-top: 1px solid var(--line) !important;
      background: var(--surface) !important;
      overflow: hidden !important;
    }

    .stitch-create-view[data-result-view="preview"] .verifier-body {
      display: none !important;
    }

    .stitch-create-view .create-verifier-panel .verifier-body {
      min-height: 0;
      overflow: auto;
    }

    /* Create verifier console: fixed like Practice's lower console, scrollable like Manage's verifier. */
    .stitch-create-view .create-verifier-panel,
    .stitch-create-view[data-verifier-open="true"] .create-verifier-panel {
      display: flex !important;
      flex-direction: column !important;
      flex: 0 0 var(--create-verifier-height) !important;
      min-height: 170px !important;
      max-height: 56% !important;
      overflow: hidden !important;
    }

    .stitch-create-view .create-verifier-panel .verifier-head {
      flex: 0 0 auto !important;
    }

    .stitch-create-view .create-verifier-panel .verifier-body {
      flex: 1 1 auto !important;
      min-height: 0 !important;
      max-height: none !important;
      overflow: auto !important;
    }

    .stitch-create-view .create-verifier-panel .verifier-body[hidden] {
      display: none !important;
    }

    .stitch-create-view[data-result-view="report"] .create-verifier-panel .verifier-body:not([hidden]),
    .stitch-create-view[data-result-view="json"] .create-verifier-panel .verifier-body:not([hidden]) {
      display: block !important;
    }

    .stitch-create-view .create-chat-message .chat-output {
      max-width: 100%;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }

    .stitch-create-view .create-chat-message.user-bubble {
      border-left: 1px solid var(--line);
      border-right: 2px solid var(--accent-soft);
    }


    /* Create verifier final layout: a real lower console with its own scroll. */
    .stitch-create-view .create-preview-pane {
      --create-verifier-height: 280px;
      display: grid !important;
      grid-template-rows: auto auto minmax(80px, 1fr) var(--splitter-size, 10px) var(--create-verifier-height) !important;
      min-height: 0 !important;
      overflow: hidden !important;
    }

    .stitch-create-view .create-preview-scroll {
      min-height: 0 !important;
      height: auto !important;
      overflow: auto !important;
    }

    .stitch-create-view .create-verifier-panel,
    .stitch-create-view[data-verifier-open="true"] .create-verifier-panel {
      height: 100% !important;
      min-height: 0 !important;
      max-height: none !important;
      flex: none !important;
      display: grid !important;
      grid-template-rows: auto minmax(0, 1fr) !important;
      overflow: hidden !important;
      border-top: 1px solid var(--line) !important;
    }

    .stitch-create-view .create-verifier-panel .verifier-head {
      min-height: 34px !important;
      overflow: hidden;
    }

    .stitch-create-view .create-verifier-panel .verifier-body {
      display: block !important;
      min-height: 0 !important;
      height: auto !important;
      max-height: none !important;
      overflow: auto !important;
      padding: 12px !important;
      background: var(--surface) !important;
    }

    .stitch-create-view .create-verifier-panel .verifier-output,
    .manager-verifier-card .manager-output {
      display: block !important;
      width: 100% !important;
      max-height: none !important;
      overflow: auto !important;
      border: 1px solid var(--line) !important;
      border-radius: 6px !important;
      background: #fff !important;
      color: var(--text) !important;
      padding: 10px 12px !important;
      font-family: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace !important;
      font-size: 12px !important;
      line-height: 1.5 !important;
      white-space: pre-wrap !important;
      overflow-wrap: anywhere !important;
    }

    .stitch-create-view .create-verifier-panel .verifier-output {
      height: 100% !important;
      min-height: 0 !important;
    }

    .manager-verifier-card {
      flex: 0 0 auto !important;
    }

    .manager-verifier-card .manager-output {
      margin: 0 12px 12px !important;
      max-height: 220px !important;
      min-height: 96px !important;
    }

    .stitch-create-view #llmResultJsonPane[hidden] {
      display: none !important;
    }

"""
