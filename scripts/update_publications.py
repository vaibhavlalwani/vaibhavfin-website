#!/usr/bin/env python3
"""Regenerate the Research & Publications page content from OpenAlex.

Reads scripts/settings.toml, queries the OpenAlex API for the author's
works, and writes three files in the project root:

    _publications.md   ready-to-render publication list (included by research.qmd)
    publications.bib   a BibTeX export offered for download

Run it any time with:

    python scripts/update_publications.py

Requires Python 3.11+ (standard library only, no pip installs).
"""

from __future__ import annotations

import html
import json
import tomllib
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SETTINGS_PATH = Path(__file__).resolve().parent / "settings.toml"

API = "https://api.openalex.org"
MAILTO = "vaibhav@xlri.ac.in"  # OpenAlex "polite pool" contact
USER_AGENT = f"vaibhavfin-site/1.0 (mailto:{MAILTO})"

SECTION_PEER = "Peer-reviewed publications"
SECTION_WORKING = "Working papers & preprints"


# ----------------------------------------------------------------------
# Networking helpers
# ----------------------------------------------------------------------
def api_get(path: str, params: dict | None = None) -> dict:
    query = urllib.parse.urlencode(params or {})
    url = f"{API}{path}" + (f"?{query}" if query else "")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def short_id(openalex_id: str) -> str:
    return openalex_id.rsplit("/", 1)[-1]


def resolve_author(settings: dict) -> dict:
    if settings.get("openalex_author_id"):
        return api_get(f"/authors/{settings['openalex_author_id']}")
    orcid = settings["orcid"]
    data = api_get("/authors", {"filter": f"orcid:{orcid}"})
    results = data.get("results") or []
    if not results:
        raise SystemExit(f"No OpenAlex author found for ORCID {orcid}")
    return results[0]


def fetch_works(author_id: str) -> list[dict]:
    works: list[dict] = []
    cursor = "*"
    select = (
        "id,doi,display_name,title,publication_year,publication_date,type,"
        "authorships,primary_location,best_oa_location,cited_by_count,"
        "is_retracted,biblio"
    )
    while cursor:
        data = api_get(
            "/works",
            {
                "filter": f"author.id:{author_id}",
                "per_page": 200,
                "cursor": cursor,
                "select": select,
            },
        )
        works.extend(data["results"])
        cursor = data["meta"].get("next_cursor")
    return works


# ----------------------------------------------------------------------
# Formatting helpers
# ----------------------------------------------------------------------
def format_authors(work: dict, me_id: str) -> str:
    names: list[str] = []
    for authorship in work.get("authorships", []):
        author = authorship.get("author") or {}
        name = author.get("display_name") or authorship.get("raw_author_name") or ""
        if not name:
            continue
        if short_id(author.get("id") or "") == me_id:
            names.append(f'<span class="me">{html.escape(name)}</span>')
        else:
            names.append(html.escape(name))
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " and " + names[-1]


def format_venue(work: dict) -> str:
    bits: list[str] = []
    source = ((work.get("primary_location") or {}).get("source") or {}).get("display_name")
    if source:
        bits.append(f'<span class="venue">{html.escape(source)}</span>')

    biblio = work.get("biblio") or {}
    volume, issue = biblio.get("volume"), biblio.get("issue")
    first, last = biblio.get("first_page"), biblio.get("last_page")
    detail = ""
    if volume:
        detail += str(volume)
    if issue:
        detail += f"({issue})"
    if first:
        pages = f"{first}\u2013{last}" if last and last != first else str(first)
        detail += (", " if detail else "") + pages
    if detail:
        bits.append(html.escape(detail))

    year = work.get("publication_year")
    if year:
        bits.append(str(year))
    return " \u00b7 ".join(bits)


def render_links(work: dict, extra: dict | None) -> str:
    links: list[tuple[str, str]] = []
    doi = work.get("doi")
    if doi:
        links.append(("DOI", doi))

    landing = (work.get("primary_location") or {}).get("landing_page_url")
    if landing and landing != doi:
        links.append(("Link", landing))

    pdf = (work.get("best_oa_location") or {}).get("pdf_url")
    if pdf:
        links.append(("PDF", pdf))

    for label, url in (extra or {}).items():
        links.append((label.replace("_", " ").capitalize(), url))

    seen: set[str] = set()
    anchors: list[str] = []
    for label, url in links:
        if not url or url in seen:
            continue
        seen.add(url)
        anchors.append(
            f'<a class="pub-link" href="{html.escape(url, quote=True)}">{html.escape(label)}</a>'
        )
    return "".join(anchors)


def render_work(work: dict, me_id: str, settings: dict) -> str:
    wid = short_id(work["id"])
    title = html.escape(work.get("display_name") or work.get("title") or "Untitled")
    authors = format_authors(work, me_id)
    meta = format_venue(work)
    links = render_links(work, (settings.get("links") or {}).get(wid))
    note = (settings.get("notes") or {}).get(wid)

    parts = [f'<div class="pub">', f'  <div class="pub-title">{title}</div>']
    if authors:
        parts.append(f'  <div class="pub-authors">{authors}</div>')
    if meta:
        parts.append(f'  <div class="pub-meta">{meta}</div>')
    if links:
        parts.append(f'  <div class="pub-links">{links}</div>')
    if note:
        parts.append(f'  <div class="pub-note">{html.escape(note)}</div>')
    parts.append("</div>")
    return "\n".join(parts)


def render_section(works: list[dict], me_id: str, settings: dict) -> str:
    if not works:
        return ""
    blocks = ['<div class="pub-list">']
    blocks.extend(render_work(work, me_id, settings) for work in works)
    blocks.append("</div>")
    return "\n".join(blocks)


def render_publications(peer: list[dict], working: list[dict], me_id: str, settings: dict) -> str:
    out: list[str] = []
    if peer:
        out.append(f"## {SECTION_PEER}\n")
        out.append(render_section(peer, me_id, settings))
        out.append("")
    if working:
        out.append(f"## {SECTION_WORKING}\n")
        out.append(render_section(working, me_id, settings))
        out.append("")
    return "\n".join(out).strip() + "\n"


# ----------------------------------------------------------------------
# BibTeX export
# ----------------------------------------------------------------------
BIB_TYPE = {
    "article": "article",
    "review": "article",
    "book": "book",
    "book-chapter": "incollection",
    "thesis": "phdthesis",
    "report": "techreport",
    "preprint": "misc",
}


def bibtex_escape(value: str) -> str:
    return value.replace("{", "\\{").replace("}", "\\}")


def render_bibtex(works: list[dict]) -> str:
    entries: list[str] = []
    for work in works:
        wid = short_id(work["id"])
        entry_type = BIB_TYPE.get(work.get("type", ""), "misc")
        authors = " and ".join(
            (a.get("author") or {}).get("display_name", "")
            for a in work.get("authorships", [])
            if (a.get("author") or {}).get("display_name")
        )
        source = ((work.get("primary_location") or {}).get("source") or {}).get("display_name")
        fields: list[tuple[str, str]] = [("title", work.get("display_name") or "")]
        if authors:
            fields.append(("author", authors))
        if work.get("publication_year"):
            fields.append(("year", str(work["publication_year"])))
        if source:
            fields.append(("journal", source) if entry_type in ("article", "incollection") else ("publisher", source))
        if work.get("doi"):
            fields.append(("doi", work["doi"].replace("https://doi.org/", "")))
        if work.get("doi"):
            fields.append(("url", work["doi"]))
        body = ",\n".join(f"  {k} = {{{bibtex_escape(str(v))}}}" for k, v in fields if v)
        entries.append(f"@{entry_type}{{{wid},\n{body}\n}}")
    return "\n\n".join(entries) + "\n"


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main() -> None:
    settings = tomllib.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    author = resolve_author(settings)
    me_id = short_id(author["id"])

    exclude = {str(x).lower() for x in settings.get("exclude_ids", [])}
    article_types = set(settings.get("article_types", []))
    preprint_types = set(settings.get("preprint_types", []))

    works = fetch_works(me_id)
    works = [
        w
        for w in works
        if short_id(w["id"]).lower() not in exclude and (w.get("doi", "") or "").lower() not in exclude
    ]
    works.sort(key=lambda w: ((w.get("publication_year") or 0), w.get("publication_date") or ""), reverse=True)

    peer = [w for w in works if w.get("type") in article_types]
    working = [w for w in works if w.get("type") in preprint_types]

    (ROOT / "_publications.md").write_text(
        render_publications(peer, working, me_id, settings), encoding="utf-8"
    )
    (ROOT / "publications.bib").write_text(render_bibtex(peer + working), encoding="utf-8")

    print(
        f"Updated: {len(peer)} peer-reviewed, {len(working)} working papers (author {me_id})."
    )


if __name__ == "__main__":
    main()
