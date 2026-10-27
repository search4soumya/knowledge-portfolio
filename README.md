# Knowledge Portfolio

Static study notes by Soumya Ranjan Panda. The site is plain HTML, CSS, JavaScript, and SVG images. It does not use a framework, a package manager, or a CDN.

The home page has four flash cards:

- Architect Design Patterns
- Cloud Fundamental
- Kubernetes
- AI / ML

Each card opens a topic page. Sections are listed in the left-hand navigation. The selected section is shown in the right-hand panel.

Published site: https://search4soumya.github.io/knowledge-portfolio/

## Preview locally

From the `site` directory:

```powershell
python -m http.server 8765
```

Open http://127.0.0.1:8765/

## Add a subsection

1. Open the topic file, for example `site/architecture/index.html`.
2. Add a link inside `<nav id="toc">`:

```html
<a href="#your-section">Your section title</a>
```

3. Add a matching section inside `<div id="notes">`:

```html
<section id="your-section" data-section>
  <h2>Your section title</h2>
  <p>Write the note here.</p>
</section>
```

4. Commit and push to `main`.

The `id` and the link target must match. The reader script uses that pair to show one section at a time. With JavaScript turned off, every section on the page is still visible.

## Add a topic

1. Copy an existing folder under `site/`, for example `site/architecture/`, and rename it.
2. Edit the title, the navigation, and the sections.
3. Add a flash card on `site/index.html` that links to the new folder.
4. Push to `main`.

Any new HTML file under `site/` is published on the next deploy, even before it is linked. Link it from the home page or from a topic navigation so people can find it.

## Deploy

Pushes to `main` run `.github/workflows/deploy.yml`. The workflow uploads the `site` directory and deploys it to GitHub Pages. You can also run **Deploy website** by hand from the Actions tab.

The site files have no third-party libraries. The workflow uses GitHub's own Pages actions (`actions/checkout`, `actions/upload-pages-artifact`, and `actions/deploy-pages`) because that is how GitHub publishes an Actions-based site.

Keep new pages self-contained. Do not add a script or stylesheet from a CDN.
