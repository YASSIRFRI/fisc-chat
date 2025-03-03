# FILE: /pdf-law-preprocessor/pdf-law-preprocessor/config/settings.py

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INPUT_DIR = os.path.join(BASE_DIR, 'data', 'input')
OUTPUT_DIR = os.path.join(BASE_DIR, 'data', 'output')

PDF_PROCESSING_SETTINGS = {
    'noise_removal_patterns': [
        r'\s+',  # Remove extra whitespace
        r'\n+',  # Remove new lines
        r'\[.*?\]',  # Remove text in brackets
    ],
    'article_pattern': r'Article\s+\d+',  # Pattern to identify articles
}

TABLE_SETTINGS = {
    'table_row_pattern': r'\|.*?\|',  # Pattern to identify table rows
}

STRUCTURE_SETTINGS = {
    'section_pattern': r'Section\s+\d+',  # Pattern to identify sections
}