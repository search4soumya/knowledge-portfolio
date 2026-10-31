const BADGES = {
  general: { text: 'GEN', bg: '#6d28d9' },
  platforms: { text: 'OSS', bg: '#0d9488' },
  aws: { text: 'AWS', bg: '#232f3e' },
  azure: { text: 'AZ', bg: '#0078d4' },
  gcp: { text: 'GC', bg: '#4285f4' },
};

const SEARCH_LIMIT = 240;
const CHEVRON = '<svg class="chevron" viewBox="0 0 24 24"><path d="m9 6 6 6-6 6"/></svg>';

export const DRAG_TYPE = 'application/x-blueprint-icon';

const escapeHtml = (s) => s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);

export function createPalette({ container, countEl, catalog, onAdd }) {
  const byId = new Map(catalog.icons.map((icon) => [icon.id, icon]));
  const providerLabel = new Map(catalog.providers.map((p) => [p.id, p.label]));
  const haystack = new Map(
    catalog.icons.map((icon) => [
      icon.id,
      [icon.name, icon.category, providerLabel.get(icon.provider), icon.kind, ...(icon.keywords ?? [])]
        .filter(Boolean)
        .join(' ')
        .toLowerCase(),
    ]),
  );

  const openProviders = new Set(['general']);
  let openCategory = 'general|Actors & Clients';
  let query = '';

  countEl.textContent = `${catalog.icons.length.toLocaleString()} icons`;

  function iconItem(icon) {
    // Absolute URL: a relative url() inside a custom property resolves against the stylesheet, not the page.
    const thumb = icon.mono
      ? `<span class="mask" style="--src:url('${new URL(icon.path, document.baseURI).href}');--tint:${icon.color ?? 'var(--accent)'}"></span>`
      : `<img src="${icon.path}" alt="" loading="lazy" decoding="async" draggable="false">`;
    const title = `${icon.name}\n${providerLabel.get(icon.provider)} / ${icon.category}\nDrag to the canvas, or double-click to add`;
    return `<div class="icon-item" draggable="true" tabindex="0" data-id="${escapeHtml(icon.id)}" title="${escapeHtml(title)}">
      <span class="icon-thumb">${thumb}</span>
      <span class="icon-name">${escapeHtml(icon.name)}</span>
    </div>`;
  }

  function renderTree() {
    const html = catalog.providers
      .map((p) => {
        const badge = BADGES[p.id] ?? { text: p.label.slice(0, 2).toUpperCase(), bg: '#6b7280' };
        const total = p.categories.reduce((n, c) => n + c.count, 0);
        const expanded = openProviders.has(p.id);
        const cats = expanded
          ? `<div class="category-list">${p.categories
              .map((c) => {
                const key = `${p.id}|${c.name}`;
                const open = key === openCategory;
                const grid = open
                  ? `<div class="icon-grid">${catalog.icons
                      .filter((i) => i.provider === p.id && i.category === c.name)
                      .map(iconItem)
                      .join('')}</div>`
                  : '';
                return `<button type="button" class="category-head" data-category="${escapeHtml(key)}" aria-expanded="${open}">
                    <span>${escapeHtml(c.name)}</span><span class="count">${c.count}</span>${CHEVRON}
                  </button>${grid}`;
              })
              .join('')}</div>`
          : '';
        return `<section class="provider">
          <button type="button" class="provider-head" data-provider="${p.id}" aria-expanded="${expanded}">
            <span class="provider-badge" style="background:${badge.bg}">${badge.text}</span>
            <span>${escapeHtml(p.label)}</span><span class="count">${total}</span>${CHEVRON}
          </button>${cats}
        </section>`;
      })
      .join('');
    container.innerHTML = html;
  }

  function renderSearch() {
    const words = query.toLowerCase().split(/\s+/).filter(Boolean);
    const q = query.toLowerCase().trim();
    const hits = catalog.icons
      .filter((icon) => {
        const text = haystack.get(icon.id);
        return words.every((w) => text.includes(w));
      })
      .map((icon) => {
        const name = icon.name.toLowerCase();
        const score = name === q ? 0 : name.startsWith(q) ? 1 : name.includes(q) ? 2 : 3;
        return { icon, score };
      })
      .sort((a, b) => a.score - b.score || a.icon.name.length - b.icon.name.length);

    if (!hits.length) {
      container.innerHTML = `<div class="palette-note">No icons match "<strong>${escapeHtml(query)}</strong>".</div>`;
      return;
    }

    const shown = hits.slice(0, SEARCH_LIMIT);
    const groups = new Map();
    for (const { icon } of shown) {
      const key = providerLabel.get(icon.provider);
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(icon);
    }
    let html = '';
    for (const p of catalog.providers) {
      const list = groups.get(p.label);
      if (!list) continue;
      html += `<div class="search-group">${escapeHtml(p.label)} · ${list.length}</div><div class="icon-grid">${list.map(iconItem).join('')}</div>`;
    }
    if (hits.length > shown.length) {
      html += `<div class="palette-note">Showing the first ${SEARCH_LIMIT} of ${hits.length} matches. Refine the search to see more.</div>`;
    }
    container.innerHTML = html;
  }

  function render() {
    if (query.trim()) renderSearch();
    else renderTree();
  }

  container.addEventListener('click', (e) => {
    const prov = e.target.closest('[data-provider]');
    if (prov) {
      const id = prov.dataset.provider;
      if (openProviders.has(id)) openProviders.delete(id);
      else openProviders.add(id);
      render();
      return;
    }
    const cat = e.target.closest('[data-category]');
    if (cat) {
      const key = cat.dataset.category;
      openCategory = openCategory === key ? null : key;
      const top = cat.getBoundingClientRect().top;
      render();
      // Keep the clicked header under the cursor when a group above it collapses.
      const again = container.querySelector(`[data-category="${CSS.escape(key)}"]`);
      if (again) container.scrollTop += again.getBoundingClientRect().top - top;
    }
  });

  container.addEventListener('dblclick', (e) => {
    const item = e.target.closest('.icon-item');
    if (item) onAdd(byId.get(item.dataset.id));
  });

  container.addEventListener('keydown', (e) => {
    const item = e.target.closest('.icon-item');
    if (item && e.key === 'Enter') onAdd(byId.get(item.dataset.id));
  });

  container.addEventListener('dragstart', (e) => {
    const item = e.target.closest('.icon-item');
    if (!item) return;
    e.dataTransfer.setData(DRAG_TYPE, item.dataset.id);
    e.dataTransfer.setData('text/plain', byId.get(item.dataset.id)?.name ?? '');
    e.dataTransfer.effectAllowed = 'copy';
    const thumb = item.querySelector('.icon-thumb');
    if (thumb) e.dataTransfer.setDragImage(thumb, 20, 20);
  });

  render();

  return {
    get: (id) => byId.get(id),
    setQuery(value) {
      query = value;
      container.scrollTop = 0;
      render();
    },
    focusFirst() {
      container.querySelector('.icon-item')?.focus();
    },
  };
}
