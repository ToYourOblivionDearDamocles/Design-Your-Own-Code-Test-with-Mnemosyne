from __future__ import annotations

CREATE_AGENT_VIEW = r"""<div id="llmView" class="view stitch-create-view" hidden>
        <div class="create-workspace">
          <section class="create-chat-pane">
            <div class="create-model-bar">
              <label class="create-control-block provider-field">
                <span>Provider</span>
                <select id="llmProvider" aria-label="Provider" onchange="handleLlmProviderChange('llmProvider', 'llmModel')"></select>
              </label>
              <label class="create-control-block model-field">
                <span>Model</span>
                <input id="llmModel" class="text-input" aria-label="Model" list="llmModelOptions" placeholder="model" />
                <datalist id="llmModelOptions"></datalist>
              </label>
              <label class="create-control-block key-field">
                <span>API Key</span>
                <div class="create-key-row">
                  <input id="llmApiKey" class="text-input" aria-label="API key" type="password" autocomplete="off" placeholder="key" oninput="handleLlmApiKeyInput(this)" />
                  <button class="icon-button danger" title="Clear API key" onclick="clearLlmApiKey()"><span class="material-symbols-outlined" aria-hidden="true">delete</span></button>
                </div>
              </label>
              <span id="llmStatus" class="badge" hidden>Checking</span>
            </div>

            <div id="createChatScroll" class="create-chat-scroll">
              <div class="chat-divider"><span>Session initialized</span></div>
              <div id="llmPrimaryBubble" class="chat-bubble agent-bubble compact-agent-bubble">
                <div class="chat-kicker bubble-kicker">
                  <span class="bubble-title"><span class="material-symbols-outlined" aria-hidden="true">psychology</span><span id="llmOutputTitle">Agent</span></span>
                  <button id="llmPrimaryCopyButton" class="copy-chip" onclick="copyCreatePrimaryText()" hidden><span class="material-symbols-outlined" aria-hidden="true">content_copy</span><span>Copy</span></button>
                </div>
                <pre id="llmOutput" class="author-output chat-output">No LLM request yet.</pre>
              </div>
              <div id="directJsonInstructionBubble" class="chat-bubble agent-bubble direct-json-instruction-bubble" hidden>
                <div class="chat-kicker"><span class="material-symbols-outlined" aria-hidden="true">assignment</span><span id="directJsonInstructionTitle">How to use</span></div>
                <pre id="directJsonInstructions" class="author-output chat-output"></pre>
              </div>
              <div id="llmProviderHint" class="llm-provider-hint"></div>
            </div>

            <div class="create-composer">
              <div class="direct-submission-row">
                <button id="createNewChatButton" class="small new-chat-button" onclick="startCreateNewChat()"><span class="material-symbols-outlined" aria-hidden="true">restart_alt</span><span>New Chat</span></button>
                <button id="createDirectJsonButton" class="small direct-json-button" onclick="toggleCreateDirectJsonMode()"><span class="material-symbols-outlined" aria-hidden="true">data_object</span><span>Direct JSON</span></button>
              </div>
              <textarea id="llmProblemRequest" class="chat-request" spellcheck="false" placeholder="Example: Create 3 medium NumPy problems about Cholesky decomposition from the attached lecture. Keep each problem focused and include explicit tests."></textarea>
              <input id="llmAttachmentInput" class="hidden-file-input" type="file" multiple accept=".pdf,.md,.markdown,.txt,.json,.csv,.tsv,.py,.yaml,.yml,image/*,application/pdf,text/markdown,text/plain,application/json" onchange="handleLlmAttachmentChange(this)" />
              <input id="llmProblemCount" class="number-input" type="number" min="1" max="10" value="1" hidden />
              <input id="llmTimeoutSeconds" class="number-input" type="number" min="10" max="600" value="180" hidden />
              <div id="llmAttachmentList" class="llm-attachment-list"></div>
              <div class="create-send-row stitch-composer-actions">
                <label class="icon-button" for="llmAttachmentInput" title="Attach file"><span class="material-symbols-outlined" aria-hidden="true">attach_file</span></label>
                <button id="createSendButton" class="primary icon-button" onclick="submitCreateComposer()" title="Send"><span class="material-symbols-outlined" aria-hidden="true">send</span></button>
              </div>
            </div>
          </section>

          <div id="createModuleSplitter" class="module-splitter" aria-hidden="true"></div>

          <section class="create-preview-pane">
            <div class="create-preview-header create-preview-actions">
              <div class="runtime-actions">
                <span id="llmDecisionStatus" class="badge" hidden>Waiting</span>
                <button class="small primary" onclick="createLlmDraftProblem()"><span class="material-symbols-outlined" aria-hidden="true">save</span><span>Commit</span></button>
                <button class="small" onclick="validateLlmDraft()"><span class="material-symbols-outlined" aria-hidden="true">check_circle</span><span>Verify</span></button>
              </div>
            </div>
            <div class="create-preview-tabs-bar">
              <div class="create-preview-tabs" aria-label="Generated problem sections">
                <button id="createPreviewProblemTab" class="active" onclick="setCreatePreviewSection('problem')">Problem</button>
                <button id="createPreviewTheoryTab" onclick="setCreatePreviewSection('theory')">Theory</button>
                <button id="createPreviewExampleTab" onclick="setCreatePreviewSection('example')">Example</button>
                <button id="createPreviewSolutionTab" onclick="setCreatePreviewSection('solution')">Solution</button>
              </div>
            </div>

            <div id="llmResultPreviewPane" class="create-preview-scroll llm-result-pane">
              <span id="llmDepsStatus" class="badge" hidden>Not checked</span>
              <span id="llmPreviewStatus" class="badge" hidden>No draft</span>
              <div id="llmPreview">
                <div class="empty">Generate a draft to preview the problem, theory, worked examples, solution, and tests.</div>
              </div>
            </div>

            <div id="createVerifierSplitter" class="vertical-splitter create-verifier-splitter" aria-hidden="true"></div>

            <div class="create-verifier-panel">
              <div class="verifier-head" title="Verifier details">
                <div><span class="material-symbols-outlined" aria-hidden="true">bug_report</span><span>Verifier Run Report</span></div>
              </div>
              <div id="llmResultReportPane" class="llm-result-pane verifier-body">
                <pre id="llmDecisionOutput" class="author-output verifier-output">Generated drafts stay here until you add them to the library.</pre>
              </div>
              <div id="llmResultJsonPane" hidden>
                <textarea id="llmDraftJson" spellcheck="false"></textarea>
                <input id="llmOverwrite" type="checkbox" />
              </div>
            </div>
          </section>
        </div>
      </div>

      """
