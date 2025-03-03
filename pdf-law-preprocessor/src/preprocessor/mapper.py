import re

class ArticleMapper:
    def __init__(self, logger=None):
        self.logger = logger
    
    def map_articles(self, text):
        """Map articles and their content from the text."""
        if self.logger:
            self.logger.info("Mapping articles to their content")
            
        # Extract article content using regex
        articles = {}
        
        # Match article numbers and content
        # This pattern looks for ARTICLE followed by number, then captures all text until the next article
        article_pattern = r'ARTICLE\s+(\d+[\w\.\-]*)\s*\.-\s*(.*?)(?=ARTICLE\s+\d+[\w\.\-]*\s*\.-|$)'
        matches = re.finditer(article_pattern, text, re.DOTALL)
        
        for match in matches:
            article_num = match.group(1)
            content = match.group(2).strip()
            
            # Clean up the article content
            content = self._clean_article_content(content)
            
            articles[article_num] = content
        
        # Also parse the structure (titles, chapters, sections)
        structure = self._extract_structure(text)
        
        return {
            'articles': articles,
            'structure': structure
        }
    
    def _clean_article_content(self, content):
        """Clean the article content."""
        # Remove excess whitespace
        content = re.sub(r' {2,}', ' ', content)
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Fix paragraph formatting
        content = re.sub(r'(\d+)[°\)\.-]\s*', r'\n\1) ', content)
        
        # Fix bullet points
        content = re.sub(r'[-•]\s*', r'\n- ', content)
        
        return content.strip()
    
    def _extract_structure(self, text):
        """Extract the document structure (titles, chapters, sections)."""
        structure = {
            'titles': {},
            'chapters': {},
            'sections': {}
        }
        
        # Extract titles
        title_pattern = r'TITRE\s+([\w\.\-]+)\s*\.-\s*(.*?)(?=\n)'
        title_matches = re.finditer(title_pattern, text)
        for match in title_matches:
            structure['titles'][match.group(1)] = match.group(2).strip()
        
        # Extract chapters
        chapter_pattern = r'CHAPITRE\s+([\w\.\-]+)\s*\.-\s*(.*?)(?=\n)'
        chapter_matches = re.finditer(chapter_pattern, text)
        for match in chapter_matches:
            structure['chapters'][match.group(1)] = match.group(2).strip()
        
        # Extract sections
        section_pattern = r'SECTION\s+([\w\.\-]+)\s*\.-\s*(.*?)(?=\n)'
        section_matches = re.finditer(section_pattern, text)
        for match in section_matches:
            structure['sections'][match.group(1)] = match.group(2).strip()
        
        return structure