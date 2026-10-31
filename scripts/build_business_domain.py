"""Generate the Business Domain Knowledge library.

Reads markdown essays from content/business-domain/ and writes an Architecture-style
library: left-hand domain groups, right-hand article pages.
"""

from __future__ import annotations

import html
import shutil
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_architecture_pages import (  # noqa: E402
    connect_section,
    header,
    markdown_to_html,
    parse_frontmatter,
    slugify,
)


DOMAIN_ORDER = ("telecom", "healthcare", "insurance", "finance")
DOMAIN_LABELS = {
    "telecom": "Telecom",
    "healthcare": "Healthcare",
    "insurance": "Insurance",
    "finance": "Finance",
}
def load_topics(source: Path) -> list[dict[str, object]]:
    topics: list[dict[str, object]] = []
    for path in sorted(source.rglob("*.md")):
        meta, body = parse_frontmatter(path)
        domain = str(meta["domain"])
        if domain not in DOMAIN_LABELS:
            raise SystemExit(f"Unknown domain in {path}: {domain}")
        meta["body"] = body
        meta["source"] = str(path)
        meta["slug"] = str(meta.get("slug") or slugify(str(meta["title"])))
        topics.append(meta)
    topics.sort(
        key=lambda topic: (
            DOMAIN_ORDER.index(str(topic["domain"])),
            int(topic["order"]),
        )
    )
    return topics


def grouped_topics(
    topics: list[dict[str, object]],
) -> OrderedDict[str, OrderedDict[str, list[dict[str, object]]]]:
    groups: OrderedDict[str, OrderedDict[str, list[dict[str, object]]]] = OrderedDict()
    for domain in DOMAIN_ORDER:
        categories: OrderedDict[str, list[dict[str, object]]] = OrderedDict()
        for topic in (item for item in topics if item["domain"] == domain):
            categories.setdefault(str(topic["category"]), []).append(topic)
        groups[domain] = categories
    return groups


def library_nav(
    topics: list[dict[str, object]],
    *,
    current_slug: str | None,
    from_article: bool,
) -> str:
    groups = grouped_topics(topics)
    chunks = [
        '<nav id="toc" class="toc library-nav" aria-labelledby="toc-title">',
        '<p id="toc-title" class="toc-title">Domain topics</p>',
        '<label class="topic-filter-label" for="topic-filter">Find a topic</label>',
        f'<input id="topic-filter" class="topic-filter" type="search" placeholder="Filter {len(topics)} topics" autocomplete="off">',
        f'<a class="library-overview" href="{"../" if from_article else ""}index.html">Domain overview</a>',
        '<div id="topic-tree">',
    ]
    for domain, categories in groups.items():
        domain_contains = any(
            topic["slug"] == current_slug
            for category_topics in categories.values()
            for topic in category_topics
        )
        chunks.append(
            f'<details class="topic-tier"{" open" if domain_contains or not from_article else ""}>'
            f"<summary>{DOMAIN_LABELS[domain]} "
            f"<span>{sum(len(items) for items in categories.values())}</span></summary>"
        )
        for category, category_topics in categories.items():
            category_contains = any(topic["slug"] == current_slug for topic in category_topics)
            chunks.append(
                f'<details class="topic-category"{" open" if category_contains else ""}>'
                f"<summary>{html.escape(category)} <span>{len(category_topics)}</span></summary>"
            )
            for topic in category_topics:
                href = (
                    f"../{topic['domain']}/{topic['slug']}.html"
                    if from_article
                    else f"{topic['domain']}/{topic['slug']}.html"
                )
                current = ' aria-current="page"' if topic["slug"] == current_slug else ""
                chunks.append(
                    f'<a href="{href}" data-topic-link{current}>'
                    f'<span>{html.escape(str(topic["id"]))}</span> '
                    f'{html.escape(str(topic["title"]))}</a>'
                )
            chunks.append("</details>")
        chunks.append("</details>")
    chunks.extend(["</div>", "</nav>"])
    return "\n".join(chunks)


def article_page(
    topic: dict[str, object],
    topics: list[dict[str, object]],
    previous: dict[str, object] | None,
    following: dict[str, object] | None,
) -> str:
    title = html.escape(str(topic["title"]))
    domain = str(topic["domain"])
    category = html.escape(str(topic["category"]))
    slug = str(topic["slug"])
    body = markdown_to_html(str(topic["body"]))

    pager = ['<nav class="article-pager" aria-label="Adjacent topics">']
    if previous:
        pager.append(
            f'<a href="../{previous["domain"]}/{previous["slug"]}.html">← '
            f'<span>{html.escape(str(previous["title"]))}</span></a>'
        )
    else:
        pager.append("<span></span>")
    if following:
        pager.append(
            f'<a class="next" href="../{following["domain"]}/{following["slug"]}.html">'
            f'<span>{html.escape(str(following["title"]))}</span> →</a>'
        )
    pager.append("</nav>")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} — Design Principles</title>
  <meta name="description" content="{title}, a {html.escape(DOMAIN_LABELS[domain])} domain note.">
  <link rel="canonical" href="https://search4soumya.github.io/knowledge-portfolio/business-domain/{domain}/{slug}.html">
  <link rel="icon" href="../../images/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="../../css/styles.css">
</head>
<body data-topic="business-domain">
  <a class="skip" href="#main">Skip to content</a>
{header("../../")}
  <main id="main" class="wrap wrap-wide">
    <p class="kicker">{html.escape(str(topic["id"]))} · {html.escape(DOMAIN_LABELS[domain])} · {category}</p>
    <div class="title-row">
      <h1>{title}</h1>
      <button type="button" class="nav-toggle" aria-expanded="false" aria-controls="toc">Topics</button>
    </div>
    <div class="reader library-reader">
{library_nav(topics, current_slug=slug, from_article=True)}
      <article class="note topic-article">
{body}
{''.join(pager)}
      </article>
    </div>
  </main>
{connect_section()}
  <script src="../../js/reader.js"></script>
</body>
</html>
"""


def overview_page(topics: list[dict[str, object]]) -> str:
    groups = grouped_topics(topics)
    cards: list[str] = []
    for domain, categories in groups.items():
        for category, category_topics in categories.items():
            links = "".join(
                f'<li><a href="{domain}/{topic["slug"]}.html">'
                f'<span>{html.escape(str(topic["id"]))}</span> '
                f'{html.escape(str(topic["title"]))}</a></li>'
                for topic in category_topics
            )
            cards.append(
                f'<section class="catalog-group" id="{domain}-{slugify(category)}">'
                f"<h2>{html.escape(category)}</h2>"
                f"<p>{DOMAIN_LABELS[domain]} · {len(category_topics)} topics</p>"
                f"<ol>{links}</ol></section>"
            )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Business Domain Knowledge — Design Principles</title>
  <meta name="description" content="Telecom, healthcare, insurance, and finance notes for architects who need the business vocabulary before they draw the boxes.">
  <link rel="canonical" href="https://search4soumya.github.io/knowledge-portfolio/business-domain/">
  <link rel="icon" href="../images/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="../css/styles.css">
</head>
<body data-topic="business-domain">
  <a class="skip" href="#main">Skip to content</a>
{header("../")}
  <main id="main" class="wrap wrap-wide">
    <p class="kicker">Business domain library</p>
    <div class="title-row">
      <h1>Business Domain Knowledge</h1>
      <button type="button" class="nav-toggle" aria-expanded="false" aria-controls="toc">Topics</button>
    </div>
    <p class="deck">Four industries, each with its own vocabulary, ledgers, and failure modes. Choose a domain on the left; the note opens on the right.</p>
    <div class="reader library-reader">
{library_nav(topics, current_slug=None, from_article=False)}
      <div class="catalog-groups">
{''.join(cards)}
      </div>
    </div>
  </main>
{connect_section()}
  <script src="../js/reader.js"></script>
</body>
</html>
"""


def main() -> None:
    source = ROOT / "content" / "business-domain"
    output = ROOT / "site" / "business-domain"
    topics = load_topics(source)
    expected = 32
    if len(topics) != expected:
        raise SystemExit(f"Expected {expected} domain topics, found {len(topics)}")

    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    for domain in DOMAIN_ORDER:
        (output / domain).mkdir()

    (output / "index.html").write_text(overview_page(topics), encoding="utf-8")
    for index, topic in enumerate(topics):
        previous = topics[index - 1] if index else None
        following = topics[index + 1] if index + 1 < len(topics) else None
        path = output / str(topic["domain"]) / f'{topic["slug"]}.html'
        path.write_text(article_page(topic, topics, previous, following), encoding="utf-8")

    print(f"Generated {len(topics)} business domain pages plus the overview.")


if __name__ == "__main__":
    main()
