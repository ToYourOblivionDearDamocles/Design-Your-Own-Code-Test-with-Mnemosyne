from __future__ import annotations

"""Workspace Modules CSS segment for the Mnemosyne UI.

Order matters: import through mnemosyne.ui_css.APP_CSS only.
"""

WORKSPACE_MODULES_CSS = r"""    /* Stitch module pass 1: Practice + Problem Catalog exact structure */
    body[data-mode="practice"] #problemSelect {
      display: none;
    }

    .practice-top-actions button {
      min-height: 32px;
      padding: 5px 16px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      font-size: 12px;
      font-family: "Geist", ui-sans-serif, sans-serif;
    }

    .console-title-group {
      display: flex;
      align-items: center;
      gap: 20px;
      min-width: 0;
    }


    .catalog-search-row {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 12px;
      margin-bottom: 18px;
    }

    .catalog-search {
      display: flex;
      align-items: center;
      gap: 10px;
      width: min(100%, 460px);
      margin-bottom: 0;
      padding: 7px 12px;
      border: 1px solid var(--line);
      border-radius: 4px;
      background: var(--surface-lowest);
    }

    .catalog-search .material-symbols-outlined {
      color: var(--muted);
      font-size: 18px;
      flex: 0 0 auto;
    }

    .catalog-search .text-input {
      border: 0;
      background: transparent;
      padding: 0;
      min-height: 24px;
      width: 100%;
      font-size: 14px;
    }

    .catalog-search .text-input:focus {
      outline: none;
      box-shadow: none;
    }

    .icon-label-button {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      min-height: 34px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--muted);
      font-family: "Geist", ui-sans-serif, sans-serif;
      font-size: 12px;
    }

    .catalog-sidebar {
      display: flex;
      align-items: flex-start;
      gap: 10px;
      margin-bottom: 24px;
    }

    .catalog-sidebar-head {
      flex: 0 0 auto;
      margin-top: 7px;
    }



    /* Stitch module pass 2: Manage + Create rebuild */
    .stitch-create-view,
    .stitch-manage-view {
      padding: 0 !important;
      overflow: hidden;
      background: var(--surface-highest);
    }

    .create-workspace,
    .manage-split {
      height: 100%;
      min-height: 0;
      display: grid;
      grid-template-columns: minmax(420px, 1fr) minmax(460px, 1fr);
      background: var(--surface-highest);
    }

    .create-chat-pane,
    .create-preview-pane,
    .manage-editor-pane,
    .manage-right-pane {
      min-width: 0;
      min-height: 0;
      display: flex;
      flex-direction: column;
    }

    .create-chat-pane,
    .manage-editor-pane {
      border-right: 1px solid var(--line);
      background: var(--surface);
    }

    .create-preview-pane,
    .manage-right-pane {
      background: var(--surface-lowest);
    }

    .create-model-bar,
    .create-preview-header,
    .manage-editor-header {
      min-height: 48px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 8px 16px;
      border-bottom: 1px solid var(--line);
      background: var(--surface-high);
    }

    .create-model-title,
    .create-model-controls,
    .create-send-row,
    .create-attachment-row,
    .direct-submission-row,
    .verifier-head,
    .verifier-head > div,
    .manager-learning-tabs,
    .manager-mode-toggle {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .create-model-title,
    .verifier-head {
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--accent);
      font-weight: 700;
    }

    .create-model-controls {
      flex: 1;
      justify-content: flex-end;
      min-width: 0;
    }

    .compact-label {
      display: grid;
      gap: 3px;
      color: var(--subtle);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      font-family: "Geist", ui-sans-serif, sans-serif;
    }

    .compact-label select,
    .compact-label input {
      min-width: 0;
      height: 30px;
      padding: 4px 8px;
      font-size: 12px;
      font-family: "JetBrains Mono", ui-monospace, monospace;
    }

    .model-field { width: min(230px, 26vw); }
    .key-field { width: min(170px, 20vw); }

    .create-chat-scroll {
      flex: 1;
      min-height: 0;
      overflow: auto;
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }

    .chat-divider {
      display: grid;
      grid-template-columns: 1fr auto 1fr;
      align-items: center;
      gap: 16px;
      color: var(--subtle);
      font-family: "Geist", ui-sans-serif, sans-serif;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }

    .chat-divider::before,
    .chat-divider::after {
      content: "";
      height: 1px;
      background: var(--line);
    }

    .chat-bubble {
      max-width: 88%;
      padding: 16px;
      border: 1px solid var(--line);
      background: var(--surface-low);
      border-radius: 8px;
    }

    .user-bubble {
      align-self: flex-end;
      background: var(--surface-highest);
      border-top-right-radius: 2px;
    }

    .agent-bubble {
      align-self: flex-start;
      border-left: 2px solid var(--accent);
      border-top-left-radius: 2px;
    }

    .chat-kicker {
      display: flex;
      align-items: center;
      gap: 6px;
      margin-bottom: 8px;
      color: var(--accent);
      font-family: "Geist", ui-sans-serif, sans-serif;
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .chat-output,
    .verifier-output {
      max-height: none;
      border: 0;
      background: transparent;
      color: var(--muted);
      padding: 0;
      font-family: "JetBrains Mono", ui-monospace, monospace;
      white-space: pre-wrap;
    }

    .create-composer {
      padding: 16px;
      border-top: 1px solid var(--line);
      background: var(--surface-high);
      display: grid;
      gap: 10px;
    }

    .direct-submission-row {
      justify-content: space-between;
      padding: 8px 10px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--surface-lowest);
      color: var(--subtle);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      font-weight: 700;
    }

    .chat-request {
      width: 100%;
      min-height: 96px;
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      background: var(--surface-lowest);
      color: var(--text);
      line-height: 1.5;
    }

    .create-attachment-row,
    .create-send-row {
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 10px;
    }

    .create-send-row button {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      min-height: 32px;
    }

    .create-preview-header {
      background: var(--surface-high);
    }

    .create-preview-tabs,
    .manager-learning-tabs,
    .manager-mode-toggle {
      padding: 3px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--surface-lowest);
    }

    .create-preview-tabs button,
    .manager-learning-tabs button,
    .manager-mode-toggle span {
      border: 0;
      border-radius: 4px;
      background: transparent;
      padding: 5px 10px;
      color: var(--muted);
      font-family: "JetBrains Mono", ui-monospace, monospace;
      font-size: 12px;
    }

    .create-preview-tabs button.active,
    .manager-learning-tabs button.active,
    .manager-mode-toggle span:first-child {
      background: var(--surface-highest);
      color: var(--accent);
      box-shadow: inset 0 0 0 1px var(--line);
      font-weight: 700;
    }

    .create-preview-scroll {
      flex: 1 1 auto;
      min-height: 160px;
      overflow: auto;
      padding: 24px;
      background: var(--surface-lowest);
    }

    .preview-status-line {
      margin: 12px 0;
    }

    .create-verifier-panel {
      flex: 0 0 42px;
      min-height: 42px;
      max-height: 42px;
      border-top: 1px solid var(--line);
      background: var(--surface);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      transition: flex-basis 140ms ease, max-height 140ms ease;
    }

    .verifier-head {
      min-height: 42px;
      padding: 6px 12px;
      justify-content: space-between;
      border-bottom: 1px solid var(--line);
      background: var(--surface-high);
      cursor: pointer;
    }

    .verifier-body {
      flex: 1;
      min-height: 0;
      overflow: auto;
      padding: 12px;
      background: var(--surface-lowest);
    }


    .stitch-create-view[data-verifier-open="true"] .create-verifier-panel {
      flex-basis: clamp(230px, 36%, 420px);
      min-height: 230px;
      max-height: 44%;
    }

    .stitch-create-view:not([data-verifier-open="true"]) .verifier-body {
      display: none;
    }

    .json-draft-editor {
      min-height: 160px;
      height: 100%;
      resize: vertical;
    }

    .manage-workspace {
      height: 100%;
      min-height: 0;
      display: grid;
      grid-template-rows: auto minmax(0, 1fr);
      background: var(--surface-highest);
    }



    .danger-text {
      color: var(--wrong);
    }

    .manager-editor-canvas {
      flex: 1;
      min-height: 0;
      overflow: hidden;
      padding: 16px;
      background: var(--surface);
    }

    .manager-learning-pane {
      height: 100%;
      min-height: 0;
      display: grid;
      grid-template-rows: minmax(260px, 1fr) minmax(170px, 34%);
      gap: 14px;
    }

    .manager-learning-pane[hidden] {
      display: none;
    }

    .manager-learning-editor {
      min-height: 0;
      height: 100%;
      resize: none;
      border-radius: 6px;
      background: var(--surface-lowest);
      border-color: var(--line);
      font-family: "JetBrains Mono", ui-monospace, monospace;
      line-height: 1.55;
    }

    .manager-live-preview {
      min-height: 0;
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 12px;
      background: var(--surface-lowest);
    }

    .manage-right-pane {
      overflow: auto;
      padding: 16px;
      gap: 16px;
    }

    .manager-verifier-card,
    .tests-pane,
    .advanced-pane {
      border-radius: 6px;
      background: var(--surface-lowest);
      border-color: var(--line);
      flex: 0 0 auto;
    }

    .manager-verifier-card .manager-output {
      margin: 0 12px 12px;
      max-height: 240px;
      padding: 12px;
      background: var(--surface-low);
      border: 1px solid var(--line-soft);
    }

    .stitch-create-view[data-verifier-open="true"] .create-verifier-panel {
      flex: 0 0 clamp(230px, 36%, 420px);
      max-height: 44%;
    }



    .manager-code-shell .manager-reference-editor {
      background: var(--surface-lowest);
      color: var(--text);
      min-height: 300px;
      height: 300px;
    }

    .tests-pane .manager-test-list {
      max-height: 360px;
    }

    .add-test-card {
      background: var(--surface-low);
    }

    @media (max-width: 1100px) {
      .create-workspace,
      .manage-split {
        grid-template-columns: 1fr;
        overflow: auto;
      }
      .create-chat-pane,
      .manage-editor-pane {
        min-height: 640px;
        border-right: 0;
        border-bottom: 1px solid var(--line);
      }
      .create-preview-pane,
      .manage-right-pane {
        min-height: 640px;
      }
      .create-model-controls {
        justify-content: flex-start;
        flex-wrap: wrap;
      }
    }

"""
