(function () {
  const STORE = "design-principles:mindmap";
  const svg = document.getElementById("map");
  const viewport = document.getElementById("viewport");
  const edgeLayer = document.getElementById("edges");
  const nodeLayer = document.getElementById("nodes");
  const zoomLabel = document.getElementById("zoom-label");
  const NS = "http://www.w3.org/2000/svg";

  const state = {
    nodes: {},
    root: null,
    selected: null,
    camera: { x: 80, y: 80, scale: 1 },
    history: [],
    future: [],
    drag: null,
    space: false,
    pan: null,
  };

  function uid() { return "m" + Math.random().toString(36).slice(2, 10); }

  function createNode(text, parent, color) {
    const node = { id: uid(), text, parent, children: [], x: 0, y: 0, color: color || "#10b981", collapsed: false };
    state.nodes[node.id] = node;
    if (parent) state.nodes[parent].children.push(node.id);
    return node;
  }

  function snapshot() {
    return JSON.parse(JSON.stringify({ nodes: state.nodes, root: state.root, selected: state.selected }));
  }

  function pushHistory() {
    state.history.push(snapshot());
    if (state.history.length > 80) state.history.shift();
    state.future = [];
    persist();
  }

  function persist() {
    try {
      localStorage.setItem(STORE, JSON.stringify({ nodes: state.nodes, root: state.root, camera: state.camera }));
    } catch (error) { /* ignore */ }
  }

  function restore(pack) {
    state.nodes = pack.nodes;
    state.root = pack.root;
    state.selected = pack.selected;
    render();
  }

  function descendants(id, list) {
    const node = state.nodes[id];
    if (!node) return list;
    node.children.forEach((child) => {
      list.push(child);
      descendants(child, list);
    });
    return list;
  }

  function visibleChildren(node) {
    return node.collapsed ? [] : node.children.map((id) => state.nodes[id]).filter(Boolean);
  }

  function measure(text) {
    const width = Math.min(280, Math.max(88, String(text).length * 8.2 + 28));
    return { w: width, h: 36 };
  }

  function layout() {
    const gapX = 56;
    const gapY = 18;
    function size(node) {
      const box = measure(node.text);
      node.w = box.w;
      node.h = box.h;
      const kids = visibleChildren(node);
      if (!kids.length) return box.h;
      const height = kids.reduce((sum, child, i) => sum + size(child) + (i ? gapY : 0), 0);
      return Math.max(box.h, height);
    }
    function place(node, x, y, height) {
      node.x = x;
      node.y = y + (height - node.h) / 2;
      const kids = visibleChildren(node);
      if (!kids.length) return;
      let cy = y;
      kids.forEach((child) => {
        const h = subtreeHeight(child);
        place(child, x + node.w + gapX, cy, h);
        cy += h + gapY;
      });
    }
    function subtreeHeight(node) {
      const kids = visibleChildren(node);
      if (!kids.length) return node.h;
      return Math.max(node.h, kids.reduce((sum, child, i) => sum + subtreeHeight(child) + (i ? gapY : 0), 0));
    }
    const root = state.nodes[state.root];
    if (!root) return;
    const total = size(root);
    place(root, 40, 40, total);
  }

  function worldFromEvent(event) {
    const box = svg.getBoundingClientRect();
    return {
      x: (event.clientX - box.left - state.camera.x) / state.camera.scale,
      y: (event.clientY - box.top - state.camera.y) / state.camera.scale,
    };
  }

  function applyCamera() {
    viewport.setAttribute("transform", `translate(${state.camera.x} ${state.camera.y}) scale(${state.camera.scale})`);
    zoomLabel.textContent = Math.round(state.camera.scale * 100) + "%";
  }

  function edgePath(from, to) {
    const x1 = from.x + from.w;
    const y1 = from.y + from.h / 2;
    const x2 = to.x;
    const y2 = to.y + to.h / 2;
    const mid = (x1 + x2) / 2;
    return `M${x1} ${y1} C${mid} ${y1}, ${mid} ${y2}, ${x2} ${y2}`;
  }

  function render() {
    edgeLayer.replaceChildren();
    nodeLayer.replaceChildren();
    Object.values(state.nodes).forEach((node) => {
      if (!node.w) {
        const box = measure(node.text);
        node.w = box.w;
        node.h = box.h;
      }
    });
    function walk(id) {
      const node = state.nodes[id];
      if (!node) return;
      visibleChildren(node).forEach((child) => {
        const path = document.createElementNS(NS, "path");
        path.setAttribute("class", "edge");
        path.setAttribute("d", edgePath(node, child));
        path.setAttribute("stroke", child.color || "#334155");
        edgeLayer.appendChild(path);
        walk(child.id);
      });
      const g = document.createElementNS(NS, "g");
      g.setAttribute("class", "node" + (id === state.root ? " root" : "") + (id === state.selected ? " selected" : ""));
      g.dataset.id = id;
      const rect = document.createElementNS(NS, "rect");
      rect.setAttribute("x", node.x);
      rect.setAttribute("y", node.y);
      rect.setAttribute("width", node.w);
      rect.setAttribute("height", node.h);
      rect.setAttribute("rx", 10);
      rect.setAttribute("stroke", node.color);
      const text = document.createElementNS(NS, "text");
      text.setAttribute("x", node.x + 14);
      text.setAttribute("y", node.y + 23);
      text.textContent = node.text + (node.collapsed && node.children.length ? " +" : "");
      g.append(rect, text);
      nodeLayer.appendChild(g);
    }
    walk(state.root);
    applyCamera();
    document.querySelector('[data-action="undo"]').disabled = !state.history.length;
    document.querySelector('[data-action="redo"]').disabled = !state.future.length;
  }

  function addChild() {
    const parent = state.nodes[state.selected || state.root];
    if (!parent) return;
    pushHistory();
    parent.collapsed = false;
    const node = createNode("New idea", parent.id, parent.color);
    node.x = parent.x + parent.w + 56;
    node.y = parent.y + (parent.children.length - 1) * 48;
    state.selected = node.id;
    persist();
    render();
    editNode(node.id);
  }

  function addSibling() {
    const current = state.nodes[state.selected];
    if (!current || !current.parent) return addChild();
    pushHistory();
    const node = createNode("New idea", current.parent, current.color);
    node.x = current.x;
    node.y = current.y + 48;
    state.selected = node.id;
    persist();
    render();
    editNode(node.id);
  }

  function deleteSelected() {
    const node = state.nodes[state.selected];
    if (!node || node.id === state.root) return;
    pushHistory();
    const gone = [node.id, ...descendants(node.id, [])];
    const parent = state.nodes[node.parent];
    parent.children = parent.children.filter((id) => id !== node.id);
    gone.forEach((id) => delete state.nodes[id]);
    state.selected = parent.id;
    persist();
    render();
  }

  function editNode(id) {
    const node = state.nodes[id];
    if (!node) return;
    const existing = document.querySelector(".node-editor");
    if (existing) existing.remove();
    const editor = document.createElement("input");
    editor.className = "node-editor";
    const box = svg.getBoundingClientRect();
    editor.value = node.text;
    editor.style.left = box.left + state.camera.x + node.x * state.camera.scale + "px";
    editor.style.top = box.top + state.camera.y + node.y * state.camera.scale + "px";
    editor.style.width = node.w * state.camera.scale + "px";
    document.querySelector(".stage").appendChild(editor);
    editor.focus();
    editor.select();
    const commit = () => {
      const text = editor.value.trim();
      editor.remove();
      if (!text || text === node.text) return;
      pushHistory();
      node.text = text;
      const boxSize = measure(text);
      node.w = boxSize.w;
      persist();
      render();
    };
    editor.addEventListener("keydown", (event) => {
      if (event.key === "Enter") { event.preventDefault(); commit(); }
      if (event.key === "Escape") editor.remove();
    });
    editor.addEventListener("blur", commit);
  }

  function colorSelected(color) {
    const node = state.nodes[state.selected || state.root];
    if (!node) return;
    pushHistory();
    node.color = color;
    persist();
    render();
  }

  function contentBounds() {
    const boxes = Object.values(state.nodes).map((n) => ({ x: n.x, y: n.y, r: n.x + n.w, b: n.y + n.h }));
    return {
      x: Math.min(...boxes.map((b) => b.x)),
      y: Math.min(...boxes.map((b) => b.y)),
      w: Math.max(...boxes.map((b) => b.r)) - Math.min(...boxes.map((b) => b.x)),
      h: Math.max(...boxes.map((b) => b.b)) - Math.min(...boxes.map((b) => b.y)),
    };
  }

  function fit() {
    const box = contentBounds();
    const pad = 80;
    const scale = Math.min(
      (svg.clientWidth - pad) / Math.max(box.w, 80),
      (svg.clientHeight - pad) / Math.max(box.h, 80),
      1.6
    );
    state.camera.scale = scale;
    state.camera.x = (svg.clientWidth - box.w * scale) / 2 - box.x * scale;
    state.camera.y = (svg.clientHeight - box.h * scale) / 2 - box.y * scale;
    persist();
    render();
  }

  function download(blob, name) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = name;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 800);
  }

  function exportPng() {
    const box = contentBounds();
    const pad = 40;
    const scale = 2;
    const out = document.createElement("canvas");
    out.width = (box.w + pad * 2) * scale;
    out.height = (box.h + pad * 2) * scale;
    const ctx = out.getContext("2d");
    ctx.fillStyle = "#0a0e17";
    ctx.fillRect(0, 0, out.width, out.height);
    ctx.scale(scale, scale);
    ctx.translate(pad - box.x, pad - box.y);
    Object.values(state.nodes).forEach((node) => {
      if (node.parent && !state.nodes[node.parent].collapsed) {
        const from = state.nodes[node.parent];
        const x1 = from.x + from.w;
        const y1 = from.y + from.h / 2;
        const x2 = node.x;
        const y2 = node.y + node.h / 2;
        const mid = (x1 + x2) / 2;
        ctx.beginPath();
        ctx.strokeStyle = node.color;
        ctx.lineWidth = 2;
        ctx.moveTo(x1, y1);
        ctx.bezierCurveTo(mid, y1, mid, y2, x2, y2);
        ctx.stroke();
      }
    });
    Object.values(state.nodes).forEach((node) => {
      ctx.fillStyle = "#1a2234";
      ctx.strokeStyle = node.color;
      ctx.lineWidth = 1.6;
      roundRect(ctx, node.x, node.y, node.w, node.h, 10);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = "#f8fafc";
      ctx.font = "14px Segoe UI, sans-serif";
      ctx.fillText(node.text + (node.collapsed && node.children.length ? " +" : ""), node.x + 14, node.y + 23);
    });
    out.toBlob((blob) => download(blob, "mindmap.png"), "image/png");
  }

  function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  const actions = {
    child: addChild,
    sibling: addSibling,
    collapse() {
      const node = state.nodes[state.selected];
      if (!node || !node.children.length) return;
      pushHistory();
      node.collapsed = !node.collapsed;
      persist();
      render();
    },
    layout() { pushHistory(); layout(); persist(); render(); },
    undo() {
      if (!state.history.length) return;
      state.future.push(snapshot());
      restore(state.history.pop());
      persist();
    },
    redo() {
      if (!state.future.length) return;
      state.history.push(snapshot());
      restore(state.future.pop());
      persist();
    },
    delete: deleteSelected,
    save() {
      download(new Blob([JSON.stringify({ nodes: state.nodes, root: state.root }, null, 2)], { type: "application/json" }), "mindmap.json");
    },
    open() { document.getElementById("open-file").click(); },
    png: exportPng,
    "zoom-in"() { state.camera.scale = Math.min(2.4, state.camera.scale * 1.15); persist(); render(); },
    "zoom-out"() { state.camera.scale = Math.max(0.3, state.camera.scale / 1.15); persist(); render(); },
    "zoom-reset"() { state.camera = { x: 80, y: 80, scale: 1 }; persist(); render(); },
    "zoom-fit": fit,
  };

  svg.addEventListener("pointerdown", (event) => {
    if (event.button === 1 || state.space) {
      state.pan = { x: event.clientX, y: event.clientY, cx: state.camera.x, cy: state.camera.y };
      return;
    }
    const group = event.target.closest(".node");
    if (!group) {
      state.selected = null;
      render();
      return;
    }
    state.selected = group.dataset.id;
    const point = worldFromEvent(event);
    const node = state.nodes[state.selected];
    const moving = [state.selected, ...descendants(state.selected, [])];
    state.drag = {
      ids: moving,
      ox: point.x,
      oy: point.y,
      origin: Object.fromEntries(moving.map((id) => [id, { x: state.nodes[id].x, y: state.nodes[id].y }])),
    };
    render();
  });

  svg.addEventListener("pointermove", (event) => {
    if (state.pan) {
      state.camera.x = state.pan.cx + (event.clientX - state.pan.x);
      state.camera.y = state.pan.cy + (event.clientY - state.pan.y);
      applyCamera();
      return;
    }
    if (!state.drag) return;
    const point = worldFromEvent(event);
    const dx = point.x - state.drag.ox;
    const dy = point.y - state.drag.oy;
    state.drag.ids.forEach((id) => {
      state.nodes[id].x = state.drag.origin[id].x + dx;
      state.nodes[id].y = state.drag.origin[id].y + dy;
    });
    render();
  });

  function endDrag() {
    if (state.pan) { state.pan = null; persist(); return; }
    if (state.drag) {
      const moved = state.drag.ids.some((id) => state.nodes[id].x !== state.drag.origin[id].x || state.nodes[id].y !== state.drag.origin[id].y);
      if (moved) {
        const after = snapshot();
        state.drag.ids.forEach((id) => {
          state.nodes[id].x = state.drag.origin[id].x;
          state.nodes[id].y = state.drag.origin[id].y;
        });
        pushHistory();
        state.nodes = after.nodes;
      }
      state.drag = null;
      persist();
      render();
    }
  }

  svg.addEventListener("pointerup", endDrag);
  svg.addEventListener("pointerleave", endDrag);
  svg.addEventListener("dblclick", (event) => {
    const group = event.target.closest(".node");
    if (group) editNode(group.dataset.id);
  });
  svg.addEventListener("wheel", (event) => {
    event.preventDefault();
    const next = Math.min(2.4, Math.max(0.3, state.camera.scale * (event.deltaY < 0 ? 1.08 : 0.92)));
    const box = svg.getBoundingClientRect();
    const mx = event.clientX - box.left;
    const my = event.clientY - box.top;
    const wx = (mx - state.camera.x) / state.camera.scale;
    const wy = (my - state.camera.y) / state.camera.scale;
    state.camera.scale = next;
    state.camera.x = mx - wx * next;
    state.camera.y = my - wy * next;
    persist();
    applyCamera();
  }, { passive: false });

  document.addEventListener("click", (event) => {
    const swatch = event.target.closest(".color-swatch");
    if (swatch) colorSelected(swatch.dataset.color);
    const action = event.target.closest("[data-action]");
    if (action && actions[action.dataset.action]) actions[action.dataset.action]();
  });

  document.getElementById("open-file").addEventListener("change", async (event) => {
    const file = event.target.files[0];
    event.target.value = "";
    if (!file) return;
    try {
      const data = JSON.parse(await file.text());
      if (!data.nodes || !data.root) throw new Error("bad");
      pushHistory();
      state.nodes = data.nodes;
      state.root = data.root;
      state.selected = data.root;
      persist();
      render();
    } catch (error) {
      const node = document.createElement("div");
      node.className = "toast";
      node.textContent = "Could not open that mind map.";
      document.body.appendChild(node);
      setTimeout(() => node.remove(), 2400);
    }
  });

  window.addEventListener("keydown", (event) => {
    if (event.target.matches("input, textarea")) return;
    if (event.code === "Space") { state.space = true; event.preventDefault(); }
    if (event.key === "Tab") { event.preventDefault(); addChild(); }
    if (event.key === "Enter") { event.preventDefault(); addSibling(); }
    if (event.key === "Delete" || event.key === "Backspace") deleteSelected();
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "z") { event.preventDefault(); actions.undo(); }
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "y") { event.preventDefault(); actions.redo(); }
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s") { event.preventDefault(); actions.save(); }
  });
  window.addEventListener("keyup", (event) => {
    if (event.code === "Space") state.space = false;
  });

  try {
    const saved = JSON.parse(localStorage.getItem(STORE) || "null");
    if (saved && saved.nodes && saved.root) {
      state.nodes = saved.nodes;
      state.root = saved.root;
      state.camera = saved.camera || state.camera;
      state.selected = saved.root;
    }
  } catch (error) { /* fresh map */ }

  if (!state.root) {
    const root = createNode("Central idea", null, "#10b981");
    state.root = root.id;
    state.selected = root.id;
    layout();
    const product = createNode("Users", root.id, "#6366f1");
    const system = createNode("System", root.id, "#f59e0b");
    createNode("Journey", product.id, "#6366f1");
    createNode("API", system.id, "#f59e0b");
    createNode("Data", system.id, "#f59e0b");
    layout();
    persist();
  }

  render();
})();
