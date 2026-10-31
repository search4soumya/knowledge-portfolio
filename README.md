# Knowledge Portfolio

Static study notes by Soumya Ranjan Panda. The site is plain HTML, CSS, JavaScript, and SVG images. It does not use a framework, a package manager, or a CDN.

The home page has eight topic cards:

- Architect Design Patterns
- Cloud Fundamental
- Kubernetes
- AI / ML
- Microservices
- DevOps
- Case Study
- Learning Path

Each card opens a topic overview. Every subtopic is a separate HTML file and is linked from the left-hand navigation.

The Architecture library contains 300 generated HTML essays sourced from the Eidos MDX collection: 100 Basic, 100 Intermediate, and 100 Advanced.

Published site: https://search4soumya.github.io/knowledge-portfolio/

## Preview locally

From the `site` directory:

```powershell
python -m http.server 8765
```

Open http://127.0.0.1:8765/

## Regenerate the Architecture library

After adding or editing MDX in `Eidos-Design-Pattern/src/content/topics`, run:

```powershell
cd C:\Users\spanda\Projects\knowledge-portfolio
python scripts\generate_architecture_pages.py --source C:\Users\spanda\Projects\Eidos-Design-Pattern\src\content\topics
```

This rewrites `site/architecture/index.html` and all files under:

- `site/architecture/basic/`
- `site/architecture/intermediate/`
- `site/architecture/advanced/`

The generator includes only published MDX files and currently expects all 300 essays.

## Edit a non-architecture subtopic

The editable source is `content/manual_topics.json`. Each tile has a title, deck, kicker, and a `sections` array. Each section has:

- `slug` — the HTML filename without `.html`
- `label` — the text in the left navigation
- `html` — the article body

After editing the JSON, regenerate:

```powershell
python scripts\generate_tile_pages.py
```

This writes one overview and one HTML file per subtopic for Cloud, Kubernetes, AI/ML, Microservices, DevOps, Case Study, and Learning Path.

Do not edit those generated HTML files directly; the next generator run will replace them.

## Add a home card

1. Add its `<a class="expertise-card">` block to `site/index.html`.
2. Add its source and generator configuration, or create a folder containing `index.html` and separate subtopic HTML files.
3. Link every subtopic from the overview's left navigation.
4. Preview, commit, and push.

Any new HTML file under `site/` is published on the next deploy, even before it is linked. Link it from the home page or from a topic navigation so people can find it.

## Deploy

Pushes to `main` run `.github/workflows/deploy.yml`. The workflow uploads the `site` directory and deploys it to GitHub Pages. You can also run **Deploy website** by hand from the Actions tab.

The site files have no third-party libraries. The workflow uses GitHub's own Pages actions (`actions/checkout`, `actions/upload-pages-artifact`, and `actions/deploy-pages`) because that is how GitHub publishes an Actions-based site.

Keep new pages self-contained. Do not add a script or stylesheet from a CDN.
