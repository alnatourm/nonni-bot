import io
import unittest

from docx import Document

from app.documents import extract_document


class DocumentTests(unittest.TestCase):
    def test_text_document(self):
        self.assertEqual(extract_document(b"hello", "note.txt", 100), "hello")

    def test_docx_document(self):
        output = io.BytesIO()
        document = Document()
        document.add_paragraph("Nonni document")
        document.save(output)
        self.assertIn("Nonni document", extract_document(output.getvalue(), "x.docx", 100))

    def test_rejects_unsupported_type(self):
        with self.assertRaises(ValueError):
            extract_document(b"data", "file.exe", 100)
