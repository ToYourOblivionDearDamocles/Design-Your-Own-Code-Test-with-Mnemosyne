from __future__ import annotations

"""Direct JSON mode, fixed repair loop, and user-facing repair prompts."""

CREATE_DIRECT_JSON_SCRIPT = r"""    async function setCreateConversationMode(mode, options = {}) {
      createConversationMode = mode === 'direct' ? 'direct' : 'agent';
      updateCreateModeUi();
      if (createConversationMode === 'direct' && options.reset) {
        await resetDirectJsonSession();
      }
      if (createConversationMode === 'agent' && options.reset) {
        clearLlmDraft();
      }
    }

    async function toggleCreateDirectJsonMode() {
      if (createConversationMode === 'direct') {
        await setCreateConversationMode('agent', {reset: true});
        return;
      }
      await setCreateConversationMode('direct', {reset: true});
    }

    function updateCreateModeUi() {
      const llmView = document.getElementById('llmView');
      if (llmView) llmView.dataset.createMode = createConversationMode;
      const directButton = document.getElementById('createDirectJsonButton');
      const newChatButton = document.getElementById('createNewChatButton');
      const textarea = document.getElementById('llmProblemRequest');
      const attachment = document.getElementById('llmAttachmentInput');
      const send = document.getElementById('createSendButton');
      if (directButton) directButton.classList.toggle('active', createConversationMode === 'direct');
      if (directButton) directButton.setAttribute('aria-pressed', createConversationMode === 'direct' ? 'true' : 'false');
      if (newChatButton) newChatButton.classList.toggle('direct-mode', false);
      if (textarea) {
        textarea.placeholder = createConversationMode === 'direct'
          ? 'Paste ONLY the generated .json file contents here, or attach the .json file. Do not paste chat prose, explanations, or markdown fences.'
          : 'Example: Create 3 medium NumPy problems about Cholesky decomposition from the attached lecture. Keep each problem focused and include explicit tests.';
      }
      if (attachment) {
        attachment.accept = createConversationMode === 'direct'
          ? '.json,application/json,text/plain'
          : '.pdf,.md,.markdown,.txt,.json,.csv,.tsv,.py,.yaml,.yml,image/*,application/pdf,text/markdown,text/plain,application/json';
        attachment.multiple = createConversationMode !== 'direct';
      }
      if (send) send.title = createConversationMode === 'direct' ? 'Validate JSON' : 'Send';
      const providerHint = document.getElementById('llmProviderHint');
      if (providerHint && createConversationMode === 'direct') providerHint.textContent = '';
      const instructionBubble = document.getElementById('directJsonInstructionBubble');
      if (instructionBubble && createConversationMode !== 'direct') instructionBubble.hidden = true;
      const title = document.getElementById('llmOutputTitle');
      if (title && createConversationMode !== 'direct') title.textContent = 'Agent';
      renderLlmStatus();
    }

    async function startCreateNewChat() {
      if (createConversationMode === 'direct') {
        await resetDirectJsonSession();
        return;
      }
      clearLlmDraft();
    }

    async function submitCreateComposer() {
      if (createConversationMode === 'direct') {
        return await submitDirectJsonDraft();
      }
      return await generateLlmProblemDraft();
    }

    async function resetDirectJsonSession() {
      clearCreateDraftState();
      const request = document.getElementById('llmProblemRequest');
      const draft = document.getElementById('llmDraftJson');
      if (request) request.value = '';
      if (draft) draft.value = '';
      clearLlmAttachments();
      clearCreateChatHistory();
      setLlmDecisionStatus(uiText('verifier.waiting', 'Waiting'), null);
      resetCreatePreview(uiText('direct_json.notifications.paste_json_first', 'Paste raw JSON or upload a .json file first.'));
      resetCreateVerifier(uiText('direct_json.notifications.no_json_verifier', 'No JSON was provided.'));
      await renderDirectJsonOpeningConversation();
      setLlmResultView('preview');
    }

    async function renderDirectJsonOpeningConversation() {
      const prompt = await ensureDirectJsonPromptText();
      const title = document.getElementById('llmOutputTitle');
      const instructionTitle = document.getElementById('directJsonInstructionTitle');
      const instructionBubble = document.getElementById('directJsonInstructionBubble');
      if (title) title.textContent = 'Prompt';
      if (instructionTitle) instructionTitle.textContent = 'How to use';
      const fullPrompt = directJsonExternalPrompt(prompt);
      setCreatePrimaryText(compactPromptPreview(fullPrompt), {copyText: fullPrompt, collapsed: true});
      if (instructionBubble) instructionBubble.hidden = false;
      const instructions = document.getElementById('directJsonInstructions');
      if (instructions) instructions.textContent = directJsonOpeningInstructions();
    }

    function directJsonExternalPrompt(prompt) {
      return [
        uiText('direct_json.external_prompt.intro', "Use this prompt in another AI chat. Ask it to create a .json file, or output only the raw JSON file contents for Mnemosyne's Direct JSON box:"),
        '',
        prompt
      ].join('\n');
    }

    function directJsonOpeningInstructions() {
      return uiTextList('direct_json.opening_instructions', [
        'Use Direct JSON when you are asking another AI chat to write the question JSON for you.',
        '',
        'Copy the prompt into another model, then paste only the returned JSON here.'
      ]).join('\n');
    }

    async function submitDirectJsonDraft() {
      const input = document.getElementById('llmProblemRequest');
      const raw = input?.value || '';
      const content = cleanModelJsonText(raw);
      if (input) input.value = content;
      if (!content.trim()) {
        setLlmDecisionStatus(uiText('direct_json.notifications.no_json_status', 'Needs JSON'), false);
        resetCreatePreview(uiText('direct_json.notifications.paste_json_first', 'Paste raw JSON or upload a .json file first.'));
        const noJson = uiText('direct_json.notifications.no_json_verifier', 'No JSON was provided.');
        resetCreateVerifier(noJson);
        return {ok: false, errors: [noJson]};
      }
      const draft = document.getElementById('llmDraftJson');
      if (draft) draft.value = content;
      const uploadedDraftContent = directJsonUploadedDraft?.content ? cleanModelJsonText(directJsonUploadedDraft.content) : '';
      const submittedFromUploadedFile = Boolean(uploadedDraftContent && uploadedDraftContent === content);
      if (!submittedFromUploadedFile) {
        appendCreateChatBubble({
          role: 'user',
          title: 'JSON draft',
          text: compactPromptPreview(content, 10, 1200),
          copyText: content,
          collapsed: true
        });
      }
      directJsonUploadedDraft = null;
      if (input) input.value = '';
      setLlmDecisionStatus('Verifying...', null);
      resetCreateVerifier(uiText('direct_json.notifications.checking_json', 'Checking JSON with the deterministic verifier...'));
      const result = await postJson('/api/authoring/validate', {content});
      renderDirectJsonResult(result, content);
      createDirty = true;
      saveCreateState();
      return result;
    }

    function renderDirectJsonResult(result, submittedContent = '') {
      const ok = Boolean(result.ok);
      const normalizedContent = problemContentFromResult(result) || submittedContent;
      const draft = document.getElementById('llmDraftJson');
      if (draft) draft.value = normalizedContent;
      if (ok) {
        setLlmDecisionStatus('Accept', true);
        const acceptedText = directJsonAcceptedMessage(result);
        setLlmOutput(acceptedText);
        appendCreateChatBubble({
          role: 'agent',
          title: 'Verifier accepted',
          text: acceptedText
        });
        const instructionTitle = document.getElementById('directJsonInstructionTitle');
        if (instructionTitle) instructionTitle.textContent = 'Next step';
        const instructions = document.getElementById('directJsonInstructions');
        if (instructions) instructions.textContent = uiText('direct_json.accepted_message.instruction', 'The verifier accepted this draft. You can still edit the JSON externally and paste a new version, or press Commit to add the validated problem(s) to the library.');
      } else {
        setLlmDecisionStatus('Needs fixes', false);
        const feedbackText = formatLlmResult(result);
        appendCreateChatBubble({
          role: 'agent',
          title: 'Verifier feedback',
          text: directJsonVerifierChatText(result),
          copyText: feedbackText,
          copyLabel: 'Copy feedback',
          collapsed: true
        });
      }
      const instructionBubble = document.getElementById('directJsonInstructionBubble');
      if (instructionBubble) instructionBubble.hidden = false;
      renderLlmPreview(result);
      renderCreateVerifierResult(result);
      setLlmResultView('preview');
    }

    function directJsonAcceptedMessage(result) {
      const count = result?.problems?.length || (result?.problem ? 1 : 0);
      const countText = count > 1
        ? formatUiText('direct_json.accepted_message.multiple', '{count} questions are ready.', {count})
        : count === 1
          ? uiText('direct_json.accepted_message.single', '1 question is ready.')
          : uiText('direct_json.accepted_message.fallback', 'The JSON is ready.');
      return [
        uiText('direct_json.accepted_message.title', 'Accept'),
        '',
        formatUiText('direct_json.accepted_message.verified', '{countText} The deterministic verifier passed.', {countText}),
        uiText('direct_json.accepted_message.next', 'Review the preview on the right. If it matches your intent, press Commit.')
      ].join('\n');
    }

    function directJsonVerifierChatText(result) {
      return [
        uiText('direct_json.verifier_chat.title', 'Needs fixes'),
        '',
        uiText('direct_json.verifier_chat.report_label', 'Verifier report:'),
        formatLlmResult(result)
      ].join('\n');
    }

"""
