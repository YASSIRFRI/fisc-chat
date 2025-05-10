import fitz  # PyMuPDF
import re
import json
import sys

def preprocess_pdf(input_pdf, output_pdf):
    """
    Create a processed PDF with:
    1. Notes/footnotes removed (identified by smaller font size)
    2. All images, tables and figures removed
    """
    doc = fitz.open(input_pdf)
    
    for page_num, page in enumerate(doc):
        # 1. Remove all images
        for img in page.get_images(full=True):
            xref = img[0]
            page.delete_image(xref)
        
        # 2. Process text by identifying footnotes based on font size
        blocks = page.get_text("dict")["blocks"]
        main_text_sizes = []
        
        # First pass: determine the main text font size
        for block in blocks:
            if block.get("type") == 0:  # Text block
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        size = span.get("size", 0)
                        if size > 0:  # Skip empty spans
                            main_text_sizes.append(size)
        
        # Calculate the main text size (using median to avoid outliers)
        if main_text_sizes:
            main_text_sizes.sort()
            main_font_size = main_text_sizes[len(main_text_sizes) // 2]  # Median
            small_font_threshold = main_font_size * 0.85  # Text 15% smaller is considered footnote
            
            # Second pass: identify and redact footnotes
            for block in blocks:
                if block.get("type") == 0:  # Text block
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            size = span.get("size", 0)
                            # If this span uses a small font, it's likely a footnote
                            if 0 < size < small_font_threshold:
                                bbox = fitz.Rect(span.get("bbox"))
                                if bbox:
                                    page.add_redact_annot(bbox, fill=(1, 1, 1))
        
        # 3. Also detect and remove horizontal lines (often separate footnotes)
        drawings = page.get_drawings()
        for d in drawings:
            if d.get("type") == "line" or d.get("type") == "rect":
                bbox = d.get("rect")
                if bbox:
                    page.add_redact_annot(bbox, fill=(1, 1, 1))
        
        # Apply all redactions
        page.apply_redactions()
    
    doc.save(output_pdf)
    doc.close()

def extract_articles(pdf_path):
    """
    Extracts PREAMBULE and ARTICLE sections into list of dicts.
    """
    doc = fitz.open(pdf_path)
    text = "\n".join(p.get_text() for p in doc)

    entries = []
    pat = re.compile(
        r"(ARTICLE\s+(?:\d+|PREMIER)[^\n]*)\s*([\s\S]*?)(?=(ARTICLE\s+(?:\d+|PREMIER)\b)|\Z)",
        re.IGNORECASE
    )
    first = pat.search(text)
    if first:
        preamble = text[: first.start()].strip()
        if preamble:
            entries.append({"article": "preamble", "heading": "PREAMBULE", "text": preamble})
    for m in pat.finditer(text):
        heading = m.group(1).strip()
        body = m.group(2).strip()
        idm = re.match(r'ARTICLE\s+(\d+|PREMIER)', heading, re.IGNORECASE)
        aid = idm.group(1).lower() if idm else heading
        entries.append({"article": aid, "heading": heading, "text": body})
    return entries

def main():
    input_pdf = "./input/cgi_cleaned.pdf"
    cleaned_pdf = "./cleaned.pdf"
    output_json = sys.argv[3] if len(sys.argv) > 3 else "articles.json"

    # 1) Preprocess PDF to remove footnotes, images, tables
    preprocess_pdf(input_pdf, cleaned_pdf)

    # 2) Extract articles JSON
    data = extract_articles(cleaned_pdf)

    # 3) Write JSON
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()