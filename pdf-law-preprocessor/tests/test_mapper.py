import unittest
from src.preprocessor.mapper import Mapper

class TestMapper(unittest.TestCase):

    def setUp(self):
        self.mapper = Mapper()

    def test_map_articles(self):
        # Sample input data
        articles = {
            "Article 1": "This is the text of article 1.",
            "Article 2": "This is the text of article 2."
        }
        expected_output = {
            "Article 1": "This is the text of article 1.",
            "Article 2": "This is the text of article 2."
        }
        output = self.mapper.map_articles(articles)
        self.assertEqual(output, expected_output)

    def test_map_articles_with_noise(self):
        # Sample input data with noise
        articles = {
            "Article 1": "This is the text of article 1. [Noise]",
            "Article 2": "This is the text of article 2. [Noise]"
        }
        expected_output = {
            "Article 1": "This is the text of article 1.",
            "Article 2": "This is the text of article 2."
        }
        output = self.mapper.map_articles(articles)
        self.assertEqual(output, expected_output)

    def test_empty_articles(self):
        # Test with empty articles
        articles = {}
        expected_output = {}
        output = self.mapper.map_articles(articles)
        self.assertEqual(output, expected_output)

if __name__ == '__main__':
    unittest.main()