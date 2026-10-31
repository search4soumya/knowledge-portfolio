import { createPalette, DRAG_TYPE } from './palette.js';
import { createEditor } from './editor.js';
import { exportPng, exportSvg, openJson, saveJson } from './io.js';

const $ = (sel) => document.querySelector(sel);
const THEME_KEY = 'blueprint-designer:theme';
const initialTheme = localStorage.getItem(THEME_KEY) === 'dark' ? 'dark' : 'light';
document.documentElement.dataset.theme = initialTheme;

let toastTimer = 0;
function toast(message) {
  let node = $('.toast');
  if (!node) {
    node = document.createElement('div');
    node.className = 'toast';
    document.body.appendChild(node);
  }
  node.textContent = message;
  node.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (node.hidden = true), 2800);
}

const svg = $('#canvas');
const stage = $('#stage');

const editor = createEditor({
  svg,
  stage,
  inspector: $('#inspector'),
  emptyHint: $('#empty-hint'),
  zoomLabel: $('#zoom-label'),
  toast,
});

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem(THEME_KEY, theme);
  const dark = theme === 'dark';
  const button = $('#theme-button');
  button.setAttribute('aria-pressed', String(dark));
  button.title = dark ? 'Switch to light theme' : 'Switch to dark theme';
  $('#theme-label').textContent = dark ? 'Light' : 'Dark';
  editor.refresh();
}
applyTheme(initialTheme);

let palette = null;

async function loadCatalog() {
  const container = $('#palette');
  try {
    const res = await fetch('data/catalog.json');
    if (!res.ok) throw new Error(res.status);
    const catalog = await res.json();
    palette = createPalette({
      container,
      countEl: $('#palette-count'),
      catalog,
      onAdd: (icon) => editor.addIcon(icon),
    });
  } catch {
    container.innerHTML = `<div class="palette-note">The icon catalog could not be loaded. Serve the site over HTTP (for example <code>python -m http.server</code> from the <code>site</code> folder) so the browser can read <code>data/catalog.json</code>.</div>`;
  }
}

/* search */
const search = $('#search');
let searchTimer = 0;
search.addEventListener('input', () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => palette?.setQuery(search.value), 120);
});
$('#search-form').addEventListener('submit', (e) => {
  e.preventDefault();
  palette?.setQuery(search.value);
  palette?.focusFirst();
});
window.addEventListener('keydown', (e) => {
  if (e.key === '/' && !e.target.closest('input, textarea')) {
    e.preventDefault();
    search.focus();
    search.select();
  }
});

/* drag from palette onto canvas */
stage.addEventListener('dragover', (e) => {
  if (!e.dataTransfer.types.includes(DRAG_TYPE)) return;
  e.preventDefault();
  e.dataTransfer.dropEffect = 'copy';
  stage.classList.add('drop-target');
});
stage.addEventListener('dragleave', (e) => {
  if (!stage.contains(e.relatedTarget)) stage.classList.remove('drop-target');
});
stage.addEventListener('drop', (e) => {
  stage.classList.remove('drop-target');
  const id = e.dataTransfer.getData(DRAG_TYPE);
  if (!id || !palette) return;
  e.preventDefault();
  editor.addIconAt(palette.get(id), e.clientX, e.clientY);
});

/* toolbar */
const fileInput = $('#open-file');
async function run(label, fn) {
  try {
    await fn();
  } catch (err) {
    toast(`${label} failed: ${err.message}`);
  }
}

const actions = {
  undo: () => editor.undo(),
  redo: () => editor.redo(),
  delete: () => editor.deleteSelection(),
  theme: () => applyTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'),
  roadmap: () => editor.arrange('roadmap'),
  flow: () => editor.arrange('flow'),
  save: () => saveJson(editor),
  open: () => fileInput.click(),
  'export-svg': () => run('SVG export', () => exportSvg(editor, svg)),
  'export-png': () => run('PNG export', () => exportPng(editor, svg)),
  'zoom-in': () => editor.zoomIn(),
  'zoom-out': () => editor.zoomOut(),
  'zoom-reset': () => editor.resetZoom(),
  'zoom-fit': () => editor.fit(),
};

document.addEventListener('click', (e) => {
  const btn = e.target.closest('[data-action]');
  if (btn && actions[btn.dataset.action]) actions[btn.dataset.action]();
});

fileInput.addEventListener('change', () => {
  const file = fileInput.files[0];
  fileInput.value = '';
  if (file) run('Open', () => openJson(editor, file));
});

window.addEventListener('keydown', (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
    e.preventDefault();
    saveJson(editor);
  }
});

function syncHistoryButtons() {
  $('[data-action="undo"]').disabled = !editor.canUndo();
  $('[data-action="redo"]').disabled = !editor.canRedo();
}
editor.onChange(syncHistoryButtons);
syncHistoryButtons();

loadCatalog();
