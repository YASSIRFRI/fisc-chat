import re

class TextCleaner:
    def __init__(self, logger=None):
        self.logger = logger
    
    def clean(self, text):
        """Clean the extracted text."""
        if self.logger:
            self.logger.info("Cleaning extracted text")
            
        text = self._remove_headers_footers(text)
        
        text = self._fix_ocr_errors(text)
        
        text = self._normalize_whitespace(text)
        
        text = self._fix_article_formatting(text)
        
        text = self._remove_duplicates(text)
        
        return text
    
    def _remove_headers_footers(self, text):
        """Remove headers and footers from the text."""
        text = re.sub(r'\n\d+\n', '\n', text)
        
        patterns = [
            r'\nCODE GÉNÉRAL DES IMPÔTS\n',
            r'\n\d+ CODE GÉNÉRAL DES IMPÔTS\n',
            r'\nBulletin Officiel\n'
        ]
        
        for pattern in patterns:
            text = re.sub(pattern, '\n', text)
            
        return text
    
    def _fix_ocr_errors(self, text):
        """Fix common OCR errors."""
        replacements = {
            '0': 'O',  
            'rn': 'm',
            'ii': 'n',
            '—': '-',
            '–': '-',
            '•': '-',
        }
        
        for old, new in replacements.items():
            if old == '0' and new == 'O':
                pattern = r'([A-Za-z])0([A-Za-z])'
                text = re.sub(pattern, r'\1O\2', text)
            else:
                text = text.replace(old, new)
            
        return text
    
    def _normalize_whitespace(self, text):
        """Normalize whitespace in the text."""
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'(\.)([A-Z])', r'\1 \2', text)
        
        return text
    
    def _fix_article_formatting(self, text):
        text = re.sub(r'(ARTICLE\s+\d+[\w\.\-]*)\s*[\.\-]\s*', r'\n\1.- ', text)
        
        text = re.sub(r'(SECTION\s+[\w\.\-]+)\s*[\.\-]\s*', r'\n\1.- ', text)
        
        text = re.sub(r'(CHAPITRE\s+[\w\.\-]+)\s*[\.\-]?\s*', r'\n\1.- ', text)
        
        text = re.sub(r'(TITRE\s+[\w\.\-]+)\s*[\.\-]?\s*', r'\n\1.- ', text)
        
        return text
    
    def _remove_duplicates(self, text):
        """Remove duplicate paragraphs that might have been extracted multiple times."""
        lines = text.split('\n')
        unique_lines = []
        prev_line = ""
        
        for line in lines:
            if line.strip() and line.strip() != prev_line.strip():
                unique_lines.append(line)
                if line.strip():
                    prev_line = line
            else:
                if not line.strip():
                    unique_lines.append(line)
        
        return '\n'.join(unique_lines)