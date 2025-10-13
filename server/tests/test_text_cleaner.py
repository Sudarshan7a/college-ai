import unittest
import sys
from pathlib import Path
from langchain_core.documents import Document

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from server.src.text_cleaner import TextCleaner

class TestTextCleaner(unittest.TestCase):
    def setUp(self):
        self.cleaner = TextCleaner()

    def test_clean_text_noise_removal(self):
        text = """
        Home » SSR 2024 Documents
        Skip to content
        Actual content here.
        Copyright © 2024 All rights reserved
        """
        cleaned = self.cleaner.clean_text(text)
        self.assertNotIn("Home »", cleaned)
        self.assertNotIn("Skip to content", cleaned)
        self.assertNotIn("Copyright", cleaned)
        self.assertIn("Actual content here.", cleaned)

    def test_clean_text_whitespace(self):
        text = "This   is  a   test.\n\n\nNew line."
        cleaned = self.cleaner.clean_text(text)
        self.assertEqual(cleaned, "This is a test.\n\nNew line.")

    def test_is_low_quality(self):
        self.assertTrue(self.cleaner.is_low_quality("Short"))
        self.assertTrue(self.cleaner.is_low_quality("lorem ipsum text"))
        self.assertFalse(self.cleaner.is_low_quality("This is a valid document with enough content to be considered high quality." * 5))

    def test_enhance_metadata(self):
        doc = Document(page_content="This is a sentence. This is another one. Artificial Intelligence is cool.")
        enhanced = self.cleaner.enhance_metadata(doc)
        self.assertEqual(enhanced.metadata['sentence_count'], 3)
        self.assertGreater(enhanced.metadata['word_count'], 10)
        self.assertIn('Artificial Intelligence', [p.replace('\n', ' ') for p in enhanced.metadata.get('key_phrases', [])])

if __name__ == '__main__':
    unittest.main()
