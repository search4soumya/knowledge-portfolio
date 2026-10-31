"""Split each non-architecture tile into an overview and one HTML file per subtopic."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

from generate_architecture_pages import connect_section, header


TILES = ("cloud", "kubernetes", "ai-ml", "microservices", "devops", "case-study", "learning-path")


def import_existing(site: Path, destination: Path) -> None:
    data: dict[str, object] = {}
    for tile in TILES:
        source = site / tile / "index.html"
        text = source.read_text(encoding="utf-8")
        title = re.search(r"<h1>(.*?)</h1>", text, re.S)
        deck = re.search(r'<p class="deck">(.*?)</p>', text, re.S)
        kicker = re.search(r'<p class="kicker">(.*?)</p>', text, re.S)
        nav = dict(re.findall(r'<a href="#([^"]+)">(.*?)</a>', text, re.S))
        sections = re.findall(
            r'<section id="([^"]+)" data-section(?: class="is-active")?>(.*?)</section>',
            text,
            re.S,
        )
        if not title or not deck or not kicker or not sections:
            raise ValueError(f"Could not import sections from {source}")
        data[tile] = {
            "title": title.group(1).strip(),
            "deck": deck.group(1).strip(),
            "kicker": kicker.group(1).strip(),
            "sections": [
                {
                    "slug": slug,
                    "label": re.sub(r"<[^>]+>", "", nav.get(slug, slug)).strip(),
                    "html": body.strip(),
                }
                for slug, body in sections
            ],
        }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Imported source sections to {destination}")


def topic_nav(tile: str, sections: list[dict[str, str]], current: str | None) -> str:
    lines = [
        '<nav id="toc" class="toc" aria-labelledby="toc-title">',
        '<p id="toc-title" class="toc-title">Subtopics</p>',
        f'<a href="index.html"{" aria-current=\"page\"" if current is None else ""}>Overview</a>',
    ]
    for section in sections:
        marker = ' aria-current="page"' if current == section["slug"] else ""
        lines.append(
            f'<a href="{section["slug"]}.html"{marker}>{html.escape(section["label"])}</a>'
        )
    lines.append("</nav>")
    return "\n".join(lines)


def frame(
    *,
    tile: str,
    title: str,
    deck: str,
    kicker: str,
    navigation: str,
    content: str,
    canonical: str,
) -> str:
    safe_title = html.escape(title)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title} — Knowledge Portfolio</title>
  <meta name="description" content="{html.escape(re.sub(r'<[^>]+>', '', deck))}">
  <link rel="canonical" href="{canonical}">
  <link rel="icon" href="../images/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="../css/styles.css">
</head>
<body data-topic="{html.escape(tile)}">
  <a class="skip" href="#main">Skip to content</a>
{header("../")}
  <main id="main" class="wrap wrap-wide">
    <p class="kicker">{kicker}</p>
    <div class="title-row">
      <h1>{safe_title}</h1>
      <button type="button" class="nav-toggle" aria-expanded="false" aria-controls="toc">Subtopics</button>
    </div>
    <p class="deck">{deck}</p>
    <div class="reader">
{navigation}
{content}
    </div>
  </main>
{connect_section()}
  <script src="../js/reader.js"></script>
</body>
</html>
"""


def overview_content(title: str, sections: list[dict[str, str]]) -> str:
    links = "".join(
        f'<li><a href="{section["slug"]}.html">'
        f'<strong>{html.escape(section["label"])}</strong>'
        "<span>Open this note →</span></a></li>"
        for section in sections
    )
    return f"""      <article class="note topic-article topic-overview">
        <h2>{html.escape(title)} subtopics</h2>
        <p>Each subtopic is a separate HTML page. Choose one from this list or from the left navigation.</p>
        <ol class="subtopic-list">{links}</ol>
      </article>"""


def article_content(
    section: dict[str, str],
    previous: dict[str, str] | None,
    following: dict[str, str] | None,
) -> str:
    pager = ['<nav class="article-pager" aria-label="Adjacent subtopics">']
    if previous:
        pager.append(
            f'<a href="{previous["slug"]}.html">← '
            f'<span>{html.escape(previous["label"])}</span></a>'
        )
    else:
        pager.append("<span></span>")
    if following:
        pager.append(
            f'<a class="next" href="{following["slug"]}.html">'
            f'<span>{html.escape(following["label"])}</span> →</a>'
        )
    pager.append("</nav>")
    return (
        '      <article class="note topic-article">\n'
        + section["html"]
        + "\n"
        + "".join(pager)
        + "\n      </article>"
    )


def generate(site: Path, source_json: Path) -> None:
    data: dict[str, dict[str, object]] = json.loads(source_json.read_text(encoding="utf-8"))
    generated = 0
    for tile in TILES:
        topic = data[tile]
        title = str(topic["title"])
        deck = str(topic["deck"])
        kicker = str(topic["kicker"])
        sections: list[dict[str, str]] = topic["sections"]  # type: ignore[assignment]
        output = site / tile
        output.mkdir(parents=True, exist_ok=True)

        (output / "index.html").write_text(
            frame(
                tile=tile,
                title=title,
                deck=deck,
                kicker=kicker,
                navigation=topic_nav(tile, sections, None),
                content=overview_content(title, sections),
                canonical=f"https://search4soumya.github.io/knowledge-portfolio/{tile}/",
            ),
            encoding="utf-8",
        )
        for index, section in enumerate(sections):
            previous = sections[index - 1] if index else None
            following = sections[index + 1] if index + 1 < len(sections) else None
            (output / f'{section["slug"]}.html').write_text(
                frame(
                    tile=tile,
                    title=f'{title}: {section["label"]}',
                    deck=deck,
                    kicker=kicker,
                    navigation=topic_nav(tile, sections, section["slug"]),
                    content=article_content(section, previous, following),
                    canonical=(
                        "https://search4soumya.github.io/knowledge-portfolio/"
                        f'{tile}/{section["slug"]}.html'
                    ),
                ),
                encoding="utf-8",
            )
            generated += 1
    print(f"Generated {generated} subtopic pages and {len(TILES)} overviews.")


def main() -> None:
    project = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", type=Path, default=project / "site")
    parser.add_argument(
        "--source-json",
        type=Path,
        default=project / "content" / "manual_topics.json",
    )
    parser.add_argument("--import-existing", action="store_true")
    args = parser.parse_args()
    if args.import_existing:
        import_existing(args.site, args.source_json)
    generate(args.site, args.source_json)


if __name__ == "__main__":
    main()
