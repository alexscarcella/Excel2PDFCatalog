"""
Test per app/build_PDF.py (revisione batch A). Coprono i tre bug critici
corretti in questo giro: prezzo NaN formattato come "nan" (punto 2), markup
ReportLab non sanificato che interrompe l'intera build (punto 5), e l'ultimo
gruppo di prodotti perso perche' mai "flushato" (punto 1).
"""
import math
import os
import tempfile
import unittest
from pathlib import Path

import pandas as pd

import app.config_utils as config_utils
import app.excel_config as excel_config
import app.build_PDF as build_PDF
from reportlab.lib.units import cm


class TestFormatPrice(unittest.TestCase):
    def test_nan_price_returns_empty_string(self):
        row = {build_PDF.XLS_PRICE: float("nan"), build_PDF.XLS_ITEM: "Widget"}
        self.assertEqual(build_PDF._format_price(row), "")

    def test_valid_price_is_formatted(self):
        row = {build_PDF.XLS_PRICE: 9.5, build_PDF.XLS_ITEM: "Widget"}
        self.assertEqual(build_PDF._format_price(row), "€ 9.50")


class TestBuildProductCardEscaping(unittest.TestCase):
    def setUp(self):
        build_PDF._init_styles()

    def test_ampersand_and_angle_brackets_do_not_raise(self):
        row = {
            build_PDF.XLS_COMPANY: "A & B <Premium>",
            build_PDF.XLS_ITEM: "Widget & Co <Deluxe>",
            build_PDF.XLS_SIZE: "M",
            build_PDF.XLS_BADGE: "New & Improved",
            build_PDF.XLS_CATEGORY: "CatA",
        }
        # Prima della fix (batch A, punto 5) questi caratteri rompevano il
        # parser XML-like di ReportLab e interrompevano l'intera build.
        build_PDF._build_product_card(row, "", "€ 9.50")


class _BuildPdfTestCase(unittest.TestCase):
    """Isola i path/scalari di config_utils in cartelle temporanee, cosi' i
    test non toccano i file reali del progetto (stesso approccio di
    tests/test_config_utils.py's _ConfigFileTestCase)."""

    COLUMN_MAP = {
        "Cat_Merc": build_PDF.XLS_CATEGORY,
        "Azienda": build_PDF.XLS_COMPANY,
        "Nome_Art": build_PDF.XLS_ITEM,
        "Formato": build_PDF.XLS_SIZE,
        "prezzo_vendita_ingrosso": build_PDF.XLS_PRICE,
        "Descrizione_prodotto": build_PDF.XLS_COLUMN_DESCRIPTION,
        "Codice_Articolo": build_PDF.XLS_COLUMN_IMG,
        "Badge": build_PDF.XLS_BADGE,
    }

    def setUp(self):
        self._original_scalars = (
            config_utils.excel_file, config_utils.txt_intro_file,
            config_utils.title, config_utils.subtitle, config_utils.footer,
        )
        self._original_paths = dict(config_utils.path_dictionary)

        self._tmp_dir = tempfile.TemporaryDirectory()
        tmp = Path(self._tmp_dir.name)
        (tmp / "tmp").mkdir()

        config_utils.title = "T"
        config_utils.subtitle = "S"
        config_utils.footer = "F"
        config_utils.txt_intro_file = self._original_scalars[1]  # file di esempio, gia' esistente
        config_utils.path_dictionary["OUTPUT_PDF_FOLDER_PATH"] = tmp
        config_utils.path_dictionary["TMP_SYSTEM_FOLDER_PATH"] = tmp / "tmp"
        # immagini/prodotto: uso le cartelle reali del progetto (contengono default.png)
        config_utils.path_dictionary["PRODUCTS_IMAGES_FOLDER_PATH"] = self._original_paths["PRODUCTS_IMAGES_FOLDER_PATH"]
        config_utils.path_dictionary["GENERAL_IMAGES_FOLDER_PATH"] = self._original_paths["GENERAL_IMAGES_FOLDER_PATH"]

    def tearDown(self):
        (config_utils.excel_file, config_utils.txt_intro_file,
         config_utils.title, config_utils.subtitle, config_utils.footer) = self._original_scalars
        config_utils.path_dictionary.clear()
        config_utils.path_dictionary.update(self._original_paths)
        self._tmp_dir.cleanup()

    def _write_excel(self, n_rows):
        rows = [
            {
                "Cat_Merc": "CatA",
                "Azienda": "Acme",
                "Nome_Art": f"Widget{i}",
                "Formato": "M",
                "prezzo_vendita_ingrosso": 9.99,
                "Descrizione_prodotto": "desc",
                "Codice_Articolo": "nonexistent",
                "Badge": "",
            }
            for i in range(n_rows)
        ]
        excel_path = Path(self._tmp_dir.name) / "products.xlsx"
        pd.DataFrame(rows, columns=list(self.COLUMN_MAP.keys())).to_excel(excel_path, index=False)
        config_utils.excel_file = str(excel_path)
        return excel_path


class TestBuildPdfFlushesTrailingRow(_BuildPdfTestCase):
    def test_single_row_catalog_produces_non_empty_pdf(self):
        # Prima della fix (batch A, punto 1) un catalogo di 1 riga produceva un
        # PDF con zero prodotti: raw_1x3_counter restava a 1 e la riga pendente
        # non veniva mai pubblicata in 'story' prima di doc.build().
        self._write_excel(1)

        build_PDF.build_pdf()

        pdfs = list(Path(self._tmp_dir.name).glob("*.pdf"))
        self.assertEqual(len(pdfs), 1)
        self.assertGreater(pdfs[0].stat().st_size, 0)
        # Se la riga pendente e' stata effettivamente flushata, il contatore e
        # il buffer tornano allo stato "vuoto" invece di restare a meta'.
        self.assertEqual(build_PDF.raw_1x3_counter, 0)
        self.assertEqual(build_PDF.raw_1x3_items, ["", "", ""])

    def test_four_rows_flushes_full_group_and_trailing_row(self):
        self._write_excel(4)  # 1 gruppo completo da 3 + 1 riga finale pendente

        build_PDF.build_pdf()

        pdfs = list(Path(self._tmp_dir.name).glob("*.pdf"))
        self.assertEqual(len(pdfs), 1)
        self.assertGreater(pdfs[0].stat().st_size, 0)
        self.assertEqual(build_PDF.raw_1x3_counter, 0)
        self.assertEqual(build_PDF.raw_1x3_items, ["", "", ""])


class TestBuildPdfLayoutParamsApplyAtBuildTime(_BuildPdfTestCase):
    """MARGIN e CARD_BORDER_WIDTH di Excel2PDFCatalog.config sono riletti da
    build_pdf() (via _init_layout/_build_product_card), non solo all'import:
    una modifica ha effetto senza riavviare l'app."""

    def setUp(self):
        super().setUp()
        self._orig_layout = dict(excel_config.layout)

    def tearDown(self):
        excel_config.layout.clear()
        excel_config.layout.update(self._orig_layout)
        build_PDF._init_layout()   # ripristina la geometria di modulo
        super().tearDown()

    def test_margin_change_is_picked_up_by_build_pdf(self):
        excel_config.layout["MARGIN"] = 3.0
        excel_config.layout["CARD_BORDER_WIDTH"] = 6.0
        self._write_excel(2)

        build_PDF.build_pdf()

        self.assertAlmostEqual(build_PDF.PAGE_MARGIN, 3.0 * cm)
        pdfs = list(Path(self._tmp_dir.name).glob("*.pdf"))
        self.assertEqual(len(pdfs), 1)
        self.assertGreater(pdfs[0].stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
