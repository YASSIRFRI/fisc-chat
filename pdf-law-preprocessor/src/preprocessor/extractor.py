import re
import os
import fitz 

class PDFExtractor:
    def __init__(self, logger=None):
        self.logger = logger

    def extract(self, pdf_path):
        """Extract text from a PDF file with special handling for legal documents."""
        if self.logger:
            self.logger.info(f"Extracting text from {pdf_path}")
        
        if not os.path.exists(pdf_path):
            if self.logger:
                self.logger.error(f"PDF file not found: {pdf_path}")
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        try:
            if pdf_path.lower().endswith('.pdf'):
                pdf_document = fitz.open(pdf_path)
                text = ""
                toc_end_page = self._find_toc_end_page(pdf_document)
                for page_num, page in enumerate(pdf_document):
                    if page_num <= toc_end_page:
                        continue
                    if self.logger and page_num % 10 == 0:
                        self.logger.debug(f"Processing page {page_num+1}/{len(pdf_document)}")
                    page_text = page.get_text("text")
                    page_text = self._remove_page_numbers(page_text)
                    
                    tables = page.find_tables()
                    if tables and len(tables.tables) > 0:
                        if self.logger:
                            self.logger.debug(f"Found {len(tables.tables)} tables on page {page_num+1}")
                        for table in tables.tables:
                            table_text = self._process_table(table)
                            page_text += "\n\n" + table_text + "\n\n"
                    
                    page_text = self._process_article_text(page_text)
                    
                    text += page_text + "\n\n"
            else:
                with open(pdf_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                    
                text = self._remove_page_numbers(text)
                text = self._process_article_text(text)
            
            text = self._post_process_text(text)
            
            if self.logger:
                self.logger.info(f"Extracted {len(text)} characters from file")
            
            return text
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error extracting text: {str(e)}")
            raise

    def _find_toc_end_page(self, pdf_document):
        toc_end_page = 0
        for i in range(min(30, len(pdf_document))):
            page_text = pdf_document[i].get_text("text")
            if "TABLE DES MATIÈRES" in page_text or "SOMMAIRE" in page_text:
                toc_end_page = i
                j = i + 1
                while j < min(50, len(pdf_document)):
                    next_text = pdf_document[j].get_text("text")
                    if "ARTICLE PREMIER" in next_text or "TITRE PREMIER" in next_text:
                        return j - 1
                    j += 1
                
        return toc_end_page

    def _remove_page_numbers(self, text):
        """Remove page numbers from text."""
        page_number_pattern = r'\n\d+\n'
        text = re.sub(page_number_pattern, '\n', text)
        header_footer_pattern = r'\n+CODE GÉNÉRAL DES IMPÔTS\n+'
        text = re.sub(header_footer_pattern, '\n', text)
        
        return text

    def _process_table(self, table):
        """Process a detected table and convert it to text representation."""
        rows = []
        for row_cells in table.cells:
            row_text = []
            for cell in row_cells:
                # Extract text from the cell area
                row_text.append(cell.text.strip())
            
            rows.append(" | ".join(row_text))
        
        return "\n".join(ows)

    def _process_article_text(self, text):
        article_pattern = r'(Article\s+\d+[\w\.\-]*)\s*[\.\-]\s*(.*?)(?=\n)'
        text = re.sub(article_pattern, r'\n\n\1.- \2\n', text, flags=re.IGNORECASE)
        section_pattern = r'(SECTION\s+[\w\.\-]+)\s*[\.\-]\s*(.*?)(?=\n)'
        text = re.sub(section_pattern, r'\n\n\1.- \2\n', text)
        chapter_pattern = r'(CHAPITRE\s+[\w\.\-]+)\s*[\.\-]?\s*(.*?)(?=\n)'
        text = re.sub(chapter_pattern, r'\n\n\1.- \2\n', text)
        title_pattern = r'(TITRE\s+[\w\.\-]+)\s*[\.\-]?\s*(.*?)(?=\n)'
        text = re.sub(title_pattern, r'\n\n\1.- \2\n', text)
        
        return text
        
    def _post_process_text(self, text):
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        text = text.replace('I', 'I').replace('l', 'l').replace('O', 'O').replace('0', '0')
        text = re.sub(r'(\.)(\w)', r'\1 \2', text)
        
        return text

    def extract_articles(self, text):
        articles = {}
        
        article_pattern = r'(?:Article|ARTICLE)\s+(\d+[\w\.\-]*)(?:\s*\.-|\s*\:|\s*\-)\s*(.*?)(?=(?:Article|ARTICLE)\s+\d+[\w\.\-]*(?:\s*\.-|\s*\:|\s*\-)|\Z)'
        matches = re.finditer(article_pattern, text, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            article_num = match.group(1)
            content = match.group(2).strip()
            if len(content) < 100 and "........." in content:
                continue
                
            articles[article_num] = content
            
        return articles

    def extract_structure(self, text):
        structure = {
            'titles': [],
            'chapters': [],
            'sections': [],
            'articles': []
        }
        title_pattern = r'TITRE\s+([\w\.\-]+)\s*\.-\s*(.*?)(?=\n)'
        title_matches = re.finditer(title_pattern, text)
        for match in title_matches:
            structure['titles'].append({
                'number': match.group(1),
                'title': match.group(2).strip()
            })
        
        chapter_pattern = r'CHAPITRE\s+([\w\.\-]+)\s*\.-\s*(.*?)(?=\n)'
        chapter_matches = re.finditer(chapter_pattern, text)
        for match in chapter_matches:
            structure['chapters'].append({
                'number': match.group(1),
                'title': match.group(2).strip()
            })
        
        section_pattern = r'SECTION\s+([\w\.\-]+)\s*\.-\s*(.*?)(?=\n)'
        section_matches = re.finditer(section_pattern, text)
        for match in section_matches:
            structure['sections'].append({
                'number': match.group(1),
                'title': match.group(2).strip()
            })
        
        article_pattern = r'Article\s+(\d+[\w\.\-]*)\s*\.-\s*(.*?)(?=\n)'
        article_matches = re.finditer(article_pattern, text, re.IGNORECASE)
        for match in article_matches:
            structure['articles'].append({
                'number': match.group(1),
                'title': match.group(2).strip()
            })
        
        return structure