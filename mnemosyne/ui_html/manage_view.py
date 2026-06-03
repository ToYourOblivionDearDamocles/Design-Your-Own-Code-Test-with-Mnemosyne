from __future__ import annotations

MANAGE_VIEW = r"""<div id="manageView" class="view stitch-manage-view" hidden>
        <div id="managerPanel" class="manage-workspace" hidden>
          <div class="manage-split">
            <section class="manage-editor-pane">
              <h2 id="managerProblemTitle" class="panel-title" hidden>Manage problem</h2>
              <div class="manage-editor-header">
                <button id="managerCreateDraftButton" class="small manager-create-button" title="Create problem" onclick="startManagerCreateDraft()"><span class="material-symbols-outlined" aria-hidden="true">add_circle</span><span>Create</span></button>
                <div class="manager-learning-tabs" role="tablist" aria-label="Editable learning modules">
                  <button id="managerProblemSectionTab" class="active" onclick="setManagerLearningSection('problem')">Problem</button>
                  <button id="managerTheorySectionTab" onclick="setManagerLearningSection('theory')">Theory</button>
                  <button id="managerExampleSectionTab" onclick="setManagerLearningSection('example')">Example</button>
                  <button id="managerSolutionSectionTab" onclick="setManagerLearningSection('solution')">Solution</button>
                </div>
                <div class="manager-mode-toggle">
                  <button id="managerEditModeButton" class="active" onclick="setManagerEditMode('edit')">Edit</button>
                  <button id="managerPreviewModeButton" onclick="setManagerEditMode('preview')">Preview</button>
                </div>
              </div>

              <div class="manager-editor-canvas">
                <div id="managerProblemSectionPane" class="manager-learning-pane">
                  <textarea id="managerStatement" class="author-textarea manager-learning-editor" spellcheck="false" oninput="syncManagerLearningPreviews()"></textarea>
                  <div class="manager-live-preview">
                    <div class="test-name">Preview</div>
                    <div id="managerStatementPreview" class="statement"></div>
                  </div>
                </div>
                <div id="managerTheorySectionPane" class="manager-learning-pane" hidden>
                  <textarea id="managerTheory" class="author-textarea manager-learning-editor" spellcheck="false" oninput="syncManagerLearningPreviews()" placeholder="Theory notes, algorithm intuition, or math background in Markdown."></textarea>
                  <div class="manager-live-preview">
                    <div class="test-name">Preview</div>
                    <div id="managerTheoryPreview" class="statement"></div>
                  </div>
                </div>
                <div id="managerExampleSectionPane" class="manager-learning-pane" hidden>
                  <textarea id="managerExamples" class="author-textarea manager-learning-editor" spellcheck="false" oninput="syncManagerLearningPreviews()" placeholder="Worked examples. Use Markdown for one or two step-by-step examples."></textarea>
                  <div class="manager-live-preview">
                    <div class="test-name">Preview</div>
                    <div id="managerExamplesPreview" class="statement"></div>
                  </div>
                </div>
                <div id="managerSolutionSectionPane" class="manager-learning-pane manager-solution-pane" hidden>
                  <textarea id="managerSolutionExplanation" class="author-textarea manager-learning-editor" spellcheck="false" oninput="syncManagerLearningPreviews()" placeholder="Approach explanation shown before the reference solution."></textarea>
                  <div class="manager-complexity-editor">
                    <label>
                      Time
                      <input id="managerComplexityTime" class="text-input" spellcheck="false" placeholder="O(n)" oninput="syncManagerLearningPreviews()" />
                    </label>
                    <label>
                      Space
                      <input id="managerComplexitySpace" class="text-input" spellcheck="false" placeholder="O(1)" oninput="syncManagerLearningPreviews()" />
                    </label>
                  </div>
                  <div class="manager-live-preview manager-solution-preview">
                    <div class="test-name">Solution Preview</div>
                    <div id="managerSolutionExplanationPreview" class="statement"></div>
                    <div id="managerComplexityPreview" class="manager-complexity-preview"></div>
                    <div class="test-name">Reference solution</div>
                    <pre id="managerReferenceSolutionPreview" class="solution-code"></pre>
                  </div>
                  <div class="manager-code-shell solution-code-shell">
                    <div class="manager-code-toolbar">
                      <span>reference_solution.py</span>
                      <span>Python 3</span>
                    </div>
                    <textarea id="managerReferenceSolution" class="code-editor manager-reference-editor" spellcheck="false" autocomplete="off" autocorrect="off" autocapitalize="off" oninput="syncManagerLearningPreviews()"></textarea>
                  </div>
                </div>
              </div>
            </section>

            <div id="manageModuleSplitter" class="module-splitter" aria-hidden="true"></div>

            <section class="manage-right-pane">
              <div class="manage-right-header">
                <span id="managerStatus" class="badge" hidden>Select a problem</span>
                <button id="managerCommitButton" class="small primary" title="Save problem" onclick="saveManagedProblem()"><span class="material-symbols-outlined" aria-hidden="true">publish</span><span id="managerCommitLabel">Commit</span></button>
                <button class="small" title="Check problem" onclick="validateManagedProblem()"><span class="material-symbols-outlined" aria-hidden="true">check_circle</span><span>Verify</span></button>
              </div>

              <section class="manager-side-section manager-tags-section">
                <h3 class="manager-section-title">Tags &amp; Labels</h3>
                <div class="manager-tags-row">
                  <div id="managerProblemMeta" class="problem-card-meta manager-tag-strip"></div>
                  <div class="manager-inline-tag-editor">
                    <input id="managerInlineTagInput" class="text-input" placeholder="python, numpy, graph" onkeydown="handleManagerTagKeydown(event)" />
                    <button class="tag-save-button" onclick="saveManagerTagsFromInline()"><span class="material-symbols-outlined" aria-hidden="true">check</span><span>Save</span></button>
                  </div>
                </div>
              </section>

              <section class="manager-side-section tests-pane">
                <div class="manager-section-head">
                  <h3 class="manager-section-title">Test Cases</h3>
                  <button class="small manager-refresh-output-button" title="Regenerate expected outputs from the reference solution" onclick="refreshManagedTestOutputs()"><span class="material-symbols-outlined" aria-hidden="true">sync</span><span>Outputs</span></button>
                </div>
                <div id="managerTestOutputNotice" class="manager-output-notice" hidden></div>
                <div class="manager-preview">
                  <div id="managerTestList" class="manager-test-list"></div>
                  <div id="managerAddTestCard" class="test-card add-test-card" hidden>
                    <div class="test-name">New Case</div>
                    <div class="form-grid compact-form-grid">
                      <select id="managerTestGroup" hidden>
                        <option value="visible_tests">Explicit test</option>
                      </select>
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
                      <button class="small primary" onclick="addManagedTestCase()"><span class="material-symbols-outlined" aria-hidden="true">add</span><span>Add Case</span></button>
                    </div>
                  </div>
                </div>
              </section>

              <section class="manager-side-section manager-verifier-card">
                <div class="manager-section-head verifier-head">
                  <h3 class="manager-section-title">Verifier Feedback</h3>
                  <button class="icon-button" title="Run verifier" onclick="validateManagedProblem()"><span class="material-symbols-outlined" aria-hidden="true">refresh</span></button>
                </div>
                <div id="managerOutput" class="manager-output verifier-output">Open Manage to edit the current problem.</div>
              </section>

              <div class="runtime-card manager-pane advanced-pane">
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
                        <button class="small primary" onclick="saveManagerTags()"><span class="material-symbols-outlined" aria-hidden="true">save</span><span>Tags</span></button>
                      </div>
                    </div>
                  </div>

                  <div id="managerLlmPane" class="manager-pane-section" hidden>
                    <div class="form-grid">
                      <label>
                        Request
                        <textarea id="managerLlmRequest" class="small-textarea" spellcheck="false" placeholder="Make the statement clearer, add one edge case, or generate explicit tests for negative values."></textarea>
                      </label>
                      <div class="llm-key-controls">
                        <label>
                          API key
                          <input id="managerLlmApiKey" class="text-input" type="password" autocomplete="off" placeholder="Paste key here if not set in shell" oninput="handleLlmApiKeyInput(this)" />
                        </label>
                        <div class="empty">Kept only until this page is refreshed.</div>
                        <button class="small" onclick="clearLlmApiKey()"><span class="material-symbols-outlined" aria-hidden="true">key_off</span><span>Key</span></button>
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
                        <button class="small primary" onclick="draftManagedProblemEdit()"><span class="material-symbols-outlined" aria-hidden="true">auto_fix_high</span><span>Edit</span></button>
                        <button class="small" onclick="draftManagedTests()"><span class="material-symbols-outlined" aria-hidden="true">science</span><span>Tests</span></button>
                      </div>
                      <div class="tag-editor-row">
                        <select id="managerLlmTestGroup">
                          <option value="visible_tests">Explicit tests</option>
                        </select>
                        <button id="managerApplyLlmTests" class="small primary" onclick="applyManagedLlmTests()" hidden><span class="material-symbols-outlined" aria-hidden="true">add_task</span><span>Add</span></button>
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
                </div>
              </div>
            </section>
          </div>
        </div>
      </div>

      """
