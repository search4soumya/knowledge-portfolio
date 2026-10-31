const XLINK = 'http://www.w3.org/1999/xlink';
const PAD = 40;

function download(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

const stamp = () => new Date().toISOString().slice(0, 16).replace(/[:T]/g, '-');
const canvasBackground = () => getComputedStyle(document.documentElement).getPropertyValue('--canvas-bg').trim() || '#ffffff';

export async function buildSvg(editor, svg) {
  const bounds = editor.contentBounds();
  if (!bounds) throw new Error('The canvas is empty.');
  await editor.ensureIcons();
  const restoreSelection = editor.clearSelectionForExport();
  const clone = svg.cloneNode(true);
  restoreSelection();

  clone.querySelectorAll('#grid, #marquee, #grid-dots, .port, .select-ring, .hit, .temp-edge').forEach((n) => n.remove());
  for (const attr of ['id', 'class', 'tabindex', 'aria-label', 'style']) clone.removeAttribute(attr);
  clone.querySelectorAll('[class]').forEach((n) => n.removeAttribute('class'));
  clone.querySelectorAll('[data-id], [data-port]').forEach((n) => {
    n.removeAttribute('data-id');
    n.removeAttribute('data-port');
  });
  clone.querySelector('#viewport')?.removeAttribute('transform');
  clone.querySelectorAll('image').forEach((img) => img.setAttributeNS(XLINK, 'xlink:href', img.getAttribute('href')));

  const x = Math.floor(bounds.x - PAD);
  const y = Math.floor(bounds.y - PAD);
  const width = Math.ceil(bounds.width + PAD * 2);
  const height = Math.ceil(bounds.height + PAD * 2);
  clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
  clone.setAttribute('xmlns:xlink', XLINK);
  clone.setAttribute('viewBox', `${x} ${y} ${width} ${height}`);
  clone.setAttribute('width', width);
  clone.setAttribute('height', height);

  const bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
  bg.setAttribute('x', x);
  bg.setAttribute('y', y);
  bg.setAttribute('width', width);
  bg.setAttribute('height', height);
  bg.setAttribute('fill', canvasBackground());
  clone.querySelector('defs').after(bg);

  return { text: new XMLSerializer().serializeToString(clone), width, height };
}

export async function exportSvg(editor, svg) {
  const { text } = await buildSvg(editor, svg);
  download(new Blob([text], { type: 'image/svg+xml' }), `architecture-${stamp()}.svg`);
}

export async function exportPng(editor, svg, scale = 2) {
  const { text, width, height } = await buildSvg(editor, svg);
  const img = new Image();
  img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(text);
  await img.decode();
  const canvas = document.createElement('canvas');
  canvas.width = width * scale;
  canvas.height = height * scale;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = canvasBackground();
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
  const blob = await new Promise((resolve, reject) => canvas.toBlob((b) => (b ? resolve(b) : reject(new Error('PNG encoding failed'))), 'image/png'));
  download(blob, `architecture-${stamp()}.png`);
}

export function saveJson(editor) {
  const text = JSON.stringify(editor.getData(), null, 2);
  download(new Blob([text], { type: 'application/json' }), `architecture-${stamp()}.json`);
}

export async function openJson(editor, file) {
  const data = JSON.parse(await file.text());
  editor.replaceDoc(data);
}
