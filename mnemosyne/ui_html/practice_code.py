from __future__ import annotations

PRACTICE_CODE_VIEW = r"""<div id="codeView" class="view">
        <div class="practice-workspace">
          <div class="practice-action-bar">
            <button onclick="submitCode('run')"><span class="material-symbols-outlined" aria-hidden="true">play_arrow</span><span>Run</span></button>
            <button onclick="resetCurrentCode()"><span>Clear</span></button>
          </div>
          <section class="practice-editor-card">
            <div class="practice-editor-toolbar">
              <div class="practice-editor-title">
                <span class="material-symbols-outlined code-mark" aria-hidden="true">code</span>
                <span>solution.py</span>
              </div>
              <div class="editor-meta">
                <span>Python 3</span>
                <span class="editor-meta-dot">•</span>
                <span>Auto</span>
              </div>
              <button class="small icon-button" title="Restore starter" onclick="resetCurrentCode()"><span class="material-symbols-outlined" aria-hidden="true">restore</span></button>
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

          <div id="practiceVerticalSplitter" class="vertical-splitter practice-vertical-splitter" aria-hidden="true"></div>

          <section class="practice-console-card">
            <div class="practice-console-head">
              <div class="console-title-group">
                <div class="console-tabs">
                  <button id="practiceTestsTab" class="console-tab active" onclick="setPracticeConsoleView('tests')"><span class="material-symbols-outlined" aria-hidden="true">check_box</span><span>Test Case</span></button>
                  <button id="practiceResultTab" class="console-tab" onclick="setPracticeConsoleView('result')"><span class="material-symbols-outlined" aria-hidden="true">terminal</span><span>Test Result</span></button>
                  <button id="practiceErrorTab" class="console-tab" onclick="setPracticeConsoleView('error')"><span class="material-symbols-outlined" aria-hidden="true">bug_report</span><span>Error</span></button>
                </div>
              </div>
              <div class="console-actions">
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
            <div id="practiceErrorPane" class="practice-console-pane panel-body" hidden>
              <div id="practiceError">
                <div class="empty">Run your code to see program errors.</div>
              </div>
            </div>
          </section>
          </div>
      </div>

      """
