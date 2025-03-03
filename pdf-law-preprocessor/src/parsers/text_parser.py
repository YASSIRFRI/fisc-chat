class TextParser:
    def __init__(self, cleaned_text):
        self.cleaned_text = cleaned_text

    def parse_articles(self):
        articles = {}
        current_article = None
        for line in self.cleaned_text.splitlines():
            line = line.strip()
            if self.is_article_header(line):
                current_article = self.extract_article_number(line)
                articles[current_article] = []
            elif current_article:
                articles[current_article].append(line)
        return {k: ' '.join(v) for k, v in articles.items()}

    def is_article_header(self, line):
        # Define the logic to identify article headers (e.g., regex pattern)
        return line.startswith("Article")  # Example pattern

    def extract_article_number(self, line):
        # Extract the article number from the header
        return line.split()[1]  # Example extraction logic