import unittest

from g5_programas.pdf_service import _pdf_text


class PdfTextTests(unittest.TestCase):
    def test_html_entities_are_decoded_before_pdf_markup_escaping(self):
        self.assertEqual(
            _pdf_text("R&D &amp; Química"),
            "R&amp;D &amp; Química",
        )

    def test_pdf_text_escapes_markup_and_serializes_lists(self):
        self.assertEqual(
            _pdf_text([{"referencia": "<Manual>"}]),
            '[{"referencia": "&lt;Manual&gt;"}]',
        )


if __name__ == "__main__":
    unittest.main()
