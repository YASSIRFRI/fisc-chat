import unittest
from src.preprocessor.extractor import Extractor

class TestExtractor(unittest.TestCase):

    def setUp(self):
        self.extractor = Extractor()

    def test_extract_text(self):
        # Test extraction of text from a sample PDF
        sample_pdf_path = 'data/input/sample.pdf'
        extracted_text = self.extractor.extract_text(sample_pdf_path)
        self.assertIsInstance(extracted_text, str)
        self.assertGreater(len(extracted_text), 0)

    def test_handle_noise(self):
        # Test that noise is handled correctly
        noisy_text = "This is some noisy text!!! @#$%^&*()"
        cleaned_text = self.extractor.clean_noise(noisy_text)
        self.assertNotIn("!!!", cleaned_text)
        self.assertNotIn("@#$%^&*()", cleaned_text)

    def test_extract_structure(self):
        # Test that the structure of the document is preserved
        sample_pdf_path = 'data/input/sample.pdf'
        extracted_text = self.extractor.extract_text(sample_pdf_path)
        structured_output = self.extractor.extract_structure(extracted_text)
        self.assertIsInstance(structured_output, dict)
        self.assertIn('articles', structured_output)

if __name__ == '__main__':
    unittest.main()