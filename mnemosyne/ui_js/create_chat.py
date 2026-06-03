from __future__ import annotations

"""Create-page chat window, compact prompt previews, copy buttons, and status chips."""

CREATE_CHAT_SCRIPT = r"""    function setLlmDecisionStatus(text, ok = null) {
      const status = document.getElementById('llmDecisionStatus');
      status.className = ok === null ? 'badge' : ok ? 'badge ok' : 'badge error';
      status.textContent = text;
    }

    function setCreatePrimaryText(text, options = {}) {
      const output = document.getElementById('llmOutput');
      if (!output) return;
      createPrimaryCopyText = options.copyText || '';
      output.textContent = text || '';
      output.classList.toggle('prompt-preview', Boolean(options.collapsed));
      const copyButton = document.getElementById('llmPrimaryCopyButton');
      if (copyButton) {
        copyButton.hidden = !createPrimaryCopyText;
        copyButton.dataset.copyLength = String(createPrimaryCopyText.length);
        copyButton.classList.remove('copied');
        const label = copyButton.querySelector('span:last-child');
        if (label) label.textContent = 'Copy';
      }
    }

    function clearCreateChatHistory() {
      createChatCopyTexts = {};
      document.querySelectorAll('[data-create-chat-message="true"]').forEach(node => node.remove());
    }

    function appendCreateChatBubble(options = {}) {
      const scroll = document.getElementById('createChatScroll');
      if (!scroll) return '';
      const role = options.role === 'user' ? 'user' : 'agent';
      const title = options.title || (role === 'user' ? 'You' : 'Mnemosyne');
      const text = options.text || '';
      const copyText = options.copyText || '';
      const id = `createChatMessage${++createChatMessageCounter}`;
      if (copyText) createChatCopyTexts[id] = copyText;

      const bubble = document.createElement('div');
      bubble.className = `chat-bubble ${role === 'user' ? 'user-bubble' : 'agent-bubble'} create-chat-message${options.collapsed ? ' compact-agent-bubble' : ''}`;
      bubble.dataset.createChatMessage = 'true';
      bubble.innerHTML = `
        <div class="chat-kicker bubble-kicker">
          <span class="bubble-title"><span class="material-symbols-outlined" aria-hidden="true">${role === 'user' ? 'person' : 'psychology'}</span><span>${escapeHtml(title)}</span></span>
          <button id="${id}Copy" class="copy-chip" onclick="copyCreateChatBubble('${id}')" ${copyText ? '' : 'hidden'}><span class="material-symbols-outlined" aria-hidden="true">content_copy</span><span>${escapeHtml(options.copyLabel || 'Copy')}</span></button>
        </div>
        <pre class="author-output chat-output${options.collapsed ? ' prompt-preview' : ''}"></pre>
      `;
      const output = bubble.querySelector('pre');
      if (output) output.textContent = text;
      const hint = document.getElementById('llmProviderHint');
      scroll.insertBefore(bubble, hint || null);
      scrollCreateChatToBottom();
      return id;
    }

    function scrollCreateChatToBottom() {
      const scroll = document.getElementById('createChatScroll');
      if (!scroll) return;
      requestAnimationFrame(() => {
        scroll.scrollTop = scroll.scrollHeight;
      });
    }

    async function copyCreateChatBubble(id) {
      const text = createChatCopyTexts[id] || '';
      if (!text.trim()) return;
      const copied = await writeClipboardText(text);
      const button = document.getElementById(`${id}Copy`);
      if (copied) {
        if (button) {
          button.classList.add('copied');
          const label = button.querySelector('span:last-child');
          if (label) label.textContent = 'Copied';
        }
        setLlmDecisionStatus('Copied', true);
      } else {
        setLlmDecisionStatus('Copy failed', false);
      }
    }

    async function writeClipboardText(text) {
      if (navigator.clipboard?.writeText) {
        try {
          await navigator.clipboard.writeText(text);
          return true;
        } catch {}
      }
      const helper = document.createElement('textarea');
      helper.value = text;
      helper.setAttribute('readonly', '');
      helper.style.position = 'fixed';
      helper.style.left = '-9999px';
      helper.style.top = '0';
      document.body.appendChild(helper);
      helper.select();
      let copied = false;
      try {
        copied = document.execCommand('copy');
      } finally {
        helper.remove();
      }
      return copied;
    }

    async function copyCreatePrimaryText() {
      const text = createPrimaryCopyText || document.getElementById('llmOutput')?.textContent || '';
      if (!text.trim()) return;
      const copied = await writeClipboardText(text);
      if (copied) {
        const copyButton = document.getElementById('llmPrimaryCopyButton');
        if (copyButton) {
          copyButton.classList.add('copied');
          const label = copyButton.querySelector('span:last-child');
          if (label) label.textContent = 'Copied';
        }
        setLlmDecisionStatus('Copied', true);
      } else {
        setLlmDecisionStatus('Copy failed', false);
      }
    }

    function setLlmOutput(text) {
      setCreatePrimaryText(text);
    }

    function setDraftDependencyStatus(id, text, ok = null) {
      const status = document.getElementById(id);
      if (!status) return;
      status.className = ok === null ? 'badge' : ok ? 'badge ok' : 'badge error';
      status.textContent = text;
    }

"""
