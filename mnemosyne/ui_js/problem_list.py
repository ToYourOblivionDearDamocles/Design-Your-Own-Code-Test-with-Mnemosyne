from __future__ import annotations

"""Problem catalog table, tag filters, search, delete, and tag helpers."""

PROBLEM_LIST_SCRIPT = r"""    function renderCatalog() {
      renderTagFilters();
      renderProblemCatalog();
    }

    function renderTagFilters() {
      const box = document.getElementById('tagFilters');
      const total = allProblems.length;
      const rows = [
        {tag: '', label: 'All', count: total},
        ...tagSummaries.map(item => ({tag: item.tag, label: item.tag, count: item.count}))
      ];

      box.innerHTML = rows.map(item => {
        const active = item.tag === activeCatalogTag ? ' active' : '';
        return `
          <button class="tag-filter${active}" onclick="selectCatalogTag('${escapeJs(item.tag)}')">
            <span>${escapeHtml(item.label)}</span>
            <span class="tag-filter-count">${escapeHtml(item.count)}</span>
          </button>
        `;
      }).join('');
    }

    function renderProblemCatalog() {
      const tagged = activeCatalogTag
        ? allProblems.filter(problem => (problem.tags || []).includes(activeCatalogTag))
        : allProblems;
      const list = catalogSearchQuery
        ? tagged.filter(problem => problemMatchesCatalogSearch(problem, catalogSearchQuery))
        : tagged;

      const title = activeCatalogTag ? `Tag: ${activeCatalogTag}` : 'All problems';
      document.getElementById('catalogTitle').textContent = title;
      document.getElementById('catalogCount').textContent = `${list.length} problem${list.length === 1 ? '' : 's'}`;
      renderCatalogSearchState();
      renderCatalogNotice(list.length);

      const box = document.getElementById('problemCatalog');
      if (!list.length) {
        box.innerHTML = '<div class="empty">No problems match this filter.</div>';
        return;
      }

      const rows = list.map((problem, idx) => {
        const tags = (problem.tags || []).map(tag => renderClickableTag(tag)).join('');
        const rowId = String(idx + 1).padStart(4, '0');
        return `
          <tr class="problem-row">
            <td class="catalog-id">${escapeHtml(rowId)}</td>
            <td>
              <button class="catalog-title-button" onclick="openCatalogProblem('${escapeJs(problem.id)}')">${escapeHtml(problem.title)}</button>
              <div class="catalog-subtitle">${escapeHtml(problem.id)} · ${escapeHtml(problem.entry_kind || 'function')}</div>
            </td>
            <td><span class="badge difficulty">${escapeHtml(problem.difficulty || 'unknown')}</span></td>
            <td><div class="problem-card-meta">${tags}</div></td>
            <td class="catalog-actions">
              <button class="icon-button" title="Practice" onclick="openCatalogProblem('${escapeJs(problem.id)}')"><span class="material-symbols-outlined" aria-hidden="true">play_arrow</span></button>
              <button class="icon-button" title="Manage" onclick="openCatalogProblemManager('${escapeJs(problem.id)}', event)"><span class="material-symbols-outlined" aria-hidden="true">edit</span></button>
              <button class="icon-button danger" title="Delete" onclick="deleteCatalogProblem('${escapeJs(problem.id)}', event)"><span class="material-symbols-outlined" aria-hidden="true">delete</span></button>
            </td>
          </tr>
        `;
      }).join('');
      box.innerHTML = `
        <table class="catalog-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Title</th>
              <th>Difficulty</th>
              <th>Tags</th>
              <th class="catalog-actions-head">Actions</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      `;
    }

    function renderCatalogSearchState() {
      const input = document.getElementById('catalogSearch');
      if (input && input.value !== catalogSearchQuery) {
        input.value = catalogSearchQuery;
      }
    }

    function renderCatalogNotice(count) {
      const box = document.getElementById('catalogNotice');
      const search = catalogSearchQuery ? ` matching <strong>${escapeHtml(catalogSearchQuery)}</strong>` : '';
      if (!activeCatalogTag) {
        box.hidden = false;
        box.innerHTML = catalogSearchQuery
          ? `Showing <strong>${escapeHtml(count)}</strong> problem${count === 1 ? '' : 's'}${search}. Clear search to see all problems.`
          : 'Click any tag to filter the problem list, or search by title, id, difficulty, type, or tag.';
        return;
      }
      box.hidden = false;
      box.innerHTML = `Showing <strong>${escapeHtml(count)}</strong> problem${count === 1 ? '' : 's'} tagged <strong>${escapeHtml(activeCatalogTag)}</strong>${search}. Click <strong>All</strong> to clear the tag filter.`;
    }

    function selectCatalogTag(tag) {
      activeCatalogTag = tag;
      renderCatalog();
    }

    async function openCatalogProblem(problemId) {
      await loadProblem(problemId);
      setAppMode('practice');
      setView('code');
    }

    async function openCatalogProblemManager(problemId, event = null) {
      if (event) event.stopPropagation();
      await selectManagerProblem(problemId);
      setAppMode('manage');
    }

    function setCatalogSearch(value) {
      catalogSearchQuery = String(value || '').trim().toLowerCase();
      renderProblemCatalog();
    }

    function clearCatalogSearch() {
      catalogSearchQuery = '';
      renderProblemCatalog();
    }

    function problemMatchesCatalogSearch(problem, query) {
      const haystack = [
        problem.id,
        problem.slug,
        problem.title,
        problem.difficulty,
        problem.entry_kind,
        ...(problem.tags || []),
      ].join(' ').toLowerCase();
      return query.split(/\s+/).filter(Boolean).every(term => haystack.includes(term));
    }

    function renderClickableTag(tag) {
      return `<button type="button" class="tag tag-click" onclick="openTag('${escapeJs(tag)}', event)">${escapeHtml(tag)}</button>`;
    }

    function openTag(tag, event = null) {
      if (event) event.stopPropagation();
      activeCatalogTag = tag;
      setAppMode('problems');
      renderCatalog();
    }

    async function deleteCatalogProblem(problemId, event) {
      event.stopPropagation();
      if (!confirm(`Delete problem "${problemId}"? This removes it from the local problem bank.`)) return;
      const res = await fetch(`/api/problems/${encodeURIComponent(problemId)}`, {method: 'DELETE'});
      const result = await res.json();
      await refreshProblemIndex();
      if (result.ok && result.deleted && currentProblem?.id === problemId) {
        if (allProblems.length) {
          await loadProblem(allProblems[0].id);
        } else {
          currentProblem = null;
          document.getElementById('problemSelect').innerHTML = '';
          document.getElementById('title').textContent = '';
          document.getElementById('meta').innerHTML = '';
          document.getElementById('statement').innerHTML = '<div class="empty">No problems left.</div>';
          document.getElementById('theoryContent').innerHTML = '';
          document.getElementById('exampleContent').innerHTML = '';
          document.getElementById('learningSolutionContent').innerHTML = '';
          const dependencyStatus = document.getElementById('dependencyStatus');
          if (dependencyStatus) dependencyStatus.innerHTML = '';
        }
      }
      renderCatalogDeleteResult(result, problemId);
    }

    function renderCatalogDeleteResult(result, problemId) {
      const box = document.getElementById('catalogNotice');
      box.hidden = false;
      if (result.ok && result.deleted) {
        box.innerHTML = `Deleted <strong>${escapeHtml(problemId)}</strong>.`;
        return;
      }
      const message = result.errors?.length ? result.errors.map(sanitizeLocalPaths).join(' ') : 'Could not delete problem.';
      box.innerHTML = `<span class="status-text wrong">${escapeHtml(message)}</span>`;
    }

    async function editCatalogProblemTags(problemId, event) {
      event.stopPropagation();
      const summary = allProblems.find(problem => problem.id === problemId);
      const current = (summary?.tags || []).join(', ');
      const input = prompt('Edit tags for this problem. Use commas between tags.', current);
      if (input === null) return;
      const tags = parseTagsInput(input);
      const result = await saveProblemTags(problemId, tags);
      if (result.ok && result.saved) {
        await refreshProblemIndex();
        if (currentProblem?.id === problemId) {
          await loadProblem(problemId);
        }
      }
      renderCatalogTagSaveResult(result, problemId);
    }

    function renderCatalogTagSaveResult(result, problemId) {
      const box = document.getElementById('catalogNotice');
      box.hidden = false;
      if (result.ok && result.saved) {
        box.innerHTML = `Tags saved for <strong>${escapeHtml(problemId)}</strong>.`;
        return;
      }
      const message = result.errors?.length ? result.errors.map(sanitizeLocalPaths).join(' ') : 'Could not save tags.';
      box.innerHTML = `<span class="status-text wrong">${escapeHtml(message)}</span>`;
    }

    function parseTagsInput(input) {
      const seen = new Set();
      const tags = String(input || '')
        .split(/[,\n]+/)
        .map(tag => tag.trim().toLowerCase().replace(/\s+/g, '_'))
        .filter(Boolean)
        .filter(tag => {
          if (seen.has(tag)) return false;
          seen.add(tag);
          return true;
        });
      return tags;
    }

    async function saveProblemTags(problemId, tags) {
      const res = await fetch(`/api/problems/${encodeURIComponent(problemId)}/raw`);
      const data = await res.json();
      const problem = data.problem;
      if (!problem) {
        return {ok: false, saved: false, errors: ['Problem not found.']};
      }
      problem.tags = tags;
      return await postJson(`/api/problems/${encodeURIComponent(problemId)}`, {
        content: stringifyProblemJson(problem)
      }, 'PUT');
    }

"""
