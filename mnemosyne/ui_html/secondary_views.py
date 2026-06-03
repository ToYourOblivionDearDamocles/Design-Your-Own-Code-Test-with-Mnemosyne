from __future__ import annotations

SECONDARY_VIEWS_AND_BODY_CLOSE = r"""<div id="solutionView" class="view" hidden>
        <div class="solution-grid">
          <div class="history-panel">
            <div class="panel-head">
              <h2 class="panel-title">Reference solution</h2>
              <button class="small" onclick="loadSolution({force: true})"><span class="material-symbols-outlined" aria-hidden="true">refresh</span><span>Refresh</span></button>
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
              <button class="small" onclick="loadRuntimeStatus()"><span class="material-symbols-outlined" aria-hidden="true">refresh</span><span>Refresh</span></button>
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
              <button class="small" onclick="loadCurrentHistory()"><span class="material-symbols-outlined" aria-hidden="true">refresh</span><span>Refresh</span></button>
            </div>
            <div class="panel-body"><table id="currentHistoryTable"></table></div>
          </div>

          <div class="history-panel">
            <div class="panel-head">
              <h2 class="panel-title">Wrong problems</h2>
              <button class="small" onclick="loadWrongProblems()"><span class="material-symbols-outlined" aria-hidden="true">refresh</span><span>Refresh</span></button>
            </div>
            <div class="panel-body"><table id="wrongProblemsTable"></table></div>
          </div>

          <div class="history-panel">
            <div class="panel-head">
              <h2 class="panel-title">All submissions</h2>
              <button class="small" onclick="loadAllHistory()"><span class="material-symbols-outlined" aria-hidden="true">refresh</span><span>Refresh</span></button>
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
"""
