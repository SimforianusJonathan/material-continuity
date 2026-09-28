import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCUMENT_DIR = ROOT / "data" / "documents"


class DocumentCorpusIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (DOCUMENT_DIR / "manifest.json").read_text(encoding="utf-8")
        )

    def test_manifest_defines_exactly_twelve_unique_documents(self):
        documents = self.manifest["documents"]
        self.assertEqual(12, len(documents))
        self.assertEqual(12, len({item["filename"] for item in documents}))
        self.assertEqual(12, len({item["document_id"] for item in documents}))

    def test_manifest_metadata_and_pdf_checksums_are_current(self):
        for item in self.manifest["documents"]:
            with self.subTest(filename=item["filename"]):
                path = DOCUMENT_DIR / item["filename"]
                self.assertTrue(path.is_file())
                self.assertGreater(path.stat().st_size, 4_000)
                self.assertGreaterEqual(item["page_count"], 2)
                self.assertTrue(item["revision"])
                self.assertTrue(item["effective_date"])
                self.assertEqual(
                    item["sha256"], hashlib.sha256(path.read_bytes()).hexdigest()
                )
                self.assertTrue(path.read_bytes().startswith(b"%PDF-"))

    def test_no_untracked_pdf_is_present_in_corpus_directory(self):
        expected = {item["filename"] for item in self.manifest["documents"]}
        actual = {path.name for path in DOCUMENT_DIR.glob("*.pdf")}
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
