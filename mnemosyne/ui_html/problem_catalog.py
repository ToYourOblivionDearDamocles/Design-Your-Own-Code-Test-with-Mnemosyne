from __future__ import annotations

CATALOG_VIEW = r"""<div id="catalogView" class="view" hidden>
        <div class="catalog-layout">
          <div class="catalog-main">
            <div class="catalog-head">
              <h2 id="catalogTitle" class="catalog-title">Problem Catalog</h2>
              <span id="catalogCount" class="badge">0 problems</span>
            </div>
            <div class="catalog-search-row">
              <div class="catalog-search">
                <span class="material-symbols-outlined" aria-hidden="true">search</span>
                <input id="catalogSearch" class="text-input" placeholder="Search problems, IDs, or tags..." oninput="setCatalogSearch(this.value)" />
              </div>
              <button class="small icon-label-button" onclick="clearCatalogSearch()"><span class="material-symbols-outlined" aria-hidden="true">filter_list</span><span>Filters</span></button>
              <button class="small icon-label-button" onclick="renderProblemCatalog()"><span class="material-symbols-outlined" aria-hidden="true">sort</span><span>Sort</span></button>
            </div>
            <aside class="catalog-sidebar">
              <div class="catalog-sidebar-head">Tags:</div>
              <div id="tagFilters"></div>
            </aside>
            <div id="catalogNotice" class="catalog-notice" hidden></div>
            <div id="problemCatalog" class="problem-grid"></div>
          </div>
        </div>
      </div>

      """
