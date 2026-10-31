r"""Generate plain HTML architecture essays from the Eidos MDX library.

Usage (PowerShell):
  python scripts\generate_architecture_pages.py `
    --source C:\Users\spanda\Projects\Eidos-Design-Pattern\src\content\topics
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from collections import OrderedDict
from pathlib import Path


TIERS = ("basic", "intermediate", "advanced")
TIER_LABELS = {
    "basic": "Basic",
    "intermediate": "Intermediate",
    "advanced": "Advanced",
}


def parse_frontmatter(path: Path) -> tuple[dict[str, object], str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    if not match:
        raise ValueError(f"Missing frontmatter: {path}")

    data: dict[str, object] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, raw = line.split(":", 1)
        value = raw.strip()
        if value.startswith('"') and value.endswith('"'):
            value = json.loads(value)
        elif value.startswith("[") and value.endswith("]"):
            value = [item.strip().strip('"') for item in value[1:-1].split(",") if item.strip()]
        elif value.isdigit():
            value = int(value)
        data[key.strip()] = value
    return data, match.group(2).strip()


def slugify(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"[^a-z0-9]+", "-", value.lower())
    return value.strip("-") or "section"


def inline_markdown(value: str) -> str:
    code: list[str] = []

    def save_code(match: re.Match[str]) -> str:
        code.append(f"<code>{html.escape(match.group(1))}</code>")
        return f"\x00CODE{len(code) - 1}\x00"

    value = re.sub(r"`([^`\n]+)`", save_code, value)
    value = html.escape(value, quote=False)
    value = re.sub(
        r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
        r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>',
        value,
    )
    value = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", value)
    value = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", value)
    value = re.sub(r"(?<!_)_([^_\n]+)_(?!_)", r"<em>\1</em>", value)
    for index, replacement in enumerate(code):
        value = value.replace(f"\x00CODE{index}\x00", replacement)
    return value


def markdown_to_html(markdown: str) -> str:
    lines = markdown.replace("\r\n", "\n").split("\n")
    output: list[str] = []
    paragraph: list[str] = []
    index = 0

    def flush_paragraph() -> None:
        if paragraph:
            output.append(f"<p>{inline_markdown(' '.join(part.strip() for part in paragraph))}</p>")
            paragraph.clear()

    def is_table_separator(line: str) -> bool:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_paragraph()
            language = stripped[3:].strip()
            index += 1
            code_lines: list[str] = []
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code_lines.append(lines[index])
                index += 1
            escaped = html.escape("\n".join(code_lines))
            if language == "mermaid":
                output.append(
                    '<figure class="diagram-source">'
                    "<figcaption>Architecture diagram source</figcaption>"
                    f'<pre><code class="language-mermaid">{escaped}</code></pre>'
                    "</figure>"
                )
            else:
                cls = f' class="language-{html.escape(language)}"' if language else ""
                output.append(f"<pre><code{cls}>{escaped}</code></pre>")
            index += 1
            continue

        heading = re.match(r"^(#{2,6})\s+(.+)$", stripped)
        if heading:
            flush_paragraph()
            level = len(heading.group(1))
            title = heading.group(2).strip()
            output.append(
                f'<h{level} id="{slugify(title)}">{inline_markdown(title)}</h{level}>'
            )
            index += 1
            continue

        if (
            "|" in stripped
            and index + 1 < len(lines)
            and is_table_separator(lines[index + 1])
        ):
            flush_paragraph()
            headers = [cell.strip() for cell in stripped.strip("|").split("|")]
            index += 2
            rows: list[list[str]] = []
            while index < len(lines) and "|" in lines[index] and lines[index].strip():
                rows.append([cell.strip() for cell in lines[index].strip().strip("|").split("|")])
                index += 1
            table = ['<div class="table-wrap"><table><thead><tr>']
            table.extend(f"<th>{inline_markdown(cell)}</th>" for cell in headers)
            table.append("</tr></thead><tbody>")
            for row in rows:
                table.append("<tr>")
                row += [""] * (len(headers) - len(row))
                table.extend(f"<td>{inline_markdown(cell)}</td>" for cell in row[: len(headers)])
                table.append("</tr>")
            table.append("</tbody></table></div>")
            output.append("".join(table))
            continue

        list_match = re.match(r"^[-*]\s+(.+)$", stripped)
        ordered_match = re.match(r"^\d+\.\s+(.+)$", stripped)
        if list_match or ordered_match:
            flush_paragraph()
            tag = "ol" if ordered_match else "ul"
            items: list[str] = []
            while index < len(lines):
                current = lines[index].strip()
                match = (
                    re.match(r"^\d+\.\s+(.+)$", current)
                    if tag == "ol"
                    else re.match(r"^[-*]\s+(.+)$", current)
                )
                if not match:
                    break
                items.append(match.group(1))
                index += 1
            output.append(
                f"<{tag}>"
                + "".join(f"<li>{inline_markdown(item)}</li>" for item in items)
                + f"</{tag}>"
            )
            continue

        if stripped.startswith("> "):
            flush_paragraph()
            quote: list[str] = []
            while index < len(lines) and lines[index].strip().startswith(">"):
                quote.append(lines[index].strip().lstrip(">").strip())
                index += 1
            output.append(f"<blockquote>{inline_markdown(' '.join(quote))}</blockquote>")
            continue

        if stripped in {"---", "***"}:
            flush_paragraph()
            output.append("<hr>")
            index += 1
            continue

        if not stripped:
            flush_paragraph()
        else:
            paragraph.append(stripped)
        index += 1

    flush_paragraph()
    return "\n".join(output)


def load_topics(source: Path) -> list[dict[str, object]]:
    topics: list[dict[str, object]] = []
    for path in source.rglob("*.mdx"):
        meta, body = parse_frontmatter(path)
        if meta.get("status") != "published":
            continue
        meta["body"] = body
        meta["source"] = str(path)
        topics.append(meta)
    topics.sort(key=lambda topic: (TIERS.index(str(topic["tier"])), int(topic["publishOrder"])))
    return topics


def social_links() -> str:
    return """
      <div class="social-links">
        <a class="social-link" href="https://github.com/soumyaranjanpanda" target="_blank" rel="noopener noreferrer" aria-label="GitHub">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"/></svg>
        </a>
        <a class="social-link" href="https://linkedin.com/in/soumyaranjanpanda" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"/><rect x="2" y="9" width="4" height="12"/><circle cx="4" cy="4" r="2"/></svg>
        </a>
        <a class="social-link" href="https://twitter.com/soumyaranjanpanda" target="_blank" rel="noopener noreferrer" aria-label="Twitter">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M23 3a10.9 10.9 0 0 1-3.14 1.53 4.48 4.48 0 0 0-7.86 3v1A10.66 10.66 0 0 1 3 4s-4 9 5 13a11.64 11.64 0 0 1-7 2c9 5 20 0 20-11.5a4.5 4.5 0 0 0-.08-.83A7.72 7.72 0 0 0 23 3z"/></svg>
        </a>
        <a class="social-link" href="mailto:soumya@example.com" aria-label="Email">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
        </a>
      </div>"""


def connect_section(prefix: str = "") -> str:
    return f"""
  <section class="connect" id="contact">
    <div class="wrap wrap-wide">
      <div class="section-header"><h2 class="section-title">Let's Connect</h2></div>
      <p class="connect-copy">Whether you're interested in collaboration, consulting, or just want to discuss architecture and technology, I'd love to hear from you.</p>
{social_links()}
    </div>
  </section>"""


def header(prefix: str) -> str:
    return f"""
  <header class="site-header">
    <div class="wrap wrap-wide header-inner">
      <a class="brand" href="{prefix}index.html">
        <img src="{prefix}images/portrait.jpg" alt="" width="36" height="36">
        <span class="brand-name">Design Principles</span>
      </a>
      <nav class="header-nav" aria-label="Site">
        <a class="header-link" href="{prefix}index.html">Home</a>
        <a class="header-link" href="{prefix}blueprint/">Blueprint Designer</a>
        <a class="header-link" href="{prefix}about.html">About me</a>
      </nav>
    </div>
  </header>"""


def grouped_topics(topics: list[dict[str, object]]) -> OrderedDict[str, OrderedDict[str, list[dict[str, object]]]]:
    groups: OrderedDict[str, OrderedDict[str, list[dict[str, object]]]] = OrderedDict()
    for tier in TIERS:
        categories: OrderedDict[str, list[dict[str, object]]] = OrderedDict()
        for topic in (item for item in topics if item["tier"] == tier):
            categories.setdefault(str(topic["category"]), []).append(topic)
        groups[tier] = categories
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
        '<p id="toc-title" class="toc-title">Architecture topics</p>',
        '<label class="topic-filter-label" for="topic-filter">Find a topic</label>',
        '<input id="topic-filter" class="topic-filter" type="search" placeholder="Filter 300 topics" autocomplete="off">',
        f'<a class="library-overview" href="{"../" if from_article else ""}index.html">Architecture overview</a>',
        '<div id="topic-tree">',
    ]
    for tier, categories in groups.items():
        tier_contains = any(
            topic["slug"] == current_slug
            for category_topics in categories.values()
            for topic in category_topics
        )
        chunks.append(
            f'<details class="topic-tier"{" open" if tier_contains or not from_article else ""}>'
            f"<summary>{TIER_LABELS[tier]} <span>{sum(len(items) for items in categories.values())}</span></summary>"
        )
        for category, category_topics in categories.items():
            category_contains = any(topic["slug"] == current_slug for topic in category_topics)
            chunks.append(
                f'<details class="topic-category"{" open" if category_contains else ""}>'
                f"<summary>{html.escape(category)} <span>{len(category_topics)}</span></summary>"
            )
            for topic in category_topics:
                if from_article:
                    href = f"../{topic['tier']}/{topic['slug']}.html"
                else:
                    href = f"{topic['tier']}/{topic['slug']}.html"
                current = ' aria-current="page"' if topic["slug"] == current_slug else ""
                chunks.append(
                    f'<a href="{href}" data-topic-link{current}>'
                    f'<span>{html.escape(str(topic["id"]))}</span> {html.escape(str(topic["title"]))}</a>'
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
    tier = str(topic["tier"])
    category = html.escape(str(topic["category"]))
    slug = str(topic["slug"])
    body = markdown_to_html(str(topic["body"]))

    pager = ['<nav class="article-pager" aria-label="Adjacent topics">']
    if previous:
        pager.append(
            f'<a href="../{previous["tier"]}/{previous["slug"]}.html">← '
            f'<span>{html.escape(str(previous["title"]))}</span></a>'
        )
    else:
        pager.append("<span></span>")
    if following:
        pager.append(
            f'<a class="next" href="../{following["tier"]}/{following["slug"]}.html">'
            f'<span>{html.escape(str(following["title"]))}</span> →</a>'
        )
    pager.append("</nav>")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} — Design Principles</title>
  <meta name="description" content="{title}, a {html.escape(tier)} architecture note.">
  <link rel="canonical" href="https://search4soumya.github.io/knowledge-portfolio/architecture/{tier}/{slug}.html">
  <link rel="icon" href="../../images/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="../../css/styles.css">
</head>
<body data-topic="architecture">
  <a class="skip" href="#main">Skip to content</a>
{header("../../")}
  <main id="main" class="wrap wrap-wide">
    <p class="kicker">{html.escape(str(topic["id"]))} · {html.escape(TIER_LABELS[tier])} · {category}</p>
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
    for tier, categories in groups.items():
        for category, category_topics in categories.items():
            links = "".join(
                f'<li><a href="{tier}/{topic["slug"]}.html">'
                f'<span>{html.escape(str(topic["id"]))}</span> {html.escape(str(topic["title"]))}</a></li>'
                for topic in category_topics
            )
            cards.append(
                f'<section class="catalog-group" id="{tier}-{slugify(category)}">'
                f"<h2>{html.escape(category)}</h2>"
                f"<p>{TIER_LABELS[tier]} · {len(category_topics)} topics</p>"
                f"<ol>{links}</ol></section>"
            )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Architect Design Patterns — Design Principles</title>
  <meta name="description" content="Three hundred architecture and system design essays from basic through advanced.">
  <link rel="canonical" href="https://search4soumya.github.io/knowledge-portfolio/architecture/">
  <link rel="icon" href="../images/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="../css/styles.css">
</head>
<body data-topic="architecture">
  <a class="skip" href="#main">Skip to content</a>
{header("../")}
  <main id="main" class="wrap wrap-wide">
    <p class="kicker">Architecture library</p>
    <div class="title-row">
      <h1>Architect Design Patterns</h1>
      <button type="button" class="nav-toggle" aria-expanded="false" aria-controls="toc">Topics</button>
    </div>
    <p class="deck">Three hundred essays, from shared vocabulary through distributed systems and planet-scale case studies. Choose a topic from the library.</p>
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


def architecture_table(topics: list[dict[str, object]]) -> str:
    lines = [
        "# Architecture topics",
        "",
        "Complete index of the 300 architecture essays sourced from `Eidos-Design-Pattern/src/content/topics`.",
        "",
        "| # | ID | Tier | Category | Topic | Page |",
        "|---:|:---:|:---|:---|:---|:---|",
    ]
    for topic in topics:
        tier = str(topic["tier"])
        slug = str(topic["slug"])
        category = str(topic["category"]).replace("|", "\\|")
        title = str(topic["title"]).replace("|", "\\|")
        lines.append(
            f'| {topic["publishOrder"]} | {topic["id"]} | {TIER_LABELS[tier]} | '
            f'{category} | {title} | [Read](../site/architecture/{tier}/{slug}.html) |'
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        type=Path,
        default=Path(r"C:\Users\spanda\Projects\Eidos-Design-Pattern\src\content\topics"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "site" / "architecture",
    )
    args = parser.parse_args()

    topics = load_topics(args.source)
    if len(topics) != 300:
        raise SystemExit(f"Expected 300 published topics, found {len(topics)}")

    args.output.mkdir(parents=True, exist_ok=True)
    for tier in TIERS:
        tier_dir = args.output / tier
        if tier_dir.exists():
            shutil.rmtree(tier_dir)
        tier_dir.mkdir(parents=True)

    (args.output / "index.html").write_text(overview_page(topics), encoding="utf-8")
    table_path = args.output.parent.parent / "content" / "architecture-topics.md"
    table_path.parent.mkdir(parents=True, exist_ok=True)
    table_path.write_text(architecture_table(topics), encoding="utf-8")
    for index, topic in enumerate(topics):
        previous = topics[index - 1] if index else None
        following = topics[index + 1] if index + 1 < len(topics) else None
        path = args.output / str(topic["tier"]) / f'{topic["slug"]}.html'
        path.write_text(
            article_page(topic, topics, previous, following),
            encoding="utf-8",
        )

    print(f"Generated {len(topics)} architecture article pages plus the overview.")


if __name__ == "__main__":
    main()
