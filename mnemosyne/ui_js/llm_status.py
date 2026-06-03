from __future__ import annotations

"""Shared LLM provider/model/key status used by Create and Manage."""

LLM_STATUS_SCRIPT = r"""    async function ensureDirectJsonPromptText() {
      if (directJsonPromptLoaded && directJsonPromptText) return directJsonPromptText;
      const promptRes = await fetch('/api/authoring/prompt');
      const data = await promptRes.json();
      directJsonPromptText = data.prompt || '';
      directJsonPromptLoaded = true;
      return directJsonPromptText;
    }

    async function loadLlmPanel() {
      await loadLlmStatus();
      const restored = restoreCreateState();
      const llmView = document.getElementById('llmView');
      if (!restored && llmView && !llmView.dataset.createMode) {
        setCreateConversationMode('agent', {reset: false});
      }
    }

    async function loadLlmStatus() {
      if (llmState) {
        renderLlmStatus();
        return llmState;
      }
      try {
        const res = await fetch('/api/llm/status');
        llmState = await res.json();
      } catch {
        llmState = {configured: false, message: 'LLM status unavailable.'};
      }
      renderLlmStatus();
      return llmState;
    }

    function renderLlmStatus() {
      const status = document.getElementById('llmStatus');
      if (!status || !llmState) return;
      renderLlmProviderSelects();
      if (createConversationMode === 'direct') {
        status.className = 'badge';
        status.textContent = 'Direct JSON';
        const hint = document.getElementById('llmProviderHint');
        if (hint) hint.textContent = '';
        return;
      }
      const provider = currentSelectedProvider();
      const ready = isProviderReady(provider);
      status.className = ready ? 'badge ok' : 'badge error';
      status.textContent = ready
        ? `Ready: ${provider?.label || provider?.id || 'provider'}`
        : providerNeedsSessionKey(provider)
          ? `${provider?.label || provider?.id || 'Provider'} needs key`
          : 'Needs provider';
      const output = document.getElementById('llmOutput');
      if (output && output.textContent === 'No LLM request yet.' && !ready) {
        output.textContent = llmState.message || 'Choose a configured provider.';
      }
      renderLlmProviderHint(provider);
    }

    function renderLlmProviderHint(provider) {
      const hint = document.getElementById('llmProviderHint');
      if (!hint) return;
      const profile = provider?.profile || {};
      const bits = [];
      if (profile.strategy) bits.push(`Strategy: ${profile.strategy}`);
      if (profile.supports_multimodal_attachments) bits.push('PDF/image attachments supported');
      if (profile.max_recommended_count) bits.push(`Recommended batch: up to ${profile.max_recommended_count}, generated one at a time`);
      if (profile.notes) bits.push(profile.notes);
      hint.textContent = bits.join(' · ');
    }

    function renderLlmProviderSelects() {
      const providers = llmState?.providers || [];
      const selected = preferredLlmProviderId(llmState?.default_provider || llmState?.provider || 'ollama');
      ['llmProvider', 'managerLlmProvider'].forEach(id => {
        const select = document.getElementById(id);
        if (!select) return;
        const previous = select.value || selected;
        select.innerHTML = providers.map(provider => {
          const label = providerOptionLabel(provider);
          return `<option value="${escapeHtml(provider.id)}">${escapeHtml(label)}</option>`;
        }).join('');
        select.value = providers.some(provider => provider.id === previous) ? previous : selected;
      });
      renderLlmModelSelect('llmProvider', 'llmModel');
      renderLlmModelSelect('managerLlmProvider', 'managerLlmModel');
      loadLlmApiKeyInputs();
    }

    function providerOptionLabel(provider) {
      const label = provider?.label || provider?.id || 'Provider';
      if (isProviderReady(provider)) return label;
      if (providerNeedsSessionKey(provider)) return `${label} (enter key)`;
      return `${label} (not ready)`;
    }

    function preferredLlmProviderId(fallback) {
      const providers = llmState?.providers || [];
      if (currentSessionApiKey() && providers.some(provider => provider.id === 'gemini')) {
        const fallbackProvider = providers.find(provider => provider.id === fallback);
        if (!fallbackProvider?.configured || fallback === 'ollama') return 'gemini';
      }
      return fallback;
    }

    function currentSelectedProvider() {
      const selected = document.getElementById('llmProvider')?.value || llmState?.provider || llmState?.default_provider;
      return (llmState?.providers || []).find(provider => provider.id === selected) || null;
    }

    function providerNeedsSessionKey(provider) {
      return Boolean(provider?.accepts_session_key && !provider.configured && !currentSessionApiKey());
    }

    function isProviderReady(provider) {
      if (!provider) return false;
      if (provider.configured) return true;
      if (!provider.accepts_session_key || !currentSessionApiKey()) return false;
      if (provider.id === 'openai_compatible') return Boolean(provider.base_url);
      return true;
    }

    function currentSessionApiKey() {
      return (document.getElementById('llmApiKey')?.value
        || document.getElementById('managerLlmApiKey')?.value
        || llmSessionApiKey
        || '').trim();
    }

    function loadLlmApiKeyInputs() {
      const key = llmSessionApiKey || '';
      ['llmApiKey', 'managerLlmApiKey'].forEach(id => {
        const input = document.getElementById(id);
        if (input && !input.value) input.value = key;
      });
    }

    function handleLlmApiKeyInput(input) {
      const value = input.value.trim();
      if (value) {
        llmSessionApiKey = value;
        syncLlmApiKeyInputs(value);
        preferSessionKeyProvider();
      } else {
        llmSessionApiKey = '';
        syncLlmApiKeyInputs('');
      }
      renderLlmStatus();
    }

    function preferSessionKeyProvider() {
      ['llmProvider', 'managerLlmProvider'].forEach(id => {
        const select = document.getElementById(id);
        if (!select || select.value !== 'ollama') return;
        const providers = llmState?.providers || [];
        const configuredDefault = providers.find(provider => provider.id === llmState?.provider && provider.accepts_session_key);
        const firstKeyProvider = configuredDefault || providers.find(provider => provider.accepts_session_key);
        if (firstKeyProvider && [...select.options].some(option => option.value === firstKeyProvider.id)) {
          select.value = firstKeyProvider.id;
        }
      });
      renderLlmModelSelect('llmProvider', 'llmModel', {force: true});
      renderLlmModelSelect('managerLlmProvider', 'managerLlmModel', {force: true});
    }

    function currentLlmApiKey() {
      const focused = document.activeElement?.id;
      const primary = focused === 'managerLlmApiKey' || focused === 'llmApiKey'
        ? document.getElementById(focused)
        : null;
      const value = (
        primary?.value
        || document.getElementById('llmApiKey')?.value
        || document.getElementById('managerLlmApiKey')?.value
        || llmSessionApiKey
        || ''
      ).trim();
      if (value) {
        llmSessionApiKey = value;
        syncLlmApiKeyInputs(value);
      }
      return value || null;
    }

    function syncLlmApiKeyInputs(value) {
      ['llmApiKey', 'managerLlmApiKey'].forEach(id => {
        const input = document.getElementById(id);
        if (input && input.value !== value) input.value = value;
      });
    }

    function clearLlmApiKey() {
      llmSessionApiKey = '';
      syncLlmApiKeyInputs('');
      setLlmOutput('API key cleared from this page.');
      renderLlmStatus();
    }

    function renderLlmModelSelect(providerSelectId, modelSelectId, {force = false} = {}) {
      const select = document.getElementById(providerSelectId);
      const modelSelect = document.getElementById(modelSelectId);
      if (!select || !modelSelect) return;
      const provider = (llmState?.providers || []).find(item => item.id === select.value);
      const previous = modelSelect.value;
      const options = llmModelOptions(provider);
      const optionMarkup = options.map(option => (
        `<option value="${escapeHtml(option.value)}" label="${escapeHtml(option.label)}"></option>`
      )).join('');
      const listId = modelSelect.getAttribute('list');
      const datalist = listId ? document.getElementById(listId) : null;
      if (datalist) {
        datalist.innerHTML = optionMarkup;
      } else {
        modelSelect.innerHTML = options.map(option => (
          `<option value="${escapeHtml(option.value)}">${escapeHtml(option.label)}</option>`
        )).join('');
      }
      const preferred = provider?.default_model || options[0]?.value || '';
      const canKeepPrevious = previous && (datalist || options.some(option => option.value === previous));
      if (!force && canKeepPrevious) {
        modelSelect.value = previous;
      } else if (preferred && options.some(option => option.value === preferred)) {
        modelSelect.value = preferred;
      } else if (options[0]) {
        modelSelect.value = options[0].value;
      } else {
        modelSelect.value = '';
      }
    }

    function llmModelOptions(provider) {
      if (!provider) return [{value: '', label: 'Default model'}];
      if (provider.available_models?.length) {
        return provider.available_models.map(model => ({value: model, label: geminiModelLabel(model)}));
      }
      if (provider.id === 'openai') {
        const defaults = [provider.default_model, 'gpt-4.1-mini', 'gpt-4.1'].filter(Boolean);
        return dedupe(defaults).map(model => ({value: model, label: model}));
      }
      if (provider.default_model) {
        return [{value: provider.default_model, label: provider.default_model}];
      }
      return [{value: '', label: 'Use environment default'}];
    }

    function geminiModelLabel(model) {
      if (typeof model !== 'string') return String(model || '');
      if (!model.startsWith('gemini-')) return model;
      return model
        .replace(/^gemini-/, 'Gemini ')
        .replaceAll('-', ' ')
        .replace(/\b\w/g, char => char.toUpperCase());
    }

    function dedupe(values) {
      const seen = new Set();
      return values.filter(value => {
        if (seen.has(value)) return false;
        seen.add(value);
        return true;
      });
    }

    function handleLlmProviderChange(providerSelectId, modelInputId) {
      renderLlmModelSelect(providerSelectId, modelInputId, {force: true});
      renderLlmStatus();
    }

    function selectedLlmModel(modelSelectId) {
      const value = document.getElementById(modelSelectId)?.value || '';
      return value.trim() || null;
    }

"""
