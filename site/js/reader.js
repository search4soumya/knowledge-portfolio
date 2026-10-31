(function () {
  document.documentElement.classList.add("js");
  var nav = document.getElementById("toc");
  var notes = document.getElementById("notes");
  var toggle = document.querySelector(".nav-toggle");
  var sections = notes
    ? Array.prototype.slice.call(notes.querySelectorAll("[data-section]"))
    : [];
  if (!nav) return;

  function elementFrom(target) {
    if (!target) return null;
    if (target.nodeType === 1) return target;
    return target.parentElement;
  }

  function idFromHash() {
    var raw = (location.hash || "").replace(/^#/, "");
    if (!raw) return sections.length ? sections[0].id : "";
    try {
      return decodeURIComponent(raw);
    } catch (error) {
      return raw;
    }
  }

  function show(id, options) {
    if (!notes || !sections.length) return;
    options = options || {};
    var match = null;
    sections.forEach(function (section) {
      var on = section.id === id;
      section.classList.toggle("is-active", on);
      if (on) match = section;
    });
    if (!match && sections[0]) {
      sections[0].classList.add("is-active");
      match = sections[0];
      id = match.id;
    }

    Array.prototype.forEach.call(nav.querySelectorAll("a[href^='#']"), function (link) {
      if (link.getAttribute("href") === "#" + id) link.setAttribute("aria-current", "true");
      else link.removeAttribute("aria-current");
    });

    document.body.classList.remove("nav-open");
    if (toggle) toggle.setAttribute("aria-expanded", "false");

    var heading = match ? match.querySelector("h2") : null;
    if (options.focus && heading) {
      if (!heading.hasAttribute("tabindex")) heading.setAttribute("tabindex", "-1");
      try {
        heading.focus({ preventScroll: true });
      } catch (error) {
        heading.focus();
      }
    }
    if (options.align) {
      notes.scrollIntoView({ block: "start", behavior: "auto" });
    }
  }

  document.addEventListener("click", function (event) {
    var el = elementFrom(event.target);
    if (!el || !el.closest) return;

    var link = el.closest("a[href^='#']");
    if (link && link.getAttribute("href").length > 1) {
      var id = link.getAttribute("href").slice(1);
      try { id = decodeURIComponent(id); } catch (error) { /* keep raw id */ }
      if (document.getElementById(id)) {
        event.preventDefault();
        if (location.hash !== "#" + id) history.pushState(null, "", "#" + id);
        show(id, { focus: true, align: true });
        return;
      }
    }

    if (!document.body.classList.contains("nav-open")) return;
    if (nav.contains(el)) return;
    if (toggle && toggle.contains(el)) return;
    document.body.classList.remove("nav-open");
    if (toggle) toggle.setAttribute("aria-expanded", "false");
  });

  if (notes && sections.length) {
    window.addEventListener("popstate", function () {
      show(idFromHash(), { align: true });
    });
  }

  if (toggle) {
    toggle.addEventListener("click", function () {
      var open = !document.body.classList.contains("nav-open");
      document.body.classList.toggle("nav-open", open);
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    document.addEventListener("keydown", function (event) {
      if (event.key !== "Escape") return;
      document.body.classList.remove("nav-open");
      toggle.setAttribute("aria-expanded", "false");
    });
  }

  var filter = document.getElementById("topic-filter");
  if (filter) {
    filter.addEventListener("input", function () {
      var query = filter.value.trim().toLowerCase();
      Array.prototype.forEach.call(nav.querySelectorAll("[data-topic-link]"), function (link) {
        link.hidden = query !== "" && link.textContent.toLowerCase().indexOf(query) === -1;
      });
      Array.prototype.forEach.call(nav.querySelectorAll(".topic-category, .topic-tier"), function (group) {
        var visible = group.querySelector("[data-topic-link]:not([hidden])");
        group.hidden = !visible;
        if (query && visible) group.open = true;
      });
    });
  }

  if (notes && sections.length) {
    show(idFromHash(), { align: location.hash !== "" });
  }
})();
