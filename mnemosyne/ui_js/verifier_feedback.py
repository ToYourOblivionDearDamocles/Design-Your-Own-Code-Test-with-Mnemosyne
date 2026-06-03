from __future__ import annotations

"""Shared verifier result formatting for compact text feedback."""

VERIFIER_FEEDBACK_SCRIPT = r"""    function formatLlmResult(result) {
      const lines = [];
      if (result.message) lines.push(result.message);
      if (result.attachments?.length) {
        lines.push(`attachments:\n${result.attachments.map(item => `- ${item.name} (${item.kind || 'file'}, ${item.mime_type || 'unknown'})`).join('\n')}`);
      }
      if (result.agent_plan?.summary) {
        const briefs = result.agent_plan.problem_briefs?.length
          ? `\nbriefs:\n${result.agent_plan.problem_briefs.map((brief, idx) => `- ${idx + 1}. ${brief.title || brief.id_hint || 'problem brief'}`).join('\n')}`
          : '';
        lines.push(`agent source digest:\n${result.agent_plan.summary}${briefs}`);
      }
      const errors = formatLimitedMessages('errors', result.errors);
      const warnings = formatLimitedMessages('warnings', result.warnings);
      if (errors) lines.push(errors);
      if (warnings) lines.push(warnings);
      const topRepairHints = formatRepairHints(result.repair_hints);
      if (topRepairHints) lines.push(`repair hints:\n${topRepairHints}`);
      if (result.attempts?.length) {
        lines.push(`attempts:\n${result.attempts.map((attempt, idx) => {
          const label = attempt.ok ? 'ok' : 'failed';
          const errors = attempt.errors?.length ? `: ${attempt.errors.map(sanitizeLocalPaths).join('; ')}` : '';
          const hints = formatRepairHints(attempt.repair_hints, {compact: true});
          const hintText = hints ? `\n  hints:\n${hints}` : '';
          const prefix = attempt.problem_index ? `problem ${attempt.problem_index}, attempt ${idx + 1}` : `${idx + 1}`;
          return `- ${prefix}: ${label}${errors}${hintText}`;
        }).join('\n')}`);
      }
      if (result.problem_results?.length) {
        lines.push(`problem results:\n${result.problem_results.map(item => {
          const mark = item.ok ? 'ready' : 'failed';
          const title = item.problem_id ? ` ${item.problem_id}` : '';
          const errors = item.errors?.length ? `: ${item.errors.map(sanitizeLocalPaths).join('; ')}` : '';
          const hints = formatRepairHints(item.repair_hints, {compact: true});
          const hintText = hints ? `\n  hints:\n${hints}` : '';
          return `- ${item.index}:${title} ${mark} (${item.attempts || 0} attempt${item.attempts === 1 ? '' : 's'})${errors}${hintText}`;
        }).join('\n')}`);
      }
      if (typeof result.created_count === 'number' && typeof result.total === 'number') {
        lines.push(`created: ${result.created_count}/${result.total}`);
      } else if (result.created) {
        lines.push('created: yes');
      } else if (result.saved) {
        lines.push('saved: yes');
      } else if (result.ok) {
        lines.push('accepted: verifier passed');
      }
      if (result.problem_id) lines.push(`problem: ${result.problem_id}`);
      if (typeof result.count === 'number') lines.push(`draft problems: ${result.count}`);
      if (typeof result.requested_count === 'number') lines.push(`requested problems: ${result.requested_count}`);
      return lines.join('\n\n') || 'No verifier feedback returned.';
    }

    function formatDependencyInstallResult(result) {
      const lines = [];
      if (result.message) lines.push(result.message);
      if (result.installed?.length) lines.push(`packages:\n- ${result.installed.join('\n- ')}`);
      const status = result.dependency_status;
      if (status?.requirements?.length) {
        const rows = status.requirements.map(req => {
          const mark = req.installed ? 'installed' : 'missing';
          const version = req.installed_version ? ` ${req.installed_version}` : '';
          return `- ${req.pip || req.package}: ${mark}${version}`;
        });
        lines.push(`dependencies:\n${rows.join('\n')}`);
      } else if (result.ok) {
        lines.push('dependencies: no package requirements found');
      }
      if (result.validation_errors?.length) lines.push(`draft validation still has errors:\n- ${result.validation_errors.join('\n- ')}`);
      const errors = formatLimitedMessages('errors', result.errors);
      const warnings = formatLimitedMessages('warnings', result.warnings);
      if (errors) lines.push(errors);
      if (warnings) lines.push(warnings);
      if (result.stdout) lines.push(`stdout:\n${result.stdout}`);
      if (result.stderr) lines.push(`stderr:\n${result.stderr}`);
      if (result.detail) lines.push(`error:\n${result.detail}`);
      return lines.join('\n\n') || JSON.stringify(result, null, 2);
    }

    function formatRepairHints(hints, options = {}) {
      if (!Array.isArray(hints) || !hints.length) return '';
      const prefix = options.compact ? '  -' : '-';
      return hints.map(hint => {
        if (!hint || typeof hint !== 'object') return `${prefix} ${hint}`;
        const code = hint.code ? `[${hint.code}] ` : '';
        const action = hint.action || hint.problem || JSON.stringify(hint);
        return `${prefix} ${code}${action}`;
      }).join('\n');
    }

    function sanitizeLocalPaths(value) {
      return String(value ?? '')
        .replace(/\/Users\/[^\s<>"'`]+/g, '[local path]')
        .replace(/\/private\/[^\s<>"'`]+/g, '[local path]')
        .replace(/\/var\/folders\/[^\s<>"'`]+/g, '[local path]');
    }

    function formatLimitedMessages(label, items, limit = 5) {
      if (!Array.isArray(items) || !items.length) return '';
      const visible = items.slice(0, limit).map(sanitizeLocalPaths);
      const more = items.length > limit ? `\n- ... ${items.length - limit} more` : '';
      return `${label}:\n- ${visible.join('\n- ')}${more}`;
    }

"""
