#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract TITRE → CHAPITRE/PREAMBULE → Article hierarchy from cleaned.pdf
and dump it to cgi_structure.json

pip install pymupdf
"""
from __future__ import annotations
import json, re
from pathlib import Path
import fitz                                    # PyMuPDF
# ────────────────────────────────────────────────────────────────────────────
PDF_PATH = Path("cleaned.pdf")
OUTPUT   = Path("cgi_structure.json")
# ────────────────────────────────────────────────────────────────────────────
def is_blue(rgb: int) -> bool:                 # heuristic – tweak if needed
    r, g, b = (rgb >> 16) & 255, (rgb >> 8) & 255, rgb & 255
    return b > 120 and r < 100 and g < 150

ARTICLE_RX   = re.compile(r"^\s*Article\s+(?:\d+|premier)\b", re.I)
TITRE_RX     = re.compile(r"^\s*TITRE\b",                        re.I)
CHAP_RX      = re.compile(r"^\s*CHAPITRE\b",                     re.I)
PREAMB_RX    = re.compile(r"^\s*PREAMBULE\b",                    re.I)
# ---------------------------------------------------------------------------

def flush_article(bag, titre, chap, art_id, art_name, buf):
    if not (titre and chap and art_id):           # ignore orphan chunks
        return
    t = next((t for t in bag if t["titre"] == titre), None)
    if t is None:
        t = {"titre": titre, "chapitres": []}
        bag.append(t)

    c = next((c for c in t["chapitres"] if c["chapitre"] == chap), None)
    if c is None:
        c = {"chapitre": chap, "articles": []}
        t["chapitres"].append(c)

    c["articles"].append({
        "id":      art_id,
        "name":    art_name,
        "content": " ".join(buf).strip()
    })

def iter_lines(doc: fitz.Document):
    for page in doc:
        for block in page.get_text("dict")["blocks"]:
            if block["type"]:
                continue
            for line in block["lines"]:
                txt  = "".join(s["text"] for s in line["spans"]).strip()
                blue = any(is_blue(s["color"]) for s in line["spans"])
                yield txt, blue
# ---------------------------------------------------------------------------

def collect_structure(pdf: Path):
    structure              = []
    current_title          = None
    current_chapitre       = None
    current_art_id         = None
    current_art_name       = None
    art_buf                = []

    title_build, chap_build = [], []             # temporary accumulators

    with fitz.open(pdf) as doc:
        for txt, blue in iter_lines(doc):
            # ───────────────────────────── article headings ─────────────────
            if ARTICLE_RX.match(txt):
                # Finalise any title/chapitre still being built
                if title_build:
                    current_title = " – ".join(title_build); title_build.clear()
                if chap_build:
                    current_chapitre = " – ".join(chap_build); chap_build.clear()

                # Flush previous article
                flush_article(structure, current_title, current_chapitre,
                              current_art_id, current_art_name, art_buf)
                art_buf.clear()

                head, _, rest = txt.partition(".-")
                current_art_id   = head.strip()
                current_art_name = rest.strip()
                continue

            # ───────────────────────────── blue headings ───────────────────
            if blue:
                # ── TITRE start
                if TITRE_RX.match(txt):
                    if title_build:                           # close prior
                        current_title = " – ".join(title_build)
                        title_build.clear()
                    if chap_build:                            # new titre resets chap
                        current_chapitre = " – ".join(chap_build)
                        chap_build.clear()
                    title_build = [txt]
                    continue

                # ── CHAPITRE / PREAMBULE start
                if CHAP_RX.match(txt) or PREAMB_RX.match(txt):
                    if chap_build:
                        current_chapitre = " – ".join(chap_build)
                        chap_build.clear()
                    chap_build = [txt]
                    continue

                # ── continuation line (still blue but neither TITRE/CHAP/ART)
                if title_build:
                    title_build.append(txt)
                elif chap_build:
                    chap_build.append(txt)
                # otherwise it belongs to the big introduction we ignore
                continue

            # ───────────────────────────── body text (non-blue) ────────────
            if title_build:
                current_title = " – ".join(title_build); title_build.clear()
            if chap_build:
                current_chapitre = " – ".join(chap_build); chap_build.clear()

            if current_art_id:                 # inside an article
                art_buf.append(txt)

        # EOF – flush everything that’s still open
        flush_article(structure, current_title, current_chapitre,
                      current_art_id, current_art_name, art_buf)

    return structure
# ---------------------------------------------------------------------------

def main():
    if not PDF_PATH.exists():
        raise SystemExit(f"{PDF_PATH} not found")
    data = collect_structure(PDF_PATH)
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                      encoding="utf-8")
    print(f"{len(data)} titres exported → {OUTPUT.resolve()}")

if __name__ == "__main__":
    main()
