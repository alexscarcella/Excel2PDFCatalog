"""
Test minimi per app/images_utils.py (punto 9 della revisione: nessun test
presente nel progetto). Copre load_image_path(), la funzione usata da
build_PDF.py per cercare l'immagine di un prodotto tra le estensioni supportate.
"""
import tempfile
import unittest
from pathlib import Path

from app.images_utils import load_image_path


class TestLoadImagePath(unittest.TestCase):
    def setUp(self):
        self._tmp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self._tmp_dir.cleanup()

    def _touch(self, name):
        path = Path(self._tmp_dir.name) / name
        path.write_bytes(b"")
        return path

    def test_prefers_png_when_multiple_extensions_exist(self):
        self._touch("SKU001.jpg")
        self._touch("SKU001.png")
        result = load_image_path(Path(self._tmp_dir.name) / "SKU001")
        self.assertEqual(result.suffix, ".png")

    def test_falls_back_to_jpg_if_no_png(self):
        self._touch("SKU002.jpg")
        result = load_image_path(Path(self._tmp_dir.name) / "SKU002")
        self.assertEqual(result.suffix, ".jpg")

    def test_falls_back_to_jpeg_if_no_png_or_jpg(self):
        self._touch("SKU003.jpeg")
        result = load_image_path(Path(self._tmp_dir.name) / "SKU003")
        self.assertEqual(result.suffix, ".jpeg")

    def test_returns_none_when_no_file_matches(self):
        result = load_image_path(Path(self._tmp_dir.name) / "SKU999")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
