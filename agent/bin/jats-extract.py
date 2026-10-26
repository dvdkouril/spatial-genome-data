#!/usr/bin/env python3
"""Print the parts of a JATS full-text XML (from Europe PMC) that can point to data.

    jats-extract.py PMCID < article.xml

Used by fulltext.sh. Prints, as plain text:
  - availability sections (data / code / materials availability statements)
  - supplementary files, as full PMC URLs with their captions
  - other sentences mentioning accessions, repositories or deposition
  - data references from the reference list
Links are written out next to their link text, so every URL is visible.
"""
import re
import sys
import xml.etree.ElementTree as ET

XLINK = "{http://www.w3.org/1999/xlink}href"

AVAILABILITY_TITLE = re.compile(r"availab|accession|deposit", re.I)
AVAILABILITY_TYPE = re.compile(r"data-availability|availability", re.I)
DATA_MENTION = re.compile(
    r"\b(GSE\d{3,}|GSM\d{3,}|PRJ[NED][A-Z]?\d+|SR[APRX]\d{4,}|E-[A-Z]{4}-\d+|4DN[A-Z0-9]{6,}|EMD-\d+|PXD\d+)\b"
    r"|zenodo|figshare|github\.com|gitlab|osf\.io|dryad|mendeley data|bitbucket"
    r"|deposited|accession|available (?:at|from|online|on|in|via|upon|on request)|can be (?:downloaded|accessed|found)",
    re.I,
)
MAX_MENTIONS = 40
MAX_REFERENCES = 20


def text(el):
    """Text of an element with whitespace collapsed and link targets written out."""
    parts = []

    def walk(node):
        if node.text:
            parts.append(node.text)
        for child in node:
            if child.tag in ("xref", "fn", "table-wrap", "fig"):
                pass  # citation markers, footnotes, tables and figures are noise here
            else:
                if child.tag == "pub-id":
                    parts.append(" ")  # ids in citations follow each other without spaces
                walk(child)
                href = child.get(XLINK)
                if child.tag in ("ext-link", "uri") and href:
                    shown = "".join(child.itertext()).strip()
                    if href.strip().startswith("http") and href.strip() not in shown:
                        parts.append(f" <{href.strip()}>")
            if child.tail:
                parts.append(child.tail)

    walk(el)
    return re.sub(r"\s+", " ", "".join(parts)).strip()


def title_of(el):
    t = el.find("title")
    return text(t) if t is not None else ""


def sentences(paragraph):
    return re.split(r"(?<=[.;])\s+(?=[A-Z(\[])", paragraph)


def main():
    pmcid = sys.argv[1]
    root = ET.parse(sys.stdin).getroot()
    out = []

    title = root.find(".//article-meta//article-title")
    out.append(f"# {text(title) if title is not None else pmcid}")
    out.append("")

    # Availability sections: by type attribute or by title. Nested ones are printed once.
    sections = []
    for el in root.iter():
        if el.tag not in ("sec", "notes", "fn-group", "app"):
            continue
        kind = el.get("sec-type") or el.get("notes-type") or ""
        if AVAILABILITY_TYPE.search(kind) or AVAILABILITY_TITLE.search(title_of(el)):
            sections.append(el)
    inside = {id(d) for s in sections for d in s.iter() if d is not s}
    seen_text = set()  # sentences already printed
    out.append("## Availability statements")
    printed = 0
    for el in sections:
        if id(el) in inside:
            continue
        body = " ".join(text(p) for p in el.iter("p"))
        new = [x for x in sentences(body) if x not in seen_text]
        if not body or not new:
            continue  # empty, or repeats statements already printed
        seen_text.update(new)
        out.append(f"### {title_of(el) or 'Availability'}")
        out.append(body)
        printed += 1
    if not printed:
        out.append("(none found)")
    out.append("")

    # Supplementary files, as full URLs.
    out.append("## Supplementary files")
    supplements = []
    for sm in root.iter("supplementary-material"):
        media = sm.find(".//media")
        href = (media if media is not None else sm).get(XLINK)
        if not href:
            continue
        label = sm.find("label")
        caption = sm.find(".//caption")
        desc = " ".join(x for x in (text(label) if label is not None else "", text(caption) if caption is not None else "") if x)
        url = href if href.startswith("http") else f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/bin/{href}"
        line = f"- {url}" + (f" : {desc}" if desc else "")
        if line not in supplements:
            supplements.append(line)
    out.extend(supplements or ["(none)"])
    out.append("")

    # Other sentences in the body that mention data, outside the availability sections.
    skip = {id(d) for s in sections for d in s.iter()}
    mentions = []
    body = root.find("body")
    for p in (body.iter("p") if body is not None else []):
        if id(p) in skip:
            continue
        for s in sentences(text(p)):
            if DATA_MENTION.search(s) and s not in mentions and s not in seen_text:
                mentions.append(s)
    out.append("## Other mentions in the text")
    out.extend(f"- {s}" for s in mentions[:MAX_MENTIONS])
    if len(mentions) > MAX_MENTIONS:
        out.append(f"({len(mentions) - MAX_MENTIONS} more not shown)")
    if not mentions:
        out.append("(none)")
    out.append("")

    # Data references: citations typed as data, or citing a repository or accession.
    refs = []
    for ref in root.iter("ref"):
        cit = ref.find("element-citation")
        if cit is None:
            cit = ref.find("mixed-citation")
        if cit is None:
            continue
        t = text(cit)
        if cit.get("publication-type") == "data" or DATA_MENTION.search(t):
            refs.append(t)
    out.append("## Data references")
    out.extend(f"- {r}" for r in refs[:MAX_REFERENCES])
    if not refs:
        out.append("(none)")

    print("\n".join(out))


if __name__ == "__main__":
    main()
