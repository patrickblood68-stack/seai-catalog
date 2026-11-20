"""Build crawler-readable guides from the catalog's checked evidence."""
import json
from datetime import date
from html import escape
from pathlib import Path
from xml.etree import ElementTree

from render_contractor_directory import render_directory
from render_individual_contractors import ROUTE, render_individual_contractors

OUTPUT = Path("dist")
SITEMAP_NAMESPACE = "http://www.sitemaps.org/schemas/sitemap/0.9"
TOPIC_MARKER = "<!-- TOPIC_GUIDES -->"
FINDER_ROUTE = "/grant-finder/"
FINDER_TOPICS = {
    "Insulation and windows": (
        "individual-grants-attic-insulation", "individual-grants-wall-insulation",
        "individual-grants-windows-and-doors",
    ),
    "Heating and solar": (
        "individual-grants-heat-pump-systems", "individual-grants-solar-electricity-grant",
        "individual-grants-solar-water-heating-grant", "individual-grants-battery",
    ),
    "Whole-home upgrades": (
        "one-stop-shop", "one-stop-shop-multiple-energy-upgrades",
        "one-stop-shop-home-energy-assessments", "one-stop-shop-traditional-homes",
    ),
    "Funding and eligibility": (
        "home-energy-grants", "individual-grants", "individual-grants-support-for-individual-grants",
        "fully-funded-upgrades-for-certain-homeowners", "fully-funded-upgrades-for-eligible-homes",
        "home-energy-upgrade-loan", "eeos-homeowners", "supports-for-landlords",
        "defective-concrete-blocks", "vacant-derelict-homes",
        "homeowners-in-receipt-of-certain-department-of-social-protection-payments",
    ),
}


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def section_html(section):
    details = "".join(f"<li>{escape(detail)}</li>" for detail in section["details"])
    detail_list = f"<ul>{details}</ul>" if details else ""
    return (
        f'<section><h2>{escape(section["heading"])}</h2>'
        f'<p>{escape(section["summary"])}</p>{detail_list}</section>'
    )


def official_links_html(links):
    if not links:
        return ""
    items = []
    for link in links:
        url = escape(link["url"], quote=True)
        label = escape(link["label"])
        items.append(f'<li><a href="{url}">{label}</a></li>')
    return '<section><h2>Official registers</h2><ul>' + "".join(items) + "</ul></section>"


def guide_html(title, record):
    title = escape(title)
    source = escape(record["sourceUrl"], quote=True)
    checked = date.fromisoformat(record["lastCheckedAt"])
    review = date.fromisoformat(record["reviewBy"])
    sections = "\n    ".join(section_html(section) for section in record["sections"])
    return f"""<!doctype html>
<html lang="en-IE">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} | Home energy guides</title>
  <style>
    body {{ margin: 0; background: #f1f5f1; color: #17291f; font-family: system-ui, sans-serif; }}
    main {{ max-width: 45rem; margin: auto; padding: 2rem 1.25rem; }}
    article {{ background: white; border: 1px solid #cbd8cd; padding: clamp(1.25rem, 5vw, 3rem); border-radius: 1rem; }}
    h1 {{ line-height: 1.12; font-size: clamp(2rem, 5vw, 3rem); }}
    p, li {{ line-height: 1.65; }}
    a {{ color: #17533b; text-underline-offset: .18em; }}
  </style>
</head>
<body>
  <main>
    <nav aria-label="Home energy guides"><a href="/#guides">All home energy guides</a></nav>
    <article>
      <h1>{title}</h1>
      {sections}
      {official_links_html(record.get("officialLinks", []))}
      <section aria-labelledby="source">
        <h2 id="source">Official source</h2>
        <p><a href="{source}">Read the full guidance on SEAI</a>.</p>
        <p>Source checked <time datetime="{checked}">{checked:%d %B %Y}</time>.
          Review due <time datetime="{review}">{review:%d %B %Y}</time>.
          For changes after the check date, consult SEAI directly.</p>
      </section>
    </article>
  </main>
</body>
</html>
"""


def finder_html(sources, guide_ids):
    options = []
    cards = []
    for topic, source_ids in FINDER_TOPICS.items():
        topic = escape(topic)
        options.append(f'<option value="{topic}">{topic}</option>')
        for source_id in source_ids:
            source = sources[source_id]
            title = escape(source["title"])
            description = escape(source["description"] or "")
            url = escape(source["sourceUrl"])
            keywords = escape(" ".join(heading["title"] for heading in source["headings"]))
            guide = (
                f'<a href="/guides/{source_id}/">Read the local guide</a>'
                if source_id in guide_ids else ""
            )
            cards.append(
                f'<li class="card" data-topic="{topic}" data-keywords="{keywords}">'
                f'<small>{topic}</small><h2>{title}</h2><p>{description}</p>'
                f'<footer><a href="{url}" aria-label="Official SEAI guidance for {title}">'
                f'Official SEAI guidance</a>{guide}</footer></li>'
            )
    template = Path("public/grant-finder.html").read_text(encoding="utf-8")
    return template.replace("<!-- TOPICS -->", "\n".join(options)).replace(
        "<!-- RESULTS -->", "\n".join(cards)
    )


def render():
    catalog = load("catalog.json")
    evidence = load(catalog["evidence"]["records"])
    sources = {page["id"]: page for dataset in catalog["datasets"]
               for page in load(dataset["records"])}
    sitemap = ElementTree.parse("public/sitemap.xml")
    namespace = f"{{{SITEMAP_NAMESPACE}}}"
    origin = sitemap.getroot().findtext(f"{namespace}url/{namespace}loc").rstrip("/")
    render_directory(OUTPUT)
    render_individual_contractors(OUTPUT)
    finder = OUTPUT / FINDER_ROUTE.strip("/")
    finder.mkdir(parents=True, exist_ok=True)
    guide_ids = {record["sourcePageId"] for record in evidence}
    (finder / "index.html").write_text(finder_html(sources, guide_ids), encoding="utf-8")
    url = ElementTree.SubElement(sitemap.getroot(), f"{namespace}url")
    ElementTree.SubElement(url, f"{namespace}loc").text = origin + FINDER_ROUTE
    route = "/contractors/"
    links = [
        f'<li><a href="{FINDER_ROUTE}">Find a home energy grant</a></li>',
        f'<li><a href="{route}">Find a contractor or One Stop Shop</a></li>',
    ]
    url = ElementTree.SubElement(sitemap.getroot(), f"{namespace}url")
    ElementTree.SubElement(url, f"{namespace}loc").text = origin + route
    url = ElementTree.SubElement(sitemap.getroot(), f"{namespace}url")
    ElementTree.SubElement(url, f"{namespace}loc").text = origin + ROUTE
    for record in evidence:
        source_id = record["sourcePageId"]
        title = record.get("title") or sources[source_id]["title"]
        route = f"/guides/{source_id}/"
        directory = OUTPUT / route.strip("/")
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "index.html").write_text(guide_html(title, record), encoding="utf-8")
        links.append(f'<li><a href="{route}">{escape(title)}</a></li>')
        url = ElementTree.SubElement(sitemap.getroot(), f"{namespace}url")
        ElementTree.SubElement(url, f"{namespace}loc").text = origin + route
    ElementTree.register_namespace("", SITEMAP_NAMESPACE)
    ElementTree.indent(sitemap)
    sitemap.write(OUTPUT / "sitemap.xml", encoding="utf-8", xml_declaration=True)

    home = Path("public/index.html").read_text(encoding="utf-8")
    if home.count(TOPIC_MARKER) != 1:
        raise ValueError("Expected one topic guide marker in the homepage")
    guide_index = '<nav id="guides" aria-labelledby="guide-title"><h2 id="guide-title">Home energy guides</h2><ul>'
    guide_index += "\n".join(links) + "</ul></nav>"
    (OUTPUT / "index.html").write_text(home.replace(TOPIC_MARKER, guide_index), encoding="utf-8")

    pilot = next(record for record in evidence
                 if record["sourcePageId"] == "individual-grants-attic-insulation")
    (OUTPUT / "catalog.json").write_text(
        json.dumps({"featuredEvidence": pilot, **catalog}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    render()
