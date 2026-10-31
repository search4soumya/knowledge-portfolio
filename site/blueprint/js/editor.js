const NS = 'http://www.w3.org/2000/svg';
const STORAGE_KEY = 'blueprint-designer:v1';
const ACCENT = '#6d28d9';
const INK = '#111827';
const SPINE = '#b4bac4';
const FONT = 'Inter, "Segoe UI", system-ui, -apple-system, Arial, sans-serif';
const HISTORY_LIMIT = 100;
const ROUTE_GAP = 14;
const ROUTE_LANE = 18;

export const TILE_COLORS = ['#7c3aed', '#0d9488', '#4f46e5', '#e11d48', '#059669', '#ea580c', '#0284c7', '#1f2937'];

const uid = (p) => `${p}${Date.now().toString(36)}${Math.random().toString(36).slice(2, 7)}`;
const emptyDoc = () => ({ version: 1, nodes: [], edges: [], spines: [] });

function el(tag, attrs = {}, parent) {
  const node = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) if (v !== undefined && v !== null) node.setAttribute(k, v);
  if (parent) parent.appendChild(node);
  return node;
}

function box(node) {
  const s = node.scale || 1;
  if (node.style === 'dot') return { hw: 11 * s, hh: 11 * s };
  if (node.style === 'tile') return { hw: 32 * s, hh: 32 * s };
  return { hw: 42 * s, hh: 42 * s };
}

function wrapLabel(text, maxChars) {
  const words = text.split(/\s+/).filter(Boolean);
  const lines = [];
  let line = '';
  for (const w of words) {
    if (!line) line = w;
    else if ((line + ' ' + w).length <= maxChars) line += ' ' + w;
    else {
      lines.push(line);
      line = w;
    }
  }
  if (line) lines.push(line);
  if (lines.length > 3) {
    lines.length = 3;
    lines[2] = lines[2].replace(/.{0,2}$/, '') + '…';
  }
  return lines;
}

/* ---------- icon data (data URLs keep exports self-contained) ---------- */

const svgTextCache = new Map();
const dataUrlCache = new Map();

function loadSvgText(path) {
  if (!svgTextCache.has(path)) {
    svgTextCache.set(
      path,
      fetch(path)
        .then((r) => (r.ok ? r.text() : Promise.reject(new Error(r.status))))
        .catch(() => '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="3" fill="none" stroke="#9ca3af" stroke-width="2" stroke-dasharray="3 3"/></svg>'),
    );
  }
  return svgTextCache.get(path);
}

function glyphColor(node) {
  if (!node.icon?.mono) return null;
  if (node.style === 'tile') return '#ffffff';
  return node.icon.color || ACCENT;
}

function themeColors() {
  const dark = document.documentElement.dataset.theme === 'dark';
  return dark
    ? { canvas: '#07090d', card: '#171b24', cardStroke: '#343b49', text: '#f3f4f6', line: '#ffffff' }
    : { canvas: '#ffffff', card: '#ffffff', cardStroke: '#eceef2', text: INK, line: ACCENT };
}

function iconKey(node) {
  return `${node.icon.path}|${glyphColor(node) ?? ''}`;
}

async function resolveIcon(node) {
  const key = iconKey(node);
  if (dataUrlCache.has(key)) return dataUrlCache.get(key);
  let text = await loadSvgText(node.icon.path);
  const color = glyphColor(node);
  if (color) text = text.replace(/currentColor/g, color);
  const url = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(text);
  dataUrlCache.set(key, url);
  return url;
}

/* ---------- editor ---------- */

export function createEditor({ svg, stage, inspector, emptyHint, zoomLabel, toast }) {
  const viewport = svg.querySelector('#viewport');
  const layers = {
    spines: svg.querySelector('#layer-spines'),
    edges: svg.querySelector('#layer-edges'),
    nodes: svg.querySelector('#layer-nodes'),
    overlay: svg.querySelector('#layer-overlay'),
  };
  const marquee = svg.querySelector('#marquee');

  let doc = emptyDoc();
  let view = { x: 0, y: 0, k: 1 };
  let selection = new Set();
  const undoStack = [];
  const redoStack = [];
  let listeners = [];

  const nodeById = (id) => doc.nodes.find((n) => n.id === id);

  /* ----- persistence & history ----- */

  let saveTimer = 0;
  function persist() {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(() => {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify({ doc, view }));
      } catch {
        /* storage full or disabled: autosave is best-effort */
      }
    }, 250);
  }

  function snapshot() {
    return JSON.stringify(doc);
  }

  function pushHistory(before) {
    if (before === snapshot()) return;
    undoStack.push(before);
    if (undoStack.length > HISTORY_LIMIT) undoStack.shift();
    redoStack.length = 0;
    changed();
  }

  function commit(mutate) {
    const before = snapshot();
    mutate();
    pushHistory(before);
    render();
  }

  function changed() {
    persist();
    listeners.forEach((fn) => fn());
  }

  function restore(json) {
    doc = JSON.parse(json);
    const ids = new Set([...doc.nodes, ...doc.edges, ...doc.spines].map((o) => o.id));
    selection = new Set([...selection].filter((id) => ids.has(id)));
    render();
    changed();
  }

  function undo() {
    if (!undoStack.length) return;
    redoStack.push(snapshot());
    restore(undoStack.pop());
  }

  function redo() {
    if (!redoStack.length) return;
    undoStack.push(snapshot());
    restore(redoStack.pop());
  }

  /* ----- view ----- */

  function applyView() {
    viewport.setAttribute('transform', `translate(${view.x} ${view.y}) scale(${view.k})`);
    zoomLabel.textContent = `${Math.round(view.k * 100)}%`;
    persist();
  }

  function toWorld(clientX, clientY) {
    const r = svg.getBoundingClientRect();
    return { x: (clientX - r.left - view.x) / view.k, y: (clientY - r.top - view.y) / view.k };
  }

  function zoomAt(factor, clientX, clientY) {
    const r = svg.getBoundingClientRect();
    const cx = clientX ?? r.left + r.width / 2;
    const cy = clientY ?? r.top + r.height / 2;
    const k = Math.min(3, Math.max(0.2, view.k * factor));
    const p = toWorld(cx, cy);
    view.k = k;
    view.x = cx - r.left - p.x * k;
    view.y = cy - r.top - p.y * k;
    applyView();
  }

  function contentBounds() {
    const items = [...doc.nodes, ...doc.spines];
    if (!items.length) return null;
    let x1 = Infinity, y1 = Infinity, x2 = -Infinity, y2 = -Infinity;
    for (const n of doc.nodes) {
      const { hw, hh } = box(n);
      const labelSpace = n.style === 'dot' ? 0 : 60 * (n.scale || 1);
      x1 = Math.min(x1, n.x - Math.max(hw, 80));
      x2 = Math.max(x2, n.x + Math.max(hw, 80));
      y1 = Math.min(y1, n.y - hh - (n.labelPos === 'top' ? labelSpace : 0));
      y2 = Math.max(y2, n.y + hh + (n.labelPos === 'top' ? 0 : labelSpace));
    }
    for (const s of doc.spines) {
      x1 = Math.min(x1, s.x1);
      x2 = Math.max(x2, s.x2 + 12);
      y1 = Math.min(y1, s.y - 12);
      y2 = Math.max(y2, s.y + 12);
    }
    return { x: x1, y: y1, width: x2 - x1, height: y2 - y1 };
  }

  function fit() {
    const b = contentBounds();
    const r = svg.getBoundingClientRect();
    if (!b) {
      view = { x: r.width / 2, y: r.height / 2, k: 1 };
      applyView();
      return;
    }
    const pad = 70;
    const k = Math.min(1.4, Math.max(0.2, Math.min((r.width - pad * 2) / b.width, (r.height - pad * 2) / b.height)));
    view = { k, x: r.width / 2 - (b.x + b.width / 2) * k, y: r.height / 2 - (b.y + b.height / 2) * k };
    applyView();
  }

  /* ----- rendering ----- */

  let renderQueued = false;
  function scheduleRender() {
    if (renderQueued) return;
    renderQueued = true;
    requestAnimationFrame(() => {
      renderQueued = false;
      render();
    });
  }

  function clipPoint(node, tx, ty) {
    const { hw, hh } = box(node);
    const dx = tx - node.x;
    const dy = ty - node.y;
    if (!dx && !dy) return { x: node.x, y: node.y };
    const pad = node.style === 'dot' ? 0 : 5;
    const t = Math.min((hw + pad) / Math.abs(dx || 1e-9), (hh + pad) / Math.abs(dy || 1e-9), 1);
    return { x: node.x + dx * t, y: node.y + dy * t };
  }

  function nodeRect(node, pad = 0) {
    const { hw, hh } = box(node);
    return {
      id: node.id,
      left: node.x - hw - pad,
      right: node.x + hw + pad,
      top: node.y - hh - pad,
      bottom: node.y + hh + pad,
    };
  }

  function laneShift(source, target, edgeId, axis) {
    const dx = target.x - source.x;
    const dy = target.y - source.y;
    const horizontal = Math.abs(dx) >= Math.abs(dy);
    if (axis !== (horizontal ? 'y' : 'x')) return 0;
    const sign = horizontal ? Math.sign(dx) || 1 : Math.sign(dy) || 1;
    const siblings = doc.edges
      .filter((edge) => {
        if (edge.kind === 'stem') return false;
        const otherId = edge.from === source.id ? edge.to : edge.to === source.id ? edge.from : null;
        if (!otherId) return false;
        const other = nodeById(otherId);
        if (!other) return false;
        const odx = other.x - source.x;
        const ody = other.y - source.y;
        const otherHorizontal = Math.abs(odx) >= Math.abs(ody);
        if (otherHorizontal !== horizontal) return false;
        const otherSign = otherHorizontal ? Math.sign(odx) || 1 : Math.sign(ody) || 1;
        return otherSign === sign;
      })
      .map((edge) => edge.id)
      .sort();
    const index = siblings.indexOf(edgeId);
    if (index < 0 || siblings.length < 2) return 0;
    return (index - (siblings.length - 1) / 2) * 12;
  }

  function sharedSpan(source, target, axis, shift) {
    const sBox = box(source);
    const tBox = box(target);
    const sHalf = axis === 'y' ? sBox.hh : sBox.hw;
    const tHalf = axis === 'y' ? tBox.hh : tBox.hw;
    const sMargin = Math.min(14, sHalf * 0.5);
    const tMargin = Math.min(14, tHalf * 0.5);
    const lo = Math.max(source[axis] - sHalf + sMargin, target[axis] - tHalf + tMargin);
    const hi = Math.min(source[axis] + sHalf - sMargin, target[axis] + tHalf - tMargin);
    if (hi - lo < 8) return null;
    return Math.max(lo, Math.min(hi, (lo + hi) / 2 + shift));
  }

  function clampToFace(center, half, value) {
    const inset = Math.min(8, half * 0.45);
    return Math.max(center - half + inset, Math.min(center + half - inset, value));
  }

  function anchors(node, sharedX, sharedY, shiftX, shiftY) {
    const { hw, hh } = box(node);
    const pad = 5;
    const x = Math.round(clampToFace(node.x, hw, sharedX ?? node.x + shiftX));
    const y = Math.round(clampToFace(node.y, hh, sharedY ?? node.y + shiftY));
    return [
      {
        side: 'top',
        point: { x, y: node.y - hh - pad },
        lead: { x, y: node.y - hh - pad - ROUTE_GAP },
      },
      {
        side: 'right',
        point: { x: node.x + hw + pad, y },
        lead: { x: node.x + hw + pad + ROUTE_GAP, y },
      },
      {
        side: 'bottom',
        point: { x, y: node.y + hh + pad },
        lead: { x, y: node.y + hh + pad + ROUTE_GAP },
      },
      {
        side: 'left',
        point: { x: node.x - hw - pad, y },
        lead: { x: node.x - hw - pad - ROUTE_GAP, y },
      },
    ];
  }

  function simplifyPath(points) {
    const result = [];
    for (const raw of points) {
      const point = { x: Math.round(raw.x), y: Math.round(raw.y) };
      const previous = result.at(-1);
      if (previous && previous.x === point.x && previous.y === point.y) continue;
      result.push(point);
      while (result.length >= 3) {
        const [a, b, c] = result.slice(-3);
        if ((a.x === b.x && b.x === c.x) || (a.y === b.y && b.y === c.y)) result.splice(-2, 1);
        else break;
      }
    }
    return result;
  }

  function pathData(points) {
    if (points.length < 2) return '';
    const radius = 12;
    let d = `M${points[0].x} ${points[0].y}`;
    for (let i = 1; i < points.length - 1; i++) {
      const prev = points[i - 1];
      const curr = points[i];
      const next = points[i + 1];
      const inLen = Math.hypot(curr.x - prev.x, curr.y - prev.y);
      const outLen = Math.hypot(next.x - curr.x, next.y - curr.y);
      const r = Math.min(radius, inLen / 2, outLen / 2);
      if (r < 1 || inLen < 1 || outLen < 1) {
        d += ` L${curr.x} ${curr.y}`;
        continue;
      }
      const x1 = curr.x - ((curr.x - prev.x) / inLen) * r;
      const y1 = curr.y - ((curr.y - prev.y) / inLen) * r;
      const x2 = curr.x + ((next.x - curr.x) / outLen) * r;
      const y2 = curr.y + ((next.y - curr.y) / outLen) * r;
      d += ` L${x1} ${y1} Q${curr.x} ${curr.y} ${x2} ${y2}`;
    }
    const last = points[points.length - 1];
    return `${d} L${last.x} ${last.y}`;
  }

  function pathSegments(points) {
    return points.slice(1).map((point, index) => ({ a: points[index], b: point }));
  }

  function segmentHitsRect(segment, rect) {
    const { a, b } = segment;
    if (a.x === b.x) {
      return a.x > rect.left && a.x < rect.right && Math.max(a.y, b.y) > rect.top && Math.min(a.y, b.y) < rect.bottom;
    }
    return a.y > rect.top && a.y < rect.bottom && Math.max(a.x, b.x) > rect.left && Math.min(a.x, b.x) < rect.right;
  }

  function segmentConflict(first, second) {
    const aHorizontal = first.a.y === first.b.y;
    const bHorizontal = second.a.y === second.b.y;
    if (aHorizontal === bHorizontal) {
      const sameLane = aHorizontal ? first.a.y === second.a.y : first.a.x === second.a.x;
      if (!sameLane) return { overlap: 0, crossing: false };
      const a1 = aHorizontal ? Math.min(first.a.x, first.b.x) : Math.min(first.a.y, first.b.y);
      const a2 = aHorizontal ? Math.max(first.a.x, first.b.x) : Math.max(first.a.y, first.b.y);
      const b1 = bHorizontal ? Math.min(second.a.x, second.b.x) : Math.min(second.a.y, second.b.y);
      const b2 = bHorizontal ? Math.max(second.a.x, second.b.x) : Math.max(second.a.y, second.b.y);
      return { overlap: Math.max(0, Math.min(a2, b2) - Math.max(a1, b1)), crossing: false };
    }
    const horizontal = aHorizontal ? first : second;
    const vertical = aHorizontal ? second : first;
    const crossing =
      vertical.a.x > Math.min(horizontal.a.x, horizontal.b.x) &&
      vertical.a.x < Math.max(horizontal.a.x, horizontal.b.x) &&
      horizontal.a.y > Math.min(vertical.a.y, vertical.b.y) &&
      horizontal.a.y < Math.max(vertical.a.y, vertical.b.y);
    return { overlap: 0, crossing };
  }

  function sidePreference(side, from, to) {
    const dx = to.x - from.x;
    const dy = to.y - from.y;
    if (Math.abs(dx) >= Math.abs(dy)) return side === (dx >= 0 ? 'right' : 'left') ? 0 : side === 'top' || side === 'bottom' ? 70 : 180;
    return side === (dy >= 0 ? 'bottom' : 'top') ? 0 : side === 'left' || side === 'right' ? 70 : 180;
  }

  function jogImbalance(points, start, finish) {
    const horizontalSide = (side) => side === 'left' || side === 'right';
    if (horizontalSide(start.side) !== horizontalSide(finish.side) || start.side === finish.side) return 0;
    const horizontal = horizontalSide(start.side);
    const mid = horizontal ? (start.point.x + finish.point.x) / 2 : (start.point.y + finish.point.y) / 2;
    let cost = 0;
    for (let i = 1; i < points.length; i++) {
      const a = points[i - 1];
      const b = points[i];
      const jog = horizontal ? a.x === b.x && a.y !== b.y : a.y === b.y && a.x !== b.x;
      if (jog) cost += Math.abs((horizontal ? a.x : a.y) - mid);
    }
    return cost;
  }

  function routeConnector(edge, occupied) {
    const source = nodeById(edge.from);
    const target = nodeById(edge.to);
    if (!source || !target) return null;

    const obstacles = doc.nodes.filter((node) => node.style !== 'dot').map((node) => nodeRect(node, 10));
    const relevant = obstacles.filter(
      (rect) =>
        rect.id !== source.id &&
        rect.id !== target.id &&
        rect.right > Math.min(source.x, target.x) - 80 &&
        rect.left < Math.max(source.x, target.x) + 80 &&
        rect.bottom > Math.min(source.y, target.y) - 80 &&
        rect.top < Math.max(source.y, target.y) + 80,
    );
    const allRects = obstacles.length ? obstacles : [nodeRect(source), nodeRect(target)];
    const outer = {
      left: Math.min(...allRects.map((rect) => rect.left)) - ROUTE_LANE,
      right: Math.max(...allRects.map((rect) => rect.right)) + ROUTE_LANE,
      top: Math.min(...allRects.map((rect) => rect.top)) - ROUTE_LANE,
      bottom: Math.max(...allRects.map((rect) => rect.bottom)) + ROUTE_LANE,
    };

    const shiftX = laneShift(source, target, edge.id, 'x');
    const shiftY = laneShift(source, target, edge.id, 'y');
    const sharedX = sharedSpan(source, target, 'x', shiftX);
    const sharedY = sharedSpan(source, target, 'y', shiftY);
    const sourceAnchors = anchors(source, sharedX, sharedY, shiftX, shiftY);
    const targetAnchors = anchors(target, sharedX, sharedY, 0, 0);

    let best = null;
    for (const start of sourceAnchors) {
      for (const finish of targetAnchors) {
        const xs = new Set([
          (start.lead.x + finish.lead.x) / 2,
          outer.left,
          outer.right,
          ...relevant.flatMap((rect) => [rect.left - ROUTE_LANE, rect.right + ROUTE_LANE]),
        ]);
        const ys = new Set([
          (start.lead.y + finish.lead.y) / 2,
          outer.top,
          outer.bottom,
          ...relevant.flatMap((rect) => [rect.top - ROUTE_LANE, rect.bottom + ROUTE_LANE]),
        ]);
        const middles = [
          [start.lead, finish.lead],
          [start.lead, { x: finish.lead.x, y: start.lead.y }, finish.lead],
          [start.lead, { x: start.lead.x, y: finish.lead.y }, finish.lead],
          ...[...xs].map((x) => [start.lead, { x, y: start.lead.y }, { x, y: finish.lead.y }, finish.lead]),
          ...[...ys].map((y) => [start.lead, { x: start.lead.x, y }, { x: finish.lead.x, y }, finish.lead]),
        ];

        for (const middle of middles) {
          const points = simplifyPath([start.point, ...middle, finish.point]);
          const segments = pathSegments(points);
          if (segments.some((segment) => segment.a.x !== segment.b.x && segment.a.y !== segment.b.y)) continue;

          let score = sidePreference(start.side, source, target) + sidePreference(finish.side, target, source);
          score += Math.max(0, segments.length - 1) * 45;
          score += segments.reduce((sum, segment) => sum + Math.abs(segment.b.x - segment.a.x) + Math.abs(segment.b.y - segment.a.y), 0);
          score += jogImbalance(points, start, finish) * 6;

          for (let index = 0; index < segments.length; index++) {
            const segment = segments[index];
            for (const rect of obstacles) {
              if (rect.id === source.id && index === 0) continue;
              if (rect.id === target.id && index === segments.length - 1) continue;
              if (segmentHitsRect(segment, rect)) score += 1_000_000;
            }
            for (const prior of occupied) {
              for (const existing of prior) {
                const conflict = segmentConflict(segment, existing);
                score += conflict.overlap * 250;
                if (conflict.crossing) score += 900;
              }
            }
          }

          if (!best || score < best.score) best = { points, segments, score };
        }
      }
    }
    return best;
  }

  function renderNode(n) {
    const s = n.scale || 1;
    const { hw, hh } = box(n);
    const theme = themeColors();
    const g = el('g', { class: `node${selection.has(n.id) ? ' selected' : ''}`, 'data-id': n.id, transform: `translate(${n.x} ${n.y})` });

    if (n.style === 'dot') {
      el('circle', { class: 'hit', r: hw + 6, fill: 'transparent' }, g);
      el('circle', { r: 10 * s, fill: theme.canvas, stroke: ACCENT, 'stroke-width': 3 * s }, g);
      el('circle', { r: 4 * s, fill: ACCENT }, g);
      el('circle', { class: 'select-ring', r: hw + 5 }, g);
      return g;
    }

    const lines = wrapLabel(n.label || '', n.style === 'tile' ? 18 : 20);
    const fontSize = (n.style === 'tile' ? 14 : 15) * s;
    const lineH = fontSize * 1.25;
    const labelBlock = lines.length * lineH;

    const hitTop = n.labelPos === 'top' ? -hh - 14 * s - labelBlock : -hh - 8;
    const hitBottom = n.labelPos === 'top' ? hh + 8 : hh + 14 * s + labelBlock;
    const hitHalfW = Math.max(hw + 8, 80 * s);
    el('rect', { class: 'hit', x: -hitHalfW, y: hitTop, width: hitHalfW * 2, height: hitBottom - hitTop, fill: 'transparent' }, g);

    const url = dataUrlCache.get(iconKey(n));
    if (!url) resolveIcon(n).then(scheduleRender);

    if (n.style === 'tile') {
      el('rect', { x: -hw, y: -hh, width: hw * 2, height: hh * 2, rx: 16 * s, fill: n.color || TILE_COLORS[0], filter: 'url(#tile-shadow)' }, g);
      if (n.icon?.mono) {
        const size = hw * 2 * 0.56;
        if (url) el('image', { href: url, x: -size / 2, y: -size / 2, width: size, height: size }, g);
      } else {
        const inner = hw * 2 * 0.74;
        el('rect', { x: -inner / 2, y: -inner / 2, width: inner, height: inner, rx: 11 * s, fill: '#ffffff' }, g);
        const size = hw * 2 * 0.58;
        if (url) el('image', { href: url, x: -size / 2, y: -size / 2, width: size, height: size }, g);
      }
    } else {
      el('rect', { x: -hw, y: -hh, width: hw * 2, height: hh * 2, rx: 16 * s, fill: theme.card, stroke: theme.cardStroke, 'stroke-width': 1, filter: 'url(#card-shadow)' }, g);
      const size = hw * 2 * 0.6;
      if (url) el('image', { href: url, x: -size / 2, y: -size / 2, width: size, height: size }, g);
    }

    if (lines.length) {
      const text = el('text', {
        class: 'label',
        'text-anchor': 'middle',
        'font-family': FONT,
        'font-weight': '800',
        'font-size': fontSize,
        'letter-spacing': n.style === 'tile' ? 0.4 * s : 0,
        fill: theme.text,
      }, g);
      const firstBaseline = n.labelPos === 'top' ? -hh - 12 * s - (lines.length - 1) * lineH : hh + 10 * s + fontSize;
      lines.forEach((line, i) => {
        const t = el('tspan', { x: 0, y: firstBaseline + i * lineH }, text);
        t.textContent = n.style === 'tile' ? line.toUpperCase() : line;
      });
    }

    el('rect', { class: 'select-ring', x: -hw - 6, y: -hh - 6, width: hw * 2 + 12, height: hh * 2 + 12, rx: 18 * s }, g);

    for (const [px, py, side] of [[0, -hh, 'top'], [hw, 0, 'right'], [0, hh, 'bottom'], [-hw, 0, 'left']]) {
      el('circle', { class: 'port', cx: px, cy: py, r: 5.5, 'data-port': side }, g);
    }
    return g;
  }

  function edgePoints(e) {
    const a = nodeById(e.from);
    const b = nodeById(e.to);
    if (!a || !b) return null;
    const p1 = clipPoint(a, b.x, b.y);
    const p2 = clipPoint(b, a.x, a.y);
    return { p1, p2 };
  }

  function renderEdge(e, route) {
    const pts = edgePoints(e);
    if (!pts) return null;
    const d = e.kind === 'stem' ? `M${pts.p1.x} ${pts.p1.y} L${pts.p2.x} ${pts.p2.y}` : pathData(route?.points ?? [pts.p1, pts.p2]);
    const g = el('g', { class: `edge${selection.has(e.id) ? ' selected' : ''}`, 'data-id': e.id });
    el('path', { class: 'hit', d }, g);
    const lineColor = themeColors().line;
    if (e.kind === 'stem') {
      el('path', { class: 'stem', d, stroke: lineColor, 'stroke-width': 2.5, 'stroke-linecap': 'round', fill: 'none' }, g);
    } else {
      el('path', {
        class: 'line',
        d,
        stroke: lineColor,
        'stroke-width': 3,
        'stroke-linecap': 'round',
        fill: 'none',
        'stroke-dasharray': e.dashed ? '8 7' : null,
        'marker-end': e.arrow ? 'url(#arrow-head)' : null,
      }, g);
    }
    return g;
  }

  function renderSpine(sp) {
    const g = el('g', { class: `spine${selection.has(sp.id) ? ' selected' : ''}`, 'data-id': sp.id });
    el('line', { class: 'hit', x1: sp.x1, y1: sp.y, x2: sp.x2, y2: sp.y, stroke: 'transparent', 'stroke-width': 20 }, g);
    el('line', { class: 'spine-line', x1: sp.x1, y1: sp.y, x2: sp.x2, y2: sp.y, stroke: SPINE, 'stroke-width': 6, 'stroke-linecap': 'round', 'marker-end': 'url(#spine-head)' }, g);
    return g;
  }

  function render() {
    document.querySelector('#arrow-head path')?.setAttribute('fill', themeColors().line);
    layers.spines.replaceChildren(...doc.spines.map(renderSpine));
    const occupied = doc.spines.map((spine) => [{ a: { x: spine.x1, y: spine.y }, b: { x: spine.x2, y: spine.y } }]);
    const routes = new Map();
    for (const edge of doc.edges.filter((item) => item.kind !== 'stem')) {
      const route = routeConnector(edge, occupied);
      if (route) {
        routes.set(edge.id, route);
        occupied.push(route.segments);
      }
    }
    layers.edges.replaceChildren(...doc.edges.map((edge) => renderEdge(edge, routes.get(edge.id))).filter(Boolean));
    layers.nodes.replaceChildren(...doc.nodes.map(renderNode));
    emptyHint.hidden = doc.nodes.length > 0 || doc.spines.length > 0;
    renderInspector();
  }

  /* ----- inspector ----- */

  function selectedNodes() {
    return doc.nodes.filter((n) => selection.has(n.id) && n.style !== 'dot');
  }
  function selectedLinks() {
    return doc.edges.filter((e) => selection.has(e.id) && e.kind !== 'stem');
  }

  function renderInspector() {
    const nodes = selectedNodes();
    const links = selectedLinks();
    if (!selection.size) {
      inspector.hidden = true;
      return;
    }
    const all = (list, fn) => list.length && list.every(fn);
    let html = '';
    if (nodes.length) {
      html += `<div class="group"><span class="caption">Style</span>
        <button data-cmd="style:card" class="${all(nodes, (n) => n.style !== 'tile') ? 'on' : ''}">Card</button>
        <button data-cmd="style:tile" class="${all(nodes, (n) => n.style === 'tile') ? 'on' : ''}">Tile</button></div>`;
      html += `<div class="group">${TILE_COLORS.map(
        (c) => `<button class="swatch ${all(nodes, (n) => n.style === 'tile' && n.color === c) ? 'on' : ''}" data-cmd="color:${c}" style="background:${c}" title="Tile color"></button>`,
      ).join('')}</div>`;
      html += `<div class="group"><span class="caption">Label</span>
        <button data-cmd="label:top" class="${all(nodes, (n) => n.labelPos === 'top') ? 'on' : ''}">Top</button>
        <button data-cmd="label:bottom" class="${all(nodes, (n) => n.labelPos !== 'top') ? 'on' : ''}">Bottom</button></div>`;
      html += `<div class="group"><span class="caption">Size</span>
        <button data-cmd="scale:-0.1" title="Smaller">-</button>
        <button data-cmd="scale:0.1" title="Larger">+</button></div>`;
    }
    if (links.length) {
      html += `<div class="group"><span class="caption">Line</span>
        <button data-cmd="arrow" class="${all(links, (e) => e.arrow) ? 'on' : ''}">Arrow</button>
        <button data-cmd="dashed" class="${all(links, (e) => e.dashed) ? 'on' : ''}">Dashed</button>
        <button data-cmd="reverse" title="Reverse direction">Reverse</button></div>`;
    }
    html += `<div class="group">${nodes.length ? '<button data-cmd="duplicate" title="Duplicate (Ctrl+D)">Duplicate</button>' : ''}<button data-cmd="delete" title="Delete (Del)">Delete</button></div>`;
    // Rewriting identical markup would detach a button mid-click.
    if (inspector.dataset.html !== html) {
      inspector.innerHTML = html;
      inspector.dataset.html = html;
    }
    inspector.hidden = false;
  }

  inspector.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-cmd]');
    if (!btn) return;
    const [cmd, arg] = btn.dataset.cmd.split(/:(.*)/s);
    const nodes = selectedNodes();
    const links = selectedLinks();
    if (cmd === 'delete') return deleteSelection();
    if (cmd === 'duplicate') return duplicate();
    commit(() => {
      if (cmd === 'style') nodes.forEach((n) => (n.style = arg));
      if (cmd === 'color') nodes.forEach((n) => ((n.color = arg), (n.style = 'tile')));
      if (cmd === 'label') nodes.forEach((n) => (n.labelPos = arg));
      if (cmd === 'scale') nodes.forEach((n) => (n.scale = Math.round(Math.min(2.5, Math.max(0.5, (n.scale || 1) + Number(arg))) * 10) / 10));
      if (cmd === 'arrow') {
        const on = !links.every((l) => l.arrow);
        links.forEach((l) => (l.arrow = on));
      }
      if (cmd === 'dashed') {
        const on = !links.every((l) => l.dashed);
        links.forEach((l) => (l.dashed = on));
      }
      if (cmd === 'reverse') links.forEach((l) => ([l.from, l.to] = [l.to, l.from]));
    });
  });

  /* ----- mutations ----- */

  function addIcon(icon, at) {
    if (!icon) return;
    let pos = at;
    if (!pos) {
      const r = svg.getBoundingClientRect();
      pos = toWorld(r.left + r.width / 2, r.top + r.height / 2);
      const offset = (doc.nodes.length % 6) * 24;
      pos = { x: pos.x + offset, y: pos.y + offset };
    }
    const node = {
      id: uid('n'),
      icon: { id: icon.id, path: icon.path, mono: !!icon.mono, color: icon.color },
      label: icon.name,
      style: 'card',
      color: TILE_COLORS[doc.nodes.filter((n) => n.style !== 'dot').length % 6],
      labelPos: 'bottom',
      scale: 1,
      x: Math.round(pos.x),
      y: Math.round(pos.y),
    };
    commit(() => {
      doc.nodes.push(node);
      selection = new Set([node.id]);
    });
  }

  function removeRoadmapFor(nodeIds) {
    const stems = doc.edges.filter((e) => e.kind === 'stem' && nodeIds.has(e.from));
    const dotIds = new Set(stems.map((e) => e.to));
    doc.edges = doc.edges.filter((e) => !(e.kind === 'stem' && (nodeIds.has(e.from) || dotIds.has(e.to))));
    doc.nodes = doc.nodes.filter((n) => !dotIds.has(n.id));
    doc.spines = doc.spines.filter((s) => !s.members.some((m) => nodeIds.has(m)));
  }

  function deleteSelection() {
    if (!selection.size) return;
    commit(() => {
      const removed = new Set(doc.nodes.filter((n) => selection.has(n.id)).map((n) => n.id));
      const orphanDots = doc.edges.filter((e) => e.kind === 'stem' && removed.has(e.from)).map((e) => e.to);
      orphanDots.forEach((id) => removed.add(id));
      doc.nodes = doc.nodes.filter((n) => !removed.has(n.id));
      doc.edges = doc.edges.filter((e) => !selection.has(e.id) && !removed.has(e.from) && !removed.has(e.to));
      doc.spines = doc.spines
        .filter((s) => !selection.has(s.id))
        .map((s) => ({ ...s, members: s.members.filter((m) => !removed.has(m)) }))
        .filter((s) => s.members.length);
      selection.clear();
    });
  }

  function duplicate() {
    const nodes = selectedNodes();
    if (!nodes.length) return;
    commit(() => {
      const map = new Map();
      for (const n of nodes) {
        const copy = { ...structuredClone(n), id: uid('n'), x: n.x + 32, y: n.y + 32 };
        map.set(n.id, copy.id);
        doc.nodes.push(copy);
      }
      for (const e of doc.edges.filter((e) => e.kind !== 'stem' && map.has(e.from) && map.has(e.to))) {
        doc.edges.push({ ...e, id: uid('e'), from: map.get(e.from), to: map.get(e.to) });
      }
      selection = new Set(map.values());
    });
  }

  function arrange(kind) {
    const nodes = selectedNodes().sort((a, b) => a.x - b.x);
    if (nodes.length < 2) {
      toast('Select at least two icons first (drag a box around them, or Shift+click).');
      return;
    }
    commit(() => {
      const ids = new Set(nodes.map((n) => n.id));
      removeRoadmapFor(ids);
      const cy = Math.round(nodes.reduce((s, n) => s + n.y, 0) / nodes.length);
      const cx = nodes.reduce((s, n) => s + n.x, 0) / nodes.length;

      if (kind === 'roadmap') {
        const gap = 130;
        const x0 = Math.round(cx - (gap * (nodes.length - 1)) / 2);
        const created = [];
        nodes.forEach((n, i) => {
          const above = i % 2 === 0;
          const x = x0 + i * gap;
          n.x = x;
          n.y = cy + (above ? -130 : 130) * (n.scale || 1);
          n.labelPos = above ? 'top' : 'bottom';
          const dot = { id: uid('d'), style: 'dot', scale: 1, x, y: cy };
          doc.nodes.push(dot);
          doc.edges.push({ id: uid('e'), kind: 'stem', from: n.id, to: dot.id });
          created.push(dot.id);
        });
        const spine = { id: uid('s'), x1: x0 - 70, x2: x0 + gap * (nodes.length - 1) + 90, y: cy, members: nodes.map((n) => n.id) };
        doc.spines.push(spine);
        selection = new Set([...ids, ...created, spine.id]);
      } else {
        const gap = 170;
        const x0 = Math.round(cx - (gap * (nodes.length - 1)) / 2);
        nodes.forEach((n, i) => {
          n.x = x0 + i * gap;
          n.y = cy;
          n.labelPos = 'bottom';
        });
        for (let i = 0; i < nodes.length - 1; i++) {
          const a = nodes[i].id;
          const b = nodes[i + 1].id;
          const exists = doc.edges.some((e) => e.kind !== 'stem' && ((e.from === a && e.to === b) || (e.from === b && e.to === a)));
          if (!exists) doc.edges.push({ id: uid('e'), kind: 'link', from: a, to: b, arrow: false });
        }
      }
    });
  }

  function selectAll() {
    selection = new Set([...doc.nodes, ...doc.edges, ...doc.spines].map((o) => o.id));
    render();
  }

  function nudge(dx, dy) {
    const nodes = doc.nodes.filter((n) => selection.has(n.id));
    const spines = doc.spines.filter((s) => selection.has(s.id));
    if (!nodes.length && !spines.length) return;
    commit(() => {
      nodes.forEach((n) => ((n.x += dx), (n.y += dy)));
      spines.forEach((s) => ((s.x1 += dx), (s.x2 += dx), (s.y += dy)));
    });
  }

  /* ----- label editing ----- */

  function editLabel(node) {
    const r = svg.getBoundingClientRect();
    const sr = stage.getBoundingClientRect();
    const { hh } = box(node);
    const ly = node.labelPos === 'top' ? node.y - hh - 26 : node.y + hh + 22;
    const input = document.createElement('input');
    input.className = 'label-editor';
    input.value = node.label || '';
    const width = 200;
    input.style.width = `${width}px`;
    input.style.left = `${r.left - sr.left + view.x + node.x * view.k - width / 2}px`;
    input.style.top = `${r.top - sr.top + view.y + ly * view.k - 16}px`;
    stage.appendChild(input);
    input.focus();
    input.select();
    let done = false;
    const finish = (save) => {
      if (done) return;
      done = true;
      const value = input.value.trim();
      input.remove();
      if (save && value !== node.label) commit(() => (node.label = value));
      svg.focus();
    };
    input.addEventListener('keydown', (e) => {
      e.stopPropagation();
      if (e.key === 'Enter') finish(true);
      if (e.key === 'Escape') finish(false);
    });
    input.addEventListener('blur', () => finish(true));
  }

  /* ----- pointer interaction ----- */

  let spaceHeld = false;
  let gesture = null;
  let lastPress = { id: null, time: 0, x: 0, y: 0 };

  function updateMarquee(a, b) {
    const x = Math.min(a.x, b.x), y = Math.min(a.y, b.y);
    marquee.setAttribute('x', x);
    marquee.setAttribute('y', y);
    marquee.setAttribute('width', Math.abs(a.x - b.x));
    marquee.setAttribute('height', Math.abs(a.y - b.y));
  }

  svg.addEventListener('pointerdown', (e) => {
    if (e.target.closest('.label-editor')) return;
    svg.focus({ preventScroll: true });
    const world = toWorld(e.clientX, e.clientY);

    if (e.button === 1 || (e.button === 0 && spaceHeld)) {
      e.preventDefault();
      gesture = { type: 'pan', sx: e.clientX, sy: e.clientY, vx: view.x, vy: view.y };
      svg.classList.add('panning');
      svg.setPointerCapture(e.pointerId);
      return;
    }
    if (e.button !== 0) return;

    const port = e.target.closest('.port');
    const nodeEl = e.target.closest('.node');
    const edgeEl = e.target.closest('.edge');
    const spineEl = e.target.closest('.spine');

    if (port && nodeEl) {
      const from = nodeById(nodeEl.dataset.id);
      const temp = el('path', { class: 'temp-edge' }, layers.overlay);
      gesture = { type: 'connect', from, temp, target: null };
      svg.classList.add('connecting');
      svg.setPointerCapture(e.pointerId);
      return;
    }

    const hitId = (nodeEl || edgeEl || spineEl)?.dataset.id;

    // Detected manually: re-rendering on pointerdown detaches the target, so the browser never fires dblclick.
    const now = performance.now();
    const isDouble = nodeEl && lastPress.id === hitId && now - lastPress.time < 400 && Math.hypot(e.clientX - lastPress.x, e.clientY - lastPress.y) < 6;
    lastPress = { id: hitId, time: isDouble ? 0 : now, x: e.clientX, y: e.clientY };
    if (isDouble) {
      const node = nodeById(hitId);
      if (node && node.style !== 'dot') {
        e.preventDefault();
        editLabel(node);
        return;
      }
    }

    if (hitId) {
      if (e.shiftKey) {
        if (selection.has(hitId)) selection.delete(hitId);
        else selection.add(hitId);
      } else if (!selection.has(hitId)) {
        selection = new Set([hitId]);
      }
      render();
      if (edgeEl && !nodeEl) return;
      const moving = doc.nodes.filter((n) => selection.has(n.id));
      const spines = doc.spines.filter((s) => selection.has(s.id));
      gesture = {
        type: 'move',
        start: world,
        before: snapshot(),
        moved: false,
        clicked: e.shiftKey ? null : hitId,
        nodes: moving.map((n) => ({ n, x: n.x, y: n.y })),
        spines: spines.map((s) => ({ s, x1: s.x1, x2: s.x2, y: s.y })),
      };
      svg.setPointerCapture(e.pointerId);
      return;
    }

    if (!e.shiftKey) selection.clear();
    render();
    const r = svg.getBoundingClientRect();
    const local = { x: e.clientX - r.left, y: e.clientY - r.top };
    gesture = { type: 'marquee', start: local, startWorld: world, base: new Set(selection) };
    updateMarquee(local, local);
    marquee.setAttribute('visibility', 'visible');
    svg.setPointerCapture(e.pointerId);
  });

  svg.addEventListener('pointermove', (e) => {
    if (!gesture) return;
    const world = toWorld(e.clientX, e.clientY);

    if (gesture.type === 'pan') {
      view.x = gesture.vx + e.clientX - gesture.sx;
      view.y = gesture.vy + e.clientY - gesture.sy;
      applyView();
    } else if (gesture.type === 'move') {
      const dx = Math.round(world.x - gesture.start.x);
      const dy = Math.round(world.y - gesture.start.y);
      if (!gesture.moved && Math.hypot(dx, dy) < 2) return;
      gesture.moved = true;
      gesture.nodes.forEach(({ n, x, y }) => ((n.x = x + dx), (n.y = y + dy)));
      gesture.spines.forEach(({ s, x1, x2, y }) => ((s.x1 = x1 + dx), (s.x2 = x2 + dx), (s.y = y + dy)));
      scheduleRender();
    } else if (gesture.type === 'connect') {
      const under = document.elementFromPoint(e.clientX, e.clientY)?.closest?.('.node');
      const target = under && under.dataset.id !== gesture.from.id ? nodeById(under.dataset.id) : null;
      layers.nodes.querySelectorAll('.connect-target').forEach((n) => n.classList.remove('connect-target'));
      if (target && target.style !== 'dot') under.classList.add('connect-target');
      gesture.target = target && target.style !== 'dot' ? target : null;
      const end = gesture.target ? { x: gesture.target.x, y: gesture.target.y } : world;
      const startPt = clipPoint(gesture.from, end.x, end.y);
      const endPt = gesture.target ? clipPoint(gesture.target, startPt.x, startPt.y) : world;
      const preview = gesture.target
        ? routeConnector({ id: 'preview', from: gesture.from.id, to: gesture.target.id }, [])
        : {
            points:
              Math.abs(endPt.x - startPt.x) >= Math.abs(endPt.y - startPt.y)
                ? [startPt, { x: endPt.x, y: startPt.y }, endPt]
                : [startPt, { x: startPt.x, y: endPt.y }, endPt],
          };
      gesture.temp.setAttribute('d', pathData(simplifyPath(preview?.points ?? [startPt, endPt])));
    } else if (gesture.type === 'marquee') {
      const r = svg.getBoundingClientRect();
      const local = { x: e.clientX - r.left, y: e.clientY - r.top };
      updateMarquee(gesture.start, local);
      const a = gesture.startWorld;
      const x1 = Math.min(a.x, world.x), x2 = Math.max(a.x, world.x);
      const y1 = Math.min(a.y, world.y), y2 = Math.max(a.y, world.y);
      const inside = (x, y) => x >= x1 && x <= x2 && y >= y1 && y <= y2;
      const next = new Set(gesture.base);
      doc.nodes.forEach((n) => inside(n.x, n.y) && next.add(n.id));
      doc.spines.forEach((s) => inside((s.x1 + s.x2) / 2, s.y) && next.add(s.id));
      doc.edges.forEach((ed) => next.has(ed.from) && next.has(ed.to) && next.add(ed.id));
      selection = next;
      scheduleRender();
    }
  });

  function endGesture() {
    if (!gesture) return;
    const g = gesture;
    gesture = null;
    if (g.type === 'pan') svg.classList.remove('panning');
    if (g.type === 'move' && g.moved) pushHistory(g.before);
    if (g.type === 'move' && !g.moved && g.clicked && selection.size > 1) selection = new Set([g.clicked]);
    if (g.type === 'marquee') marquee.setAttribute('visibility', 'hidden');
    if (g.type === 'connect') {
      g.temp.remove();
      svg.classList.remove('connecting');
      if (g.target) {
        const exists = doc.edges.some((ed) => ed.kind !== 'stem' && ed.from === g.from.id && ed.to === g.target.id);
        if (!exists) {
          commit(() => {
            const edge = { id: uid('e'), kind: 'link', from: g.from.id, to: g.target.id, arrow: true };
            doc.edges.push(edge);
            selection = new Set([edge.id]);
          });
          return;
        }
      }
    }
    render();
  }

  svg.addEventListener('pointerup', endGesture);
  svg.addEventListener('pointercancel', endGesture);

  svg.addEventListener(
    'wheel',
    (e) => {
      e.preventDefault();
      const delta = e.deltaMode === 1 ? e.deltaY * 16 : e.deltaY;
      zoomAt(Math.exp(-delta * 0.0015), e.clientX, e.clientY);
    },
    { passive: false },
  );

  /* ----- keyboard ----- */

  const typing = (e) => e.target.closest?.('input, textarea, [contenteditable="true"]');

  window.addEventListener('keydown', (e) => {
    if (typing(e)) return;
    const mod = e.ctrlKey || e.metaKey;
    if (e.code === 'Space' && !spaceHeld) {
      spaceHeld = true;
      svg.classList.add('space-pan');
      e.preventDefault();
      return;
    }
    if (mod && e.key.toLowerCase() === 'z') {
      e.preventDefault();
      if (e.shiftKey) redo();
      else undo();
    } else if (mod && e.key.toLowerCase() === 'y') {
      e.preventDefault();
      redo();
    } else if (mod && e.key.toLowerCase() === 'a') {
      e.preventDefault();
      selectAll();
    } else if (mod && e.key.toLowerCase() === 'd') {
      e.preventDefault();
      duplicate();
    } else if (e.key === 'Delete' || e.key === 'Backspace') {
      e.preventDefault();
      deleteSelection();
    } else if (e.key === 'Escape') {
      selection.clear();
      render();
    } else if (e.key.startsWith('Arrow') && selection.size) {
      e.preventDefault();
      const step = e.shiftKey ? 10 : 1;
      const dx = e.key === 'ArrowLeft' ? -step : e.key === 'ArrowRight' ? step : 0;
      const dy = e.key === 'ArrowUp' ? -step : e.key === 'ArrowDown' ? step : 0;
      nudge(dx, dy);
    }
  });

  window.addEventListener('keyup', (e) => {
    if (e.code === 'Space') {
      spaceHeld = false;
      svg.classList.remove('space-pan');
    }
  });

  /* ----- startup ----- */

  function load(data, { keepView = false } = {}) {
    const next = data?.doc ?? data;
    if (!next || !Array.isArray(next.nodes)) throw new Error('Not a Blueprint Designer diagram');
    doc = { ...emptyDoc(), ...next, spines: next.spines ?? [], edges: next.edges ?? [] };
    selection.clear();
    render();
    if (!keepView && data?.view) {
      view = data.view;
      applyView();
    } else if (!keepView) fit();
  }

  function replaceDoc(data) {
    const before = snapshot();
    load(data);
    pushHistory(before);
  }

  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null');
    if (saved) load(saved);
    else fit();
  } catch {
    fit();
  }
  applyView();

  return {
    addIcon,
    addIconAt(icon, clientX, clientY) {
      addIcon(icon, toWorld(clientX, clientY));
    },
    undo,
    redo,
    deleteSelection,
    arrange,
    selectAll,
    fit,
    zoomIn: () => zoomAt(1.2),
    zoomOut: () => zoomAt(1 / 1.2),
    resetZoom: () => zoomAt(1 / view.k),
    clear() {
      commit(() => {
        doc = emptyDoc();
        selection.clear();
      });
    },
    getData: () => ({ app: 'architecture-blueprint-designer', ...structuredClone({ doc, view }) }),
    replaceDoc,
    contentBounds,
    refresh: render,
    async ensureIcons() {
      await Promise.all(doc.nodes.filter((n) => n.icon).map(resolveIcon));
      render();
    },
    clearSelectionForExport() {
      const prev = selection;
      selection = new Set();
      render();
      return () => {
        selection = prev;
        render();
      };
    },
    canUndo: () => undoStack.length > 0,
    canRedo: () => redoStack.length > 0,
    onChange(fn) {
      listeners.push(fn);
    },
  };
}
