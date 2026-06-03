from __future__ import annotations

"""LLM-backed problem generation, attachment handling, draft preview, and verifier panel state."""

CREATE_LLM_SCRIPT = r"""    async function handleLlmAttachmentChange(input) {
      llmAttachmentFiles = Array.from(input.files || []);
      directJsonUploadedDraft = null;
      if (createConversationMode === 'direct') {
        const file = llmAttachmentFiles[0];
        renderLlmAttachmentList();
        if (!file) return;
        const name = file.name.toLowerCase();
        if (!name.endsWith('.json') && file.type !== 'application/json') {
          setLlmDecisionStatus('Needs .json', false);
          resetCreateVerifier(uiText('direct_json.notifications.direct_json_only', 'Direct JSON mode only accepts raw JSON text or a .json file.'));
          clearDirectJsonAttachmentPicker(input);
          return;
        }
        try {
          const text = await readFileAsText(file);
          document.getElementById('llmProblemRequest').value = text;
          directJsonUploadedDraft = {content: text, fileName: file.name};
          setLlmDecisionStatus('JSON loaded', true);
          resetCreateVerifier(formatUiText('direct_json.notifications.json_loaded', 'Loaded {fileName}. Press Send to run the deterministic verifier.', {fileName: file.name}));
          appendCreateChatBubble({
            role: 'user',
            title: 'Uploaded JSON',
            text: `${file.name} (${formatFileSize(file.size)})\n\n${compactPromptPreview(text, 8, 900)}`,
            copyText: text,
            copyLabel: 'Copy JSON',
            collapsed: true
          });
          scrollCreateChatToBottom();
          const instructionBubble = document.getElementById('directJsonInstructionBubble');
          if (instructionBubble) instructionBubble.hidden = false;
          clearDirectJsonAttachmentPicker(input);
        } catch (error) {
          setLlmDecisionStatus('File failed', false);
          resetCreateVerifier(error instanceof Error ? error.message : String(error));
          clearDirectJsonAttachmentPicker(input);
        }
        return;
      }
      renderLlmAttachmentList();
      if (llmAttachmentFiles.length) {
        renderCreateAttachmentChatBubble();
        setLlmDecisionStatus(`${llmAttachmentFiles.length} attachment${llmAttachmentFiles.length === 1 ? '' : 's'} ready`, true);
        setCreatePrimaryText(`Attached ${llmAttachmentFiles.length} file${llmAttachmentFiles.length === 1 ? '' : 's'}. Add or revise the request, then press Send.`);
      }
    }

    function clearDirectJsonAttachmentPicker(input) {
      llmAttachmentFiles = [];
      if (input) input.value = '';
      renderLlmAttachmentList();
    }

    function renderCreateAttachmentChatBubble() {
      const lines = llmAttachmentFiles.map(file => `- ${file.name} (${attachmentKindLabel(file)}, ${formatFileSize(file.size)})`);
      appendCreateChatBubble({
        role: 'user',
        title: 'Attached files',
        text: lines.join('\n') || 'No files attached.',
        collapsed: true
      });
    }

    function clearLlmAttachments() {
      llmAttachmentFiles = [];
      directJsonUploadedDraft = null;
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
      createDirty = true;
      saveCreateState();
      return result;
    }

    async function validateLlmDraft() {
      const content = document.getElementById('llmDraftJson').value;
      const result = await postJson('/api/authoring/validate', {content});
      renderLlmDraftResult(result, result.ok ? 'Valid' : 'Needs fixes');
      setDraftDependencyStatus('llmDepsStatus', 'Not installed', null);
      createDirty = true;
      saveCreateState();
      return result;
    }

    async function createLlmDraftProblem() {
      const content = document.getElementById('llmDraftJson').value;
      const overwrite = document.getElementById('llmOverwrite').checked;
      const result = await postJson('/api/authoring/problems', {content, overwrite});
      renderLlmDraftResult(result, result.created ? 'Created' : 'Not created');
      if (result.ok && result.created_count) {
        clearCreateDraftState();
        await refreshProblemIndex();
        const problemId = result.problem_id || result.results?.find(item => item.created)?.problem_id;
        if (problemId) await loadProblem(problemId);
      } else {
        createDirty = true;
        saveCreateState();
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
      createDirty = true;
      saveCreateState();
      return result;
    }

    function renderLlmDraftResult(result, statusText) {
      if (createConversationMode !== 'direct') {
        setLlmOutput(formatLlmResult(result));
      }
      setLlmDecisionStatus(Boolean(result.ok) ? statusText : 'Needs fixes', Boolean(result.ok));
      renderCreateVerifierResult(result);
      renderLlmPreview(result);
      const content = result.content || problemContentFromResult(result);
      if (content) {
        document.getElementById('llmDraftJson').value = content;
      }
      setLlmResultView(result.problems?.length || result.problem ? 'preview' : 'report');
    }

    function renderLlmPreview(result) {
      renderCreatePreview(result);
    }

    function renderCreateVerifierResult(result) {
      const output = document.getElementById('llmDecisionOutput');
      if (output) output.textContent = formatLlmResult(result);
    }

    function resetCreateVerifier(message) {
      const output = document.getElementById('llmDecisionOutput');
      if (output) output.textContent = message || 'Generated drafts stay here until you add them to the library.';
    }

    function toggleCreateVerifierPanel() {
      setLlmResultView('verifier');
    }

    function setLlmResultView(view = 'verifier') {
      llmResultView = 'verifier';
      createVerifierOpen = true;
      autoSizeCreateVerifierForView();
      const llmView = document.getElementById('llmView');
      if (llmView) {
        llmView.dataset.resultView = 'verifier';
        llmView.dataset.verifierOpen = 'true';
      }
      const previewPane = document.getElementById('llmResultPreviewPane');
      if (previewPane) previewPane.hidden = false;
      const reportPane = document.getElementById('llmResultReportPane');
      if (reportPane) reportPane.hidden = false;
      const jsonPane = document.getElementById('llmResultJsonPane');
      if (jsonPane) jsonPane.hidden = true;
    }

    function autoSizeCreateVerifierForView() {
      const pane = document.querySelector('.create-preview-pane');
      if (!pane || pane.dataset.verifierHeightTouched === 'true') return;
      const rect = pane.getBoundingClientRect();
      if (rect.height <= 0) return;
      const headerHeight = pane.querySelector('.create-preview-header')?.getBoundingClientRect().height || 48;
      const tabsHeight = pane.querySelector('.create-preview-tabs-bar')?.getBoundingClientRect().height || 44;
      const splitterHeight = document.getElementById('createVerifierSplitter')?.getBoundingClientRect().height || 10;
      const minPreview = 120;
      const minVerifier = 300;
      const fixedHeight = headerHeight + tabsHeight + splitterHeight;
      const maxVerifier = Math.max(minVerifier, rect.height - fixedHeight - minPreview);
      const target = rect.height * 0.46;
      const verifierHeight = clampNumber(target, minVerifier, maxVerifier);
      pane.style.setProperty('--create-verifier-height', `${Math.round(verifierHeight)}px`);
    }

    function compactPromptPreview(text, maxLines = 14, maxChars = 1800) {
      const raw = String(text || '');
      const lines = raw.split('\n');
      const visibleLines = lines.slice(0, maxLines).join('\n');
      const preview = visibleLines.length > maxChars ? `${visibleLines.slice(0, maxChars).trimEnd()}...` : visibleLines;
      if (lines.length <= maxLines && raw.length <= maxChars) return preview;
      return `${preview}\n\n[Prompt shortened. Use Copy to copy the complete text.]`;
    }

    function problemContentFromResult(result) {
      const problems = result?.problems?.length ? result.problems : result?.problem ? [result.problem] : [];
      if (!problems.length) return '';
      return stringifyProblemJson(problems.length === 1 ? problems[0] : problems);
    }

    function clearLlmDraft() {
      if (createConversationMode === 'direct') {
        resetDirectJsonSession();
        return;
      }
      document.getElementById('llmProblemRequest').value = '';
      document.getElementById('llmDraftJson').value = '';
      clearLlmAttachments();
      setLlmOutput('No LLM request yet.');
      setLlmDecisionStatus('Waiting', null);
      resetCreatePreview('Generate a draft to preview the problem, theory, worked examples, solution, and tests.');
      resetCreateVerifier('Generated drafts stay here until you add them to the library.');
      setDraftDependencyStatus('llmDepsStatus', 'Not checked', null);
      setLlmResultView('preview');
      clearCreateDraftState();
    }

    function sendLlmDraftToCreate() {
      const content = document.getElementById('llmDraftJson').value;
      setView('llm');
      setCreateConversationMode('direct', {reset: false});
      document.getElementById('llmProblemRequest').value = content;
      setLlmDecisionStatus('Draft copied', true);
      setCreatePrimaryText('Draft copied into Direct JSON. Press Send to verify it with the deterministic checker.');
      createDirty = true;
      saveCreateState();
    }

"""
