#!/usr/bin/env python3
"""Convert a JATS full-text XML (from Europe PMC) to plain text, without leaving anything out.

    jats-to-text.py PMCID < article.xml > paper.txt

Only mechanical changes: section titles become Markdown headings, every
paragraph, table row and reference becomes one line, link targets are written
next to their link text, and supplementary files are listed with full URLs.
Publishing metadata (authors, affiliations, dates, license) is skipped.
"""
import re
import sys
import xml.etree.ElementTree as ET

XLINK = "{http://www.w3.org/1999/xlink}href"
SKIP = {"journal-meta", "contrib-group", "aff", "author-notes", "history", "permissions",
        "pub-date", "article-id", "article-categories", "funding-group", "counts",
        "custom-meta-group", "kwd-group", "self-uri", "tex-math",
        "{http://www.w3.org/1998/Math/MathML}math"}
SECTIONS = {"sec", "abstract", "app", "ack", "notes", "ref-list", "fn-group", "glossary", "boxed-text"}
LINES = {"p", "tr", "ref", "label", "fn", "list-item", "def-item"}


def inline(el, pmcid):
    """Text of el on one line, with link targets and supplementary file URLs written out."""
    parts = [el.text or ""]
    for child in el:
        if child.tag in SKIP:
            pass
        elif child.tag == "supplementary-material":
            parts.append(" " + supplement(child, pmcid) + " ")
        else:
            parts.append(inline(child, pmcid))
            href = (child.get(XLINK) or "").strip()
            if child.tag in ("ext-link", "uri") and href.startswith("http") and href not in "".join(child.itertext()):
                parts.append(f" <{href}>")
            if child.tag in ("td", "th", "pub-id"):
                parts.append(" | " if child.tag != "pub-id" else " ")
        parts.append(child.tail or "")
    return re.sub(r"\s+", " ", "".join(parts)).strip()


def supplement(el, pmcid):
    media = el.find(".//media")
    href = ((media if media is not None else el).get(XLINK) or "").strip()
    url = href if href.startswith("http") or not href else f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/bin/{href}"
    return f"Supplementary file: {url} : {inline(el, pmcid)}".rstrip(" :")


def walk(el, level, pmcid, out):
    if el.tag in SKIP:
        return
    if el.tag == "article-title":
        out.append(f"# {inline(el, pmcid)}")
    elif el.tag == "title":
        out.append(f"{'#' * min(level, 6)} {inline(el, pmcid)}")
    elif el.tag == "supplementary-material":
        out.append(supplement(el, pmcid))
    elif el.tag in LINES:
        out.append(inline(el, pmcid))
    else:
        if el.tag == "abstract" and el.find("title") is None:
            out.append(f"{'#' * min(level + 1, 6)} Abstract")
        for child in el:
            walk(child, level + 1 if el.tag in SECTIONS else level, pmcid, out)


def main():
    pmcid = sys.argv[1]
    out = []
    walk(ET.parse(sys.stdin).getroot(), 1, pmcid, out)
    print("\n\n".join(line for line in out if line.strip("# ")))


if __name__ == "__main__":
    main()
