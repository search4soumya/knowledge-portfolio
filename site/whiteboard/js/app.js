(function () {
  const STORE = "design-principles:whiteboard";
  const canvas = document.getElementById("board");
  const hint = document.getElementById("empty-hint");
  const zoomLabel = document.getElementById("zoom-label");
  const ctx = canvas.getContext("2d");
  const COLORS = ["#10b981", "#f59e0b", "#6366f1", "#f8fafc", "#ef4444"];

  const state = {
    tool: "pen",
    color: "#10b981",
    width: 3,
    items: [],
    selected: null,
    camera: { x: 0, y: 0, scale: 1 },
    history: [],
    future: [],
    drawing: null,
    lastPoint: null,
    panning: false,
    space: false,
    panFrom: null,
    dragOffset: null,
  };

  let toastTimer = 0;
  function toast(message) {
    let node = document.querySelector(".toast");
    if (!node) {
      node = document.createElement("div");
      node.className = "toast";
      document.body.appendChild(node);
    }
    node.textContent = message;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => node.remove(), 2400);
  }

  function uid() {
    return "w" + Math.random().toString(36).slice(2, 10);
  }

  function snapshot() {
    return JSON.parse(JSON.stringify({ items: state.items, selected: state.selected }));
  }

  function pushHistory() {
    state.history.push(snapshot());
    if (state.history.length > 80) state.history.shift();
    state.future = [];
    persist();
  }

  function persist() {
    try {
      localStorage.setItem(STORE, JSON.stringify({ items: state.items, camera: state.camera }));
    } catch (error) { /* ignore quota */ }
  }

  function restore(pack) {
    state.items = pack.items || [];
    state.selected = pack.selected || null;
    render();
  }

  function worldFromEvent(event) {
    const box = canvas.getBoundingClientRect();
    return {
      x: (event.clientX - box.left - state.camera.x) / state.camera.scale,
      y: (event.clientY - box.top - state.camera.y) / state.camera.scale,
    };
  }

  function boundsOf(item) {
    if (item.type === "pen") {
      const xs = item.points.map((p) => p.x);
      const ys = item.points.map((p) => p.y);
      return {
        x: Math.min(...xs) - item.width,
        y: Math.min(...ys) - item.width,
        w: Math.max(...xs) - Math.min(...xs) + item.width * 2,
        h: Math.max(...ys) - Math.min(...ys) + item.width * 2,
      };
    }
    const x = Math.min(item.x, item.x + (item.w || 0));
    const y = Math.min(item.y, item.y + (item.h || 0));
    return { x, y, w: Math.abs(item.w || 140), h: Math.abs(item.h || 40) };
  }

  function hitTest(point) {
    for (let i = state.items.length - 1; i >= 0; i -= 1) {
      const item = state.items[i];
      const b = boundsOf(item);
      const pad = item.type === "pen" ? 8 : 4;
      if (point.x >= b.x - pad && point.x <= b.x + b.w + pad && point.y >= b.y - pad && point.y <= b.y + b.h + pad) {
        return item;
      }
    }
    return null;
  }

  function moveItem(item, dx, dy) {
    if (item.points) item.points.forEach((p) => { p.x += dx; p.y += dy; });
    if (item.x != null) { item.x += dx; item.y += dy; }
  }

  function drawItem(item, preview) {
    ctx.save();
    ctx.strokeStyle = item.color;
    ctx.fillStyle = item.color;
    ctx.lineWidth = item.width;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    if (item.type === "pen" && item.points.length) {
      ctx.beginPath();
      ctx.moveTo(item.points[0].x, item.points[0].y);
      item.points.forEach((p) => ctx.lineTo(p.x, p.y));
      ctx.stroke();
    } else if (item.type === "line" || item.type === "arrow") {
      ctx.beginPath();
      ctx.moveTo(item.x, item.y);
      ctx.lineTo(item.x + item.w, item.y + item.h);
      ctx.stroke();
      if (item.type === "arrow") {
        const angle = Math.atan2(item.h, item.w);
        const len = 12 + item.width;
        ctx.beginPath();
        ctx.moveTo(item.x + item.w, item.y + item.h);
        ctx.lineTo(item.x + item.w - Math.cos(angle - 0.4) * len, item.y + item.h - Math.sin(angle - 0.4) * len);
        ctx.lineTo(item.x + item.w - Math.cos(angle + 0.4) * len, item.y + item.h - Math.sin(angle + 0.4) * len);
        ctx.closePath();
        ctx.fill();
      }
    } else if (item.type === "rect") {
      ctx.strokeRect(item.x, item.y, item.w, item.h);
    } else if (item.type === "ellipse") {
      ctx.beginPath();
      ctx.ellipse(item.x + item.w / 2, item.y + item.h / 2, Math.abs(item.w / 2), Math.abs(item.h / 2), 0, 0, Math.PI * 2);
      ctx.stroke();
    } else if (item.type === "text") {
      ctx.font = "18px Segoe UI, sans-serif";
      ctx.fillText(item.text || "Text", item.x, item.y + 18);
    } else if (item.type === "note") {
      ctx.fillStyle = item.fill || "#f59e0b";
      ctx.globalAlpha = 0.9;
      ctx.fillRect(item.x, item.y, item.w, item.h);
      ctx.globalAlpha = 1;
      ctx.fillStyle = "#0a0e17";
      ctx.font = "15px Segoe UI, sans-serif";
      wrapText(item.text || "Note", item.x + 10, item.y + 24, item.w - 20, 20);
    }
    if (!preview && item.id === state.selected) {
      const b = boundsOf(item);
      ctx.strokeStyle = "#10b981";
      ctx.setLineDash([5, 4]);
      ctx.lineWidth = 1;
      ctx.strokeRect(b.x - 4, b.y - 4, b.w + 8, b.h + 8);
    }
    ctx.restore();
  }

  function wrapText(text, x, y, max, lineH) {
    const words = String(text).split(/\s+/);
    let line = "";
    let cy = y;
    words.forEach((word) => {
      const next = line ? line + " " + word : word;
      if (ctx.measureText(next).width > max && line) {
        ctx.fillText(line, x, cy);
        line = word;
        cy += lineH;
      } else line = next;
    });
    ctx.fillText(line, x, cy);
  }

  function drawGrid() {
    const step = 24 * state.camera.scale;
    if (step < 10) return;
    ctx.save();
    ctx.fillStyle = "#162033";
    const startX = ((state.camera.x % step) + step) % step;
    const startY = ((state.camera.y % step) + step) % step;
    for (let x = startX; x < canvas.width; x += step) {
      for (let y = startY; y < canvas.height; y += step) ctx.fillRect(x, y, 1.2, 1.2);
    }
    ctx.restore();
  }

  function render() {
    const dpr = window.devicePixelRatio || 1;
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    if (canvas.width !== width * dpr || canvas.height !== height * dpr) {
      canvas.width = width * dpr;
      canvas.height = height * dpr;
    }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, width, height);
    drawGrid();
    ctx.save();
    ctx.translate(state.camera.x, state.camera.y);
    ctx.scale(state.camera.scale, state.camera.scale);
    state.items.forEach((item) => drawItem(item, false));
    if (state.drawing) drawItem(state.drawing, true);
    ctx.restore();
    hint.hidden = state.items.length > 0 || !!state.drawing;
    zoomLabel.textContent = Math.round(state.camera.scale * 100) + "%";
    canvas.classList.toggle("select-mode", state.tool === "select");
    syncButtons();
  }

  function syncButtons() {
    document.querySelectorAll("[data-tool]").forEach((btn) => {
      btn.setAttribute("aria-pressed", String(btn.dataset.tool === state.tool));
    });
    document.querySelectorAll(".color-swatch").forEach((btn) => {
      btn.setAttribute("aria-pressed", String(btn.dataset.color === state.color));
    });
    document.querySelector('[data-action="undo"]').disabled = !state.history.length;
    document.querySelector('[data-action="redo"]').disabled = !state.future.length;
  }

  function setTool(tool) {
    state.tool = tool;
    render();
  }

  function setColor(color) {
    state.color = color;
    document.getElementById("color").value = color;
    const selected = state.items.find((item) => item.id === state.selected);
    if (selected) {
      pushHistory();
      selected.color = color;
      if (selected.type === "note") selected.fill = color;
    }
    render();
  }

  function contentBounds() {
    if (!state.items.length) return null;
    const boxes = state.items.map(boundsOf);
    const x = Math.min(...boxes.map((b) => b.x));
    const y = Math.min(...boxes.map((b) => b.y));
    const r = Math.max(...boxes.map((b) => b.x + b.w));
    const b = Math.max(...boxes.map((b) => b.y + b.h));
    return { x, y, w: r - x, h: b - y };
  }

  function fit() {
    const box = contentBounds();
    if (!box) {
      state.camera = { x: 0, y: 0, scale: 1 };
    } else {
      const pad = 80;
      const scale = Math.min(
        (canvas.clientWidth - pad) / Math.max(box.w, 40),
        (canvas.clientHeight - pad) / Math.max(box.h, 40),
        2
      );
      state.camera.scale = scale;
      state.camera.x = (canvas.clientWidth - box.w * scale) / 2 - box.x * scale;
      state.camera.y = (canvas.clientHeight - box.h * scale) / 2 - box.y * scale;
    }
    persist();
    render();
  }

  function placeText(point, type) {
    const existing = document.querySelector(".text-editor");
    if (existing) existing.remove();
    const editor = document.createElement("textarea");
    editor.className = type === "note" ? "note-editor" : "text-editor";
    const box = canvas.getBoundingClientRect();
    editor.style.left = point.x * state.camera.scale + state.camera.x + box.left - document.body.getBoundingClientRect().left + "px";
    editor.style.top = point.y * state.camera.scale + state.camera.y + 64 + "px";
    editor.placeholder = type === "note" ? "Sticky note" : "Type and press Enter";
    document.querySelector(".stage").appendChild(editor);
    editor.focus();
    const commit = () => {
      const text = editor.value.trim();
      editor.remove();
      if (!text) return;
      pushHistory();
      state.items.push(type === "note"
        ? { id: uid(), type: "note", x: point.x, y: point.y, w: 180, h: 120, text, color: "#0a0e17", fill: state.color, width: 1 }
        : { id: uid(), type: "text", x: point.x, y: point.y, w: 220, h: 28, text, color: state.color, width: 1 });
      persist();
      render();
    };
    editor.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        commit();
      }
      if (event.key === "Escape") editor.remove();
    });
    editor.addEventListener("blur", commit);
  }

  canvas.addEventListener("pointerdown", (event) => {
    if (event.button === 1 || state.space) {
      state.panning = true;
      state.panFrom = { x: event.clientX, y: event.clientY, cx: state.camera.x, cy: state.camera.y };
      canvas.classList.add("panning");
      return;
    }
    if (event.button !== 0) return;
    canvas.setPointerCapture(event.pointerId);
    const point = worldFromEvent(event);
    if (state.tool === "select") {
      const hit = hitTest(point);
      state.selected = hit ? hit.id : null;
      state.dragOffset = hit ? { x: point.x, y: point.y } : null;
      if (hit) pushHistory();
      render();
      return;
    }
    if (state.tool === "eraser") {
      const hit = hitTest(point);
      if (hit) {
        pushHistory();
        state.items = state.items.filter((item) => item.id !== hit.id);
        state.selected = null;
        persist();
        render();
      }
      return;
    }
    if (state.tool === "text" || state.tool === "note") {
      placeText(point, state.tool);
      return;
    }
    state.drawing = state.tool === "pen"
      ? { id: uid(), type: "pen", points: [point], color: state.color, width: state.width }
      : { id: uid(), type: state.tool, x: point.x, y: point.y, w: 0, h: 0, color: state.color, width: state.width };
    state.lastPoint = point;
    render();
  });

  canvas.addEventListener("pointermove", (event) => {
    if (state.panning && state.panFrom) {
      state.camera.x = state.panFrom.cx + (event.clientX - state.panFrom.x);
      state.camera.y = state.panFrom.cy + (event.clientY - state.panFrom.y);
      render();
      return;
    }
    const point = worldFromEvent(event);
    if (state.tool === "select" && state.dragOffset && state.selected) {
      const item = state.items.find((entry) => entry.id === state.selected);
      if (item) {
        moveItem(item, point.x - state.dragOffset.x, point.y - state.dragOffset.y);
        state.dragOffset = point;
        render();
      }
      return;
    }
    if (!state.drawing) return;
    if (state.drawing.type === "pen") state.drawing.points.push(point);
    else {
      state.drawing.w = point.x - state.drawing.x;
      state.drawing.h = point.y - state.drawing.y;
    }
    render();
  });

  function endStroke() {
    if (state.panning) {
      state.panning = false;
      state.panFrom = null;
      canvas.classList.remove("panning");
      persist();
      return;
    }
    state.dragOffset = null;
    if (!state.drawing) return;
    const item = state.drawing;
    state.drawing = null;
    const tiny = item.type === "pen" ? item.points.length < 2 : Math.abs(item.w) < 2 && Math.abs(item.h) < 2;
    if (!tiny) {
      pushHistory();
      state.items.push(item);
      persist();
    }
    render();
  }

  canvas.addEventListener("pointerup", endStroke);
  canvas.addEventListener("pointercancel", endStroke);

  canvas.addEventListener("wheel", (event) => {
    event.preventDefault();
    const factor = event.deltaY < 0 ? 1.08 : 0.92;
    const next = Math.min(3, Math.max(0.25, state.camera.scale * factor));
    const box = canvas.getBoundingClientRect();
    const mx = event.clientX - box.left;
    const my = event.clientY - box.top;
    const wx = (mx - state.camera.x) / state.camera.scale;
    const wy = (my - state.camera.y) / state.camera.scale;
    state.camera.scale = next;
    state.camera.x = mx - wx * next;
    state.camera.y = my - wy * next;
    persist();
    render();
  }, { passive: false });

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
    if (!box) return toast("The board is empty.");
    const pad = 40;
    const scale = 2;
    const out = document.createElement("canvas");
    out.width = (box.w + pad * 2) * scale;
    out.height = (box.h + pad * 2) * scale;
    const g = out.getContext("2d");
    g.fillStyle = "#0a0e17";
    g.fillRect(0, 0, out.width, out.height);
    g.scale(scale, scale);
    g.translate(pad - box.x, pad - box.y);
    const old = ctx;
    // draw using a temporary context swap
    const store = canvas.getContext("2d");
    void store;
    state.items.forEach((item) => {
      const prev = { ctx };
      void prev;
    });
    const backup = {
      draw: drawItem,
    };
    void backup;
    const tempCtx = g;
    const original = canvas.getContext.bind(canvas);
    void original;
    const savedCtx = ctx;
    // Re-implement draw on export context
    const draw = drawItem;
    // Monkey-patch by calling with substituted global ctx via wrapper
    function paint(item) {
      const c = tempCtx;
      c.save();
      c.strokeStyle = item.color;
      c.fillStyle = item.color;
      c.lineWidth = item.width;
      c.lineCap = "round";
      c.lineJoin = "round";
      if (item.type === "pen" && item.points.length) {
        c.beginPath();
        c.moveTo(item.points[0].x, item.points[0].y);
        item.points.forEach((p) => c.lineTo(p.x, p.y));
        c.stroke();
      } else if (item.type === "line" || item.type === "arrow") {
        c.beginPath();
        c.moveTo(item.x, item.y);
        c.lineTo(item.x + item.w, item.y + item.h);
        c.stroke();
        if (item.type === "arrow") {
          const angle = Math.atan2(item.h, item.w);
          const len = 12 + item.width;
          c.beginPath();
          c.moveTo(item.x + item.w, item.y + item.h);
          c.lineTo(item.x + item.w - Math.cos(angle - 0.4) * len, item.y + item.h - Math.sin(angle - 0.4) * len);
          c.lineTo(item.x + item.w - Math.cos(angle + 0.4) * len, item.y + item.h - Math.sin(angle + 0.4) * len);
          c.closePath();
          c.fill();
        }
      } else if (item.type === "rect") c.strokeRect(item.x, item.y, item.w, item.h);
      else if (item.type === "ellipse") {
        c.beginPath();
        c.ellipse(item.x + item.w / 2, item.y + item.h / 2, Math.abs(item.w / 2), Math.abs(item.h / 2), 0, 0, Math.PI * 2);
        c.stroke();
      } else if (item.type === "text") {
        c.font = "18px Segoe UI, sans-serif";
        c.fillText(item.text || "Text", item.x, item.y + 18);
      } else if (item.type === "note") {
        c.fillStyle = item.fill || "#f59e0b";
        c.globalAlpha = 0.9;
        c.fillRect(item.x, item.y, item.w, item.h);
        c.globalAlpha = 1;
        c.fillStyle = "#0a0e17";
        c.font = "15px Segoe UI, sans-serif";
        const words = String(item.text || "Note").split(/\s+/);
        let line = "";
        let cy = item.y + 24;
        words.forEach((word) => {
          const next = line ? line + " " + word : word;
          if (c.measureText(next).width > item.w - 20 && line) {
            c.fillText(line, item.x + 10, cy);
            line = word;
            cy += 20;
          } else line = next;
        });
        c.fillText(line, item.x + 10, cy);
      }
      c.restore();
    }
    void draw;
    void savedCtx;
    state.items.forEach(paint);
    out.toBlob((blob) => download(blob, "whiteboard.png"), "image/png");
  }

  const actions = {
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
    delete() {
      if (!state.selected) return;
      pushHistory();
      state.items = state.items.filter((item) => item.id !== state.selected);
      state.selected = null;
      persist();
      render();
    },
    clear() {
      if (!state.items.length) return;
      pushHistory();
      state.items = [];
      state.selected = null;
      persist();
      render();
    },
    save() {
      download(new Blob([JSON.stringify({ items: state.items }, null, 2)], { type: "application/json" }), "whiteboard.json");
    },
    open() { document.getElementById("open-file").click(); },
    png: exportPng,
    "zoom-in"() { state.camera.scale = Math.min(3, state.camera.scale * 1.15); persist(); render(); },
    "zoom-out"() { state.camera.scale = Math.max(0.25, state.camera.scale / 1.15); persist(); render(); },
    "zoom-reset"() { state.camera = { x: 0, y: 0, scale: 1 }; persist(); render(); },
    "zoom-fit": fit,
  };

  document.addEventListener("click", (event) => {
    const tool = event.target.closest("[data-tool]");
    if (tool) setTool(tool.dataset.tool);
    const swatch = event.target.closest(".color-swatch");
    if (swatch) setColor(swatch.dataset.color);
    const action = event.target.closest("[data-action]");
    if (action && actions[action.dataset.action]) actions[action.dataset.action]();
  });

  document.getElementById("color").addEventListener("input", (event) => setColor(event.target.value));
  document.getElementById("width").addEventListener("input", (event) => { state.width = Number(event.target.value); });
  document.getElementById("open-file").addEventListener("change", async (event) => {
    const file = event.target.files[0];
    event.target.value = "";
    if (!file) return;
    try {
      const data = JSON.parse(await file.text());
      pushHistory();
      state.items = data.items || [];
      state.selected = null;
      persist();
      render();
    } catch (error) {
      toast("Could not open that file.");
    }
  });

  window.addEventListener("keydown", (event) => {
    if (event.target.matches("input, textarea")) return;
    if (event.code === "Space") { state.space = true; event.preventDefault(); }
    const keys = { v: "select", p: "pen", e: "eraser", l: "line", a: "arrow", r: "rect", o: "ellipse", t: "text", n: "note" };
    if (!event.ctrlKey && !event.metaKey && keys[event.key.toLowerCase()]) setTool(keys[event.key.toLowerCase()]);
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "z") { event.preventDefault(); actions.undo(); }
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "y") { event.preventDefault(); actions.redo(); }
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s") { event.preventDefault(); actions.save(); }
    if (event.key === "Delete" || event.key === "Backspace") actions.delete();
  });
  window.addEventListener("keyup", (event) => {
    if (event.code === "Space") state.space = false;
  });
  window.addEventListener("resize", render);

  try {
    const saved = JSON.parse(localStorage.getItem(STORE) || "null");
    if (saved) {
      state.items = saved.items || [];
      state.camera = saved.camera || state.camera;
    }
  } catch (error) { /* start empty */ }

  render();
})();
