import unittest
from src.preprocessor.cleaner import Cleaner

class TestCleaner(unittest.TestCase):
    def setUp(self):
        self.cleaner = Cleaner()

    def test_remove_noise(self):
        noisy_text = "This is some noisy text!!! @#$%^&*()"
        expected_cleaned_text = "This is some noisy text"
        cleaned_text = self.cleaner.remove_noise(noisy_text)
        self.assertEqual(cleaned_text, expected_cleaned_text)

    def test_preserve_structure(self):
        structured_text = "Article 1: Introduction\nArticle 2: Background"
        expected_cleaned_text = "Article 1: Introduction\nArticle 2: Background"
        cleaned_text = self.cleaner.clean(structured_text)
        self.assertEqual(cleaned_text, expected_cleaned_text)

    def test_formatting_issues(self):
        text_with_formatting_issues = "Article 1: \n\nThis is the content.\n\n\nArticle 2: This is the next article."
        expected_cleaned_text = "Article 1: This is the content.\nArticle 2: This is the next article."
        cleaned_text = self.cleaner.clean(text_with_formatting_issues)
        self.assertEqual(cleaned_text, expected_cleaned_text)

if __name__ == '__main__':
    unittest.main()