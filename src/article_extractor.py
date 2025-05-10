#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Extract blue-coloured article headings from cleaned.pdf and write them
to articles.json as a list of {title, content} objects.

Requirements
------------
pip install pymupdf   # aka 'fitz'
"""

import json
import re
from pathlib import Path
import fitz  # PyMuPDF

PDF_PATH  = Path("cleaned.pdf")
OUTPUT    = Path("articles.json")

# --------------------------------------------------------------------------- #
# Adjust these two things if your document’s blue is different
# --------------------------------------------------------------------------- #
def is_blue(rgb_int: int) -> bool:
    """Return True if the colour is 'blue-ish' (heuristic)."""
    r = (rgb_int >> 16) & 255
    g = (rgb_int >> 8)  & 255
    b =  rgb_int        & 255
    return b > 120 and r < 100 and g < 150      # tweak if necessary

ARTICLE_RX = re.compile(r"^\s*Article\s+\d+\b", re.I)
# --------------------------------------------------------------------------- #

def iter_lines(pdf):
    """
    Yield (text, is_article_heading) for every logical line in reading order.
    `is_article_heading` is True only when at least one span in the line:
        • starts with "Article <number>"
        • is printed in blue-ish colour
    """
    for page in pdf:
        for block in page.get_text("dict")["blocks"]:
            if block["type"] != 0:          # 0 = text
                continue
            for line in block["lines"]:
                full = "".join(span["text"] for span in line["spans"]).strip()
                # Does any *span* qualify as a blue Article heading?
                heading = any(
                    is_blue(span["color"]) and ARTICLE_RX.match(span["text"])
                    for span in line["spans"]
                )
                yield full, heading


def collect_articles(pdf_path: Path):
    articles = []
    title, buffer = None, []

    with fitz.open(pdf_path) as doc:
        for text, is_heading in iter_lines(doc):
            if is_heading:
                if title is not None:                 # flush previous
                    articles.append(
                        {"title": title, "content": " ".join(buffer).strip()}
                    )
                    buffer.clear()
                title = text
            else:
                if title is not None:                 # ignore pre-amble
                    buffer.append(text)

        # final flush
        if title is not None:
            articles.append({"title": title, "content": " ".join(buffer).strip()})

    return articles


def main():
    if not PDF_PATH.exists():
        raise SystemExit(f"{PDF_PATH} not found – put the PDF here first.")

    data = collect_articles(PDF_PATH)
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
    print(f"Extracted {len(data)} articles → {OUTPUT.resolve()}")


if __name__ == "__main__":
    main()
