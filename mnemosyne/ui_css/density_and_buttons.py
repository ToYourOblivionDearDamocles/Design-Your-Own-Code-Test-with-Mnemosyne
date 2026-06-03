from __future__ import annotations

"""Density And Buttons CSS segment for the Mnemosyne UI.

Order matters: import through mnemosyne.ui_css.APP_CSS only.
"""

DENSITY_AND_BUTTONS_CSS = r"""    /* Stitch density pass: tighten buttons, fonts, and toolbar icon rhythm. */
    body {
      font-size: 14px;
    }

    button,
    .small,
    .icon-label-button,
    .runtime-actions button,
    .console-actions button,
    .create-send-row button,
    .direct-submission-row button {
      min-height: 30px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      padding: 4px 10px;
      border-radius: 4px;
      font-family: "Geist", ui-sans-serif, sans-serif;
      font-size: 12px;
      line-height: 18px;
      font-weight: 600;
      letter-spacing: 0;
      white-space: nowrap;
    }

    .small,
    button.small {
      min-height: 28px;
      padding: 3px 8px;
      font-size: 12px;
    }

    .material-symbols-outlined,
    button .material-symbols-outlined,
    .small .material-symbols-outlined {
      width: 17px;
      height: 17px;
      font-size: 17px;
      line-height: 1;
      flex: 0 0 auto;
    }

    .icon-button,
    button.icon-button {
      width: 28px;
      height: 28px;
      min-height: 28px;
      padding: 0;
      border-radius: 4px;
    }

    .topbar {
      height: 56px;
      padding: 0 24px;
      gap: 22px;
    }

    .brand {
      font-size: 18px;
      line-height: 24px;
    }

    .brand-icon {
      width: 30px;
      height: 30px;
      font-size: 17px;
    }

    .top-nav {
      gap: 20px;
      padding-left: 22px;
    }

    .top-nav button {
      min-height: 56px;
      padding: 16px 0 13px;
      font-size: 14px;
      line-height: 20px;
      font-weight: 500;
    }

    .top-nav button.active {
      font-weight: 650;
    }

    .practice-top-actions {
      gap: 8px;
    }

    .practice-top-actions button {
      min-height: 30px;
      padding: 4px 14px;
      font-size: 12px;
      line-height: 18px;
      letter-spacing: 0.04em;
    }

    #syntaxBadge,
    .badge {
      min-height: 22px;
      padding: 2px 7px;
      border-radius: 4px;
      font-size: 11px;
      line-height: 16px;
    }

    select,
    .text-input,
    .number-input,
    input[type="password"],
    input[type="number"] {
      min-height: 30px;
      padding: 5px 8px;
      border-radius: 4px;
      font-size: 12px;
      line-height: 18px;
    }

    .learning-tabs {
      padding: 8px 12px;
    }

    .learning-tab,
    .create-preview-tabs button,
    .manager-learning-tabs button,
    .manager-tool-tabs button,
    .manager-mode-toggle span {
      min-height: 28px;
      padding: 4px 10px;
      font-size: 12px;
      line-height: 18px;
    }

    .problem-inner {
      padding: 34px 44px 56px;
    }

    .problem-title {
      font-size: 28px;
      line-height: 36px;
      margin-bottom: 14px;
    }

    .statement {
      font-size: 15px;
      line-height: 1.6;
    }

    .statement h1 { font-size: 25px; line-height: 34px; }
    .statement h2 { font-size: 21px; line-height: 30px; }
    .statement h3 { font-size: 17px; line-height: 26px; }

    .tag {
      min-height: 22px;
      padding: 2px 7px;
      border-radius: 4px;
      font-size: 11px;
      line-height: 16px;
    }

    .work-tabs {
      min-height: 42px;
      padding: 0 12px;
    }

    button.tab {
      min-height: 42px;
      padding: 10px 10px 8px;
      font-size: 13px;
      line-height: 18px;
    }

    .practice-editor-toolbar,
    .practice-console-head,
    .panel-head,
    .create-model-bar,
    .create-preview-header,
    .manage-editor-header {
      min-height: 40px;
      padding: 6px 12px;
      gap: 10px;
    }

    .practice-editor-title {
      font-size: 15px;
      line-height: 22px;
    }

    .editor-meta,
    .cursor-status,
    .status-line,
    .verifier-head,
    .create-model-title {
      font-size: 11px;
      line-height: 16px;
    }

    .console-title-group {
      gap: 14px;
    }

    .console-tab {
      min-height: 30px;
      padding: 5px 0;
      font-size: 14px;
      line-height: 20px;
    }

    .console-actions {
      gap: 6px;
      margin-left: auto;
    }

    .console-actions button {
      min-width: 74px;
    }

    .case-tab {
      min-height: 34px;
      padding: 7px 14px;
      font-size: 14px;
    }

    .console-field-label,
    .test-name,
    .io-label,
    .manager-test-section-title,
    .catalog-sidebar-head {
      font-size: 11px;
      line-height: 16px;
    }

    .console-field-value,
    pre,
    .small-textarea,
    .author-textarea,
    .manager-learning-editor,
    .manager-reference-editor,
    .CodeMirror {
      font-size: 13px;
      line-height: 20px;
    }

    .catalog-title {
      font-size: 24px;
      line-height: 32px;
    }

    .catalog-search-row {
      gap: 10px;
      margin-bottom: 16px;
    }

    .catalog-search {
      width: min(100%, 430px);
      min-height: 34px;
      padding: 5px 10px;
    }

    .catalog-table {
      font-size: 13px;
    }

    .catalog-table th {
      padding: 10px 14px;
      font-size: 11px;
    }

    .catalog-table td {
      padding: 10px 14px;
    }

    .create-model-bar {
      min-height: 40px;
      padding: 5px 12px;
    }

    .create-model-controls {
      gap: 8px;
      align-items: center;
    }

    .compact-label {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 10px;
      line-height: 14px;
      white-space: nowrap;
    }

    .compact-label select,
    .compact-label input {
      height: 28px;
      min-height: 28px;
      font-size: 12px;
    }

    .model-field { width: min(210px, 24vw); }
    .key-field { width: min(145px, 17vw); }

    .chat-bubble {
      padding: 12px;
      max-width: 86%;
    }

    .chat-kicker,
    .direct-submission-row,
    .dependency-title,
    .dependency-subtitle,
    .llm-provider-hint,
    .empty {
      font-size: 12px;
      line-height: 18px;
    }

    .create-composer {
      padding: 12px;
      gap: 8px;
    }

    .chat-request {
      min-height: 78px;
      padding: 10px;
      font-size: 14px;
      line-height: 20px;
    }

    .create-preview-scroll {
      padding: 18px 22px;
    }

    .create-verifier-panel {
      min-height: 190px;
    }

    .verifier-head {
      min-height: 32px;
      padding: 5px 10px;
    }





    .manager-editor-canvas,
    .manage-right-pane {
      padding: 12px;
    }

    .manager-learning-pane {
      grid-template-rows: minmax(240px, 1fr) minmax(150px, 32%);
      gap: 12px;
    }

    .runtime-actions {
      gap: 6px;
    }

    .runtime-actions button,
    .panel-head button,
    .dependency-actions button {
      display: inline-flex;
      align-items: center;
      gap: 5px;
    }

    .author-columns {
      grid-template-columns: minmax(0, 1.05fr) minmax(280px, 0.85fr) minmax(240px, 0.65fr);
    }

    @media (max-width: 900px) {
      .top-nav button { min-height: 40px; padding: 8px 0; }
    }


    /* Stitch correction pass: Create header and Practice actions. */
    body[data-mode="practice"] #syntaxBadge {
      display: none;
    }

    body[data-mode="practice"] .practice-top-actions {
      margin-left: auto;
      gap: 6px;
    }

    body[data-mode="practice"] .practice-top-actions button {
      min-width: 30px;
      min-height: 28px;
      height: 28px;
      padding: 0 9px;
      border-radius: 4px;
      font-size: 11px;
      line-height: 16px;
      letter-spacing: 0.04em;
    }

    body[data-mode="practice"] .practice-top-actions button .material-symbols-outlined {
      width: 15px;
      height: 15px;
      font-size: 15px;
    }

    .practice-console-head {
      min-height: 38px;
      padding: 5px 10px;
    }

    .console-actions {
      margin-left: auto;
      gap: 5px;
    }

    .console-actions button {
      width: 29px;
      min-width: 29px;
      height: 29px;
      min-height: 29px;
      padding: 0;
    }

    .console-actions button span:not(.material-symbols-outlined) {
      display: none;
    }

    .console-actions .status-line {
      margin-left: 4px;
      font-size: 11px;
    }

    .stitch-create-view .create-model-bar {
      min-height: 40px;
      height: 40px;
      padding: 4px 10px;
      gap: 8px;
      justify-content: space-between;
      overflow: hidden;
    }

    .stitch-create-view .create-model-title {
      min-width: 0;
      flex: 1 1 auto;
      gap: 7px;
      overflow: hidden;
    }

    .stitch-create-view .create-model-title > .material-symbols-outlined {
      width: 18px;
      height: 18px;
      font-size: 18px;
    }

    .stitch-create-view .create-model-title select {
      width: min(100%, 290px);
      min-width: 160px;
      height: 30px;
      min-height: 30px;
      padding: 3px 26px 3px 8px;
      border: 1px solid var(--line);
      border-radius: 4px;
      background: var(--surface-lowest);
      color: var(--text);
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-size: 12px;
      line-height: 18px;
    }

    .stitch-create-view .create-model-controls {
      flex: 0 1 auto;
      gap: 6px;
      align-items: center;
      justify-content: flex-end;
      min-width: 0;
    }

    .icon-field {
      height: 30px;
      min-width: 0;
      display: inline-flex;
      align-items: center;
      gap: 5px;
      padding: 0 7px;
      border: 1px solid var(--line);
      border-radius: 4px;
      background: var(--surface-lowest);
      color: var(--subtle);
    }

    .icon-field .material-symbols-outlined {
      width: 15px;
      height: 15px;
      font-size: 15px;
    }

    .icon-field input {
      min-height: 0;
      height: 24px;
      padding: 0;
      border: 0;
      background: transparent;
      box-shadow: none;
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-size: 12px;
      line-height: 18px;
    }

    .icon-field input:focus {
      outline: none;
      box-shadow: none;
    }

    .stitch-create-view .model-field {
      width: 150px;
    }

    .stitch-create-view .key-field {
      width: 116px;
    }

    .stitch-create-view .icon-button {
      width: 28px;
      height: 28px;
      min-height: 28px;
    }

    .stitch-create-view #llmStatus {
      max-width: 116px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-family: "JetBrains Mono", ui-monospace, monospace;
    }

    .stitch-create-view .create-chat-scroll {
      padding: 14px 16px;
      gap: 12px;
    }

    .stitch-create-view .chat-divider {
      font-size: 10px;
      line-height: 14px;
      letter-spacing: 0.05em;
    }

    .stitch-create-view .chat-bubble {
      max-width: 92%;
      padding: 10px 12px;
      border-radius: 6px;
    }

    .stitch-create-view .compact-agent-bubble {
      min-width: min(360px, 92%);
    }

    .stitch-create-view .chat-kicker {
      margin-bottom: 6px;
      font-size: 11px;
      line-height: 16px;
    }

    .stitch-create-view .create-composer {
      padding: 10px;
      gap: 7px;
    }

    .stitch-create-view .direct-submission-row {
      min-height: 30px;
      padding: 4px 7px;
      font-size: 10px;
      line-height: 14px;
      letter-spacing: 0.05em;
    }

    .stitch-create-view .direct-submission-row button {
      width: 28px;
      min-width: 28px;
      height: 26px;
      min-height: 26px;
      padding: 0;
    }

    .stitch-create-view .direct-submission-row button span:not(.material-symbols-outlined) {
      display: none;
    }

    .stitch-create-view .chat-request {
      min-height: 72px;
      padding: 9px 10px;
      border-radius: 6px;
      font-size: 13px;
      line-height: 19px;
    }

    .stitch-create-view .create-attachment-row {
      gap: 6px;
    }

    .stitch-create-view .llm-attachment-picker .empty {
      display: none;
    }

    .stitch-create-view .create-attachment-row button {
      width: 28px;
      min-width: 28px;
      height: 28px;
      min-height: 28px;
      padding: 0;
    }

    .stitch-create-view .create-attachment-row button span:not(.material-symbols-outlined) {
      display: none;
    }

    .stitch-create-view .create-send-row {
      justify-content: flex-end;
      gap: 6px;
    }

    .stitch-create-view .create-send-row .compact-label {
      margin-right: auto;
    }

    .stitch-create-view .create-send-row button {
      min-height: 28px;
      height: 28px;
      padding: 0 9px;
      font-size: 11px;
    }

    @media (max-width: 1100px) {
      .stitch-create-view .create-model-title select {
        width: min(100%, 230px);
      }
      .stitch-create-view .model-field {
        width: 120px;
      }
      .stitch-create-view .key-field {
        width: 92px;
      }
      .stitch-create-view #llmStatus {
        max-width: 92px;
      }
    }


    /* Stitch final button normalization */
    button {
      min-height: 28px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      padding: 4px 10px;
      border: 1px solid var(--line);
      border-radius: 4px;
      background: var(--surface);
      color: var(--text);
      box-shadow: none;
      font-family: "Geist", ui-sans-serif, sans-serif;
      font-size: 11px;
      line-height: 16px;
      font-weight: 600;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      white-space: nowrap;
    }

    button:hover {
      background: var(--surface-high);
      border-color: var(--subtle);
    }

    button.primary {
      background: var(--accent);
      border-color: var(--accent);
      color: #fff;
    }

    button.small,
    .small {
      min-height: 26px;
      padding: 3px 8px;
      font-size: 10px;
      line-height: 14px;
      letter-spacing: 0.06em;
    }

    button .material-symbols-outlined,
    .small .material-symbols-outlined {
      width: 16px;
      height: 16px;
      font-size: 16px;
      line-height: 1;
      flex: 0 0 auto;
    }

    .icon-button,
    button.icon-button,
    .catalog-actions .icon-button,
    .practice-editor-toolbar .icon-button,
    .stitch-create-view .icon-button {
      width: 28px;
      min-width: 28px;
      height: 28px;
      min-height: 28px;
      padding: 0;
      border: 0;
      border-radius: 4px;
      background: transparent;
      color: var(--muted);
    }

    .icon-button:hover,
    button.icon-button:hover,
    .catalog-actions .icon-button:hover {
      background: var(--surface-high);
      color: var(--accent);
      border-color: transparent;
    }

    .icon-button.danger:hover,
    button.danger:hover,
    .danger-text:hover {
      color: var(--wrong);
      background: var(--error-container, #ffdad6);
    }

    .top-nav {
      gap: 24px;
    }

    .top-nav button {
      min-height: 56px;
      padding: 16px 0 13px;
      border: 0;
      border-bottom: 2px solid transparent;
      border-radius: 0;
      background: transparent;
      color: var(--muted);
      font-size: 14px;
      line-height: 20px;
      font-weight: 500;
      letter-spacing: 0;
      text-transform: none;
    }

    .top-nav button:hover {
      background: transparent;
      color: var(--text);
      border-bottom-color: var(--line);
    }

    .top-nav button.active {
      background: transparent;
      color: var(--accent);
      border-bottom-color: var(--accent);
      font-weight: 700;
    }

    .learning-tab,
    .create-preview-tabs button,
    .manager-learning-tabs button,
    .manager-tool-tabs button,
    button.tab {
      min-height: 28px;
      padding: 4px 10px;
      border-radius: 4px;
      font-size: 12px;
      line-height: 18px;
      letter-spacing: 0.02em;
      text-transform: none;
      background: transparent;
      color: var(--muted);
    }

    .learning-tab.active,
    .create-preview-tabs button.active,
    .manager-learning-tabs button.active,
    .manager-tool-tabs button.active {
      background: var(--surface-highest);
      border-color: var(--line);
      color: var(--accent);
      font-weight: 700;
    }

    button.tab {
      min-height: 40px;
      border: 0;
      border-bottom: 2px solid transparent;
      border-radius: 0;
      background: transparent;
    }

    button.tab.active {
      border-bottom-color: var(--accent);
      background: transparent;
      color: var(--accent);
    }

    body[data-mode="practice"] .practice-top-actions {
      margin-left: auto;
      gap: 6px;
    }

    body[data-mode="practice"] .practice-top-actions button,
    .console-actions button {
      height: 28px;
      min-height: 28px;
      padding: 0 9px;
      border-radius: 4px;
      font-size: 10px;
      line-height: 14px;
      letter-spacing: 0.08em;
    }

    .console-actions button {
      width: auto;
      min-width: 28px;
    }

    .console-actions button span:not(.material-symbols-outlined) {
      display: inline;
    }

    .console-tab {
      min-height: 30px;
      padding: 5px 0;
      border: 0;
      border-bottom: 2px solid transparent;
      border-radius: 0;
      background: transparent;
      color: var(--muted);
      font-size: 13px;
      letter-spacing: 0;
      text-transform: none;
    }

    .console-tab:hover {
      background: transparent;
      color: var(--text);
      border-bottom-color: var(--line);
    }

    .console-tab.active {
      background: transparent;
      border-bottom-color: var(--secondary);
      color: var(--text);
    }

    .case-tab {
      min-height: 32px;
      padding: 6px 12px;
      border: 0;
      border-radius: 4px;
      background: var(--surface);
      color: var(--muted);
      font-size: 13px;
      letter-spacing: 0;
      text-transform: none;
    }

    button.tag,
    .tag-filter {
      min-height: 22px;
      padding: 2px 8px;
      border-radius: 4px;
      background: var(--surface-low);
      color: var(--muted);
      font-size: 11px;
      line-height: 16px;
      letter-spacing: 0;
      text-transform: none;
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-weight: 500;
    }

    .catalog-title-button {
      min-height: auto;
      padding: 0;
      border: 0;
      border-radius: 0;
      background: transparent;
      color: var(--accent);
      font-size: 13px;
      letter-spacing: 0;
      text-transform: none;
      justify-content: flex-start;
    }

    .catalog-title-button:hover {
      background: transparent;
      border: 0;
      text-decoration: underline;
    }

    .icon-label-button,
    .runtime-actions button,
    .panel-head button,
    .dependency-actions button,
    .direct-submission-row button,
    .create-send-row button,
    .create-attachment-row button {
      min-height: 26px;
      padding: 3px 8px;
      font-size: 10px;
      line-height: 14px;
      letter-spacing: 0.08em;
    }



    .stitch-create-view .direct-submission-row button,
    .stitch-create-view .create-attachment-row button {
      width: 28px;
      min-width: 28px;
      padding: 0;
    }

    .stitch-create-view .create-send-row button {
      height: 28px;
      min-height: 28px;
      padding: 0 9px;
      font-size: 10px;
    }

    .stitch-create-view .create-preview-header .runtime-actions button {
      height: 28px;
      min-height: 28px;
      padding: 0 8px;
      font-size: 10px;
    }



    /* Strict Stitch content pruning */
    .work-tabs,
    #catalogCount,
    #dependencyStatus,
    .advanced-pane,
    .llm-result-tabs,
    .preview-status-line,
    .create-deps-bar {
      display: none !important;
    }

    .practice-workspace {
      grid-template-rows: 40px minmax(0, 1fr) minmax(220px, 34%) !important;
    }

    .practice-action-bar {
      min-height: 40px;
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 6px;
      padding: 5px 12px;
      border-bottom: 1px solid var(--line);
      background: var(--surface-low);
    }

    .practice-action-bar button {
      height: 28px;
      min-height: 28px;
      padding: 0 10px;
      border-radius: 4px;
      font-size: 10px;
      line-height: 14px;
      letter-spacing: 0.08em;
    }

    .brand {
      flex-direction: row;
    }

    .create-model-controls .badge[hidden],
    .create-preview-header .badge[hidden],
    .create-preview-scroll .badge[hidden] .badge[hidden] {
      display: none !important;
    }

    .direct-submission-row {
      justify-content: flex-start;
      gap: 8px;
      border: 0;
      background: transparent;
      padding: 0;
    }

    .direct-submission-row button {
      width: auto !important;
      min-width: 0 !important;
      padding: 3px 8px !important;
    }

    .stitch-create-view .create-preview-header .runtime-actions {
      margin-left: auto;
    }

    .stitch-create-view .create-preview-header .runtime-actions button {
      width: auto;
    }

    .catalog-actions .icon-button:nth-child(n+4) {
      display: none !important;
    }





    .hidden-file-input {
      position: absolute;
      width: 1px;
      height: 1px;
      opacity: 0;
      pointer-events: none;
    }

    .stitch-composer-actions {
      justify-content: space-between;
      align-items: center;
    }

    .stitch-composer-actions label.icon-button {
      display: inline-flex;
      cursor: pointer;
    }



    /* Strict Stitch Manage convergence: right rail order = actions, tags, tests, verifier. */
    .manage-workspace {
      display: block;
      height: 100%;
      min-height: 0;
      background: var(--surface-highest);
    }

    .stitch-manage-view .manage-split {
      height: 100%;
      grid-template-columns: minmax(420px, 1fr) minmax(420px, 1fr);
    }

    .stitch-manage-view .manage-editor-pane {
      background: var(--surface-low);
    }

    .stitch-manage-view .manage-right-pane {
      padding: 0;
      gap: 0;
      overflow: auto;
      background: var(--surface-low);
    }

    .manage-right-header {
      min-height: 40px;
      padding: 5px 12px;
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 6px;
      border-bottom: 1px solid var(--line);
      background: var(--surface-low);
      position: sticky;
      top: 0;
      z-index: 5;
    }

    .manage-right-header #managerStatus {
      margin-right: auto;
    }

    .manage-right-header button {
      height: 28px;
      min-height: 28px;
      padding: 0 9px;
      font-size: 10px;
      letter-spacing: 0.08em;
    }

    .manager-side-section {
      flex: 0 0 auto;
      padding: 12px;
      border-bottom: 1px solid var(--line);
      background: var(--surface-low);
    }

    .manager-section-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 10px;
    }

    .manager-section-title {
      margin: 0;
      color: var(--muted);
      font-family: "Geist", ui-sans-serif, sans-serif;
      font-size: 11px;
      line-height: 16px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    .manager-tags-row {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
    }

    .manager-tag-strip {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 6px;
    }

    .empty-inline {
      color: var(--subtle);
      font-size: 12px;
      line-height: 18px;
    }

    .tag-add-button,
    .manager-link-button {
      min-height: 24px;
      padding: 2px 6px;
      border: 1px dashed var(--line);
      background: transparent;
      color: var(--muted);
      box-shadow: none;
      font-size: 11px;
      line-height: 16px;
      letter-spacing: 0;
      text-transform: none;
    }

    .manager-link-button {
      border-color: transparent;
      color: var(--secondary);
    }

    .tag-add-button .material-symbols-outlined,
    .manager-link-button .material-symbols-outlined {
      width: 14px;
      height: 14px;
      font-size: 14px;
    }

    .manager-test-list {
      display: flex;
      flex-direction: column;
      gap: 10px;
      max-height: 420px;
      overflow: auto;
    }

    .manager-case-tabs {
      display: flex;
      align-items: center;
      gap: 0;
      border-bottom: 1px solid var(--line);
      margin-bottom: 2px;
    }

    .manager-case-tabs button {
      min-height: 28px;
      padding: 4px 12px;
      border: 0;
      border-bottom: 2px solid transparent;
      border-radius: 0;
      background: transparent;
      color: var(--muted);
      font-size: 12px;
      letter-spacing: 0;
      text-transform: none;
    }

    .manager-case-tabs button.active {
      border-bottom-color: var(--accent);
      color: var(--accent);
      font-weight: 700;
    }

    .manager-case-card,
    .add-test-card {
      border-radius: 4px;
      border-color: var(--line);
      background: var(--surface-lowest);
    }

    .manager-case-card .case-title {
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;
    }

    .manager-test-grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 8px;
    }

    .compact-io-label {
      display: grid;
      gap: 4px;
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }

    .manager-test-name-input {
      min-height: 28px;
      font-size: 13px;
    }

    .manager-case-card .small-textarea,
    .add-test-card .small-textarea {
      min-height: 54px;
      resize: vertical;
      border-radius: 4px;
      background: var(--surface-low);
      font-size: 12px;
      line-height: 18px;
    }

    .compact-form-grid {
      gap: 8px;
    }

    .manager-input-row {
      gap: 5px;
    }

    .manager-input-row textarea {
      min-height: 44px;
      font-size: 12px;
      line-height: 18px;
    }

    .manager-solution-pane {
      grid-template-rows: minmax(110px, 0.42fr) auto minmax(120px, 0.45fr) minmax(220px, 1fr);
    }

    .solution-code-shell {
      min-height: 0;
      height: 100%;
      border-color: var(--line);
      background: var(--surface-lowest);
    }

    .solution-code-shell .manager-code-toolbar {
      min-height: 30px;
      background: var(--surface-low);
      border-bottom-color: var(--line);
      color: var(--muted);
    }

    .solution-code-shell .manager-reference-editor {
      min-height: 0;
      height: calc(100% - 31px);
      background: var(--surface-lowest);
      color: var(--text);
    }

    .manager-verifier-card {
      flex: 1 1 auto;
      border-radius: 0;
      border: 0;
      background: var(--surface);
    }

    .manager-verifier-card .manager-output {
      margin: 0 12px 12px;
      max-height: 260px;
      padding: 10px;
      background: var(--surface-lowest);
      border: 1px solid var(--line);
      border-radius: 4px;
    }


    /* Strict Stitch Create convergence: small labeled model bar, action row, then preview tabs. */
    .stitch-create-view .create-model-bar {
      height: 57px;
      min-height: 57px;
      padding: 8px 12px;
      display: flex;
      align-items: center;
      gap: 14px;
      justify-content: flex-start;
      overflow: hidden;
      background: var(--surface-low);
      border-bottom: 1px solid var(--line);
    }

    .create-control-block {
      display: flex;
      flex-direction: column;
      gap: 3px;
      min-width: 0;
      color: var(--muted);
      font-family: "Geist", ui-sans-serif, sans-serif;
      font-size: 10px;
      line-height: 14px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    .create-control-block select,
    .create-control-block input {
      width: 100%;
      height: 28px;
      min-height: 28px;
      padding: 3px 8px;
      border: 1px solid var(--line);
      border-radius: 4px;
      background: var(--surface-lowest);
      color: var(--text);
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-size: 12px;
      line-height: 18px;
      text-transform: none;
      letter-spacing: 0;
    }

    .stitch-create-view .provider-field {
      width: min(210px, 27vw);
    }

    .stitch-create-view .model-field {
      width: min(180px, 22vw);
    }

    .stitch-create-view .key-field {
      width: min(150px, 18vw);
    }

    .create-key-row {
      display: flex;
      align-items: center;
      gap: 5px;
      min-width: 0;
    }

    .create-key-row input {
      flex: 1;
      min-width: 0;
    }

    .create-key-row .icon-button {
      width: 28px;
      min-width: 28px;
      height: 28px;
      min-height: 28px;
    }

    .stitch-create-view .create-preview-actions {
      min-height: 40px;
      height: 40px;
      padding: 5px 12px;
      justify-content: flex-end;
    }

    .stitch-create-view .create-preview-tabs-bar {
      min-height: 40px;
      padding: 6px 12px;
      display: flex;
      align-items: center;
      border-bottom: 1px solid var(--line);
      background: var(--surface-low);
    }

    .stitch-create-view .create-preview-tabs-bar .create-preview-tabs {
      width: auto;
    }

    .practice-action-bar button:first-child {
      background: var(--surface);
      color: var(--text);
    }

    .practice-action-bar button:last-child {
      color: var(--muted);
    }


"""
