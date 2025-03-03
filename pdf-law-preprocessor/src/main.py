import os
import argparse
import logging
import json
import re
from pathlib import Path
from src.preprocessor.extractor import PDFExtractor
from src.preprocessor.cleaner import TextCleaner
from src.preprocessor.mapper import ArticleMapper

def setup_logging(debug=False):
    """Setup logging configuration"""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('pdf_processor.log')
        ]
    )
    return logging.getLogger("PDFProcessor")

def save_to_json(data, filepath):
    """Save data to JSON file"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Process law PDF and extract articles")
    parser.add_argument("--input", type=str, required=True, help="Path to input file (PDF or text)")
    parser.add_argument("--output", type=str, default="output", help="Path to output directory")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(debug=args.debug)
    
    # Create output directory if it doesn't exist
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting preprocessing of {args.input}")
    
    # Extract text from PDF
    extractor = PDFExtractor(logger=logger)
    raw_text = extractor.extract(args.input)
    
    # Save raw extracted text
    with open(output_dir / "raw_text.txt", "w", encoding="utf-8") as f:
        f.write(raw_text)
    logger.info(f"Raw text saved to {output_dir}/raw_text.txt")
    
    # Clean and normalize text
    cleaner = TextCleaner(logger=logger)
    clean_text = cleaner.clean(raw_text)
    
    # Save cleaned text
    with open(output_dir / "clean_text.txt", "w", encoding="utf-8") as f:
        f.write(clean_text)
    logger.info(f"Clean text saved to {output_dir}/clean_text.txt")
    
    # Extract articles and map to content
    mapper = ArticleMapper(logger=logger)
    article_map = mapper.map_articles(clean_text)
    
    # Save article map to JSON
    save_to_json(article_map, output_dir / "article_map.json")
    logger.info(f"Article mapping saved to {output_dir}/article_map.json")
    
    # Save individual articles as separate files
    articles_dir = output_dir / "articles"
    articles_dir.mkdir(exist_ok=True)
    
    for article_num, content in article_map['articles'].items():
        # Clean article number for filename (remove special characters)
        safe_num = re.sub(r'[^\w\.]', '_', article_num)
        with open(articles_dir / f"article_{safe_num}.txt", "w", encoding="utf-8") as f:
            f.write(content)
    
    logger.info(f"Individual articles saved to {articles_dir}")
    logger.info("Preprocessing completed successfully")

if __name__ == "__main__":
    main()