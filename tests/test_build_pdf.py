"""
Test per app/build_PDF.py (revisione batch A). Coprono i tre bug critici
corretti in questo giro: prezzo NaN formattato come "nan" (punto 2), markup
ReportLab non sanificato che interrompe l'intera build (punto 5), e l'ultimo
gruppo di prodotti perso perche' mai "flushato" (punto 1).
"""
import io
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
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import KeepInFrame


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


class TestBuildProductCardLongName(unittest.TestCase):
    """Un nome prodotto lungo va a 3-4 righe (branch multi_rows_title): la cella
    del nome ha altezza fissa NAME_ROW_HEIGHT e occupa quasi tutta la larghezza
    della scheda, cosi' il testo si distribuisce a corpo pieno; il
    KeepInFrame(mode='shrink') e' la rete di sicurezza che scala il font solo per
    i nomi che sforerebbero comunque, senza toccare il bordo ne' cambiare il
    footprint (griglia 3x3 intatta)."""

    # nome della segnalazione: 3 righe, ora entrano a corpo pieno.
    LONG_NAME = "Cantina San Donaci - Assina Susumaniello Rosato"
    # nome patologico: sfora anche NAME_ROW_HEIGHT -> deve scattare lo shrink.
    OVERFLOW_NAME = ("Scheda video con un nome del prodotto esageratamente lungo "
                     "che non entra nemmeno in quattro righe a corpo pieno nella scheda")
    NAME_ROW_HEIGHT = 1.8 * cm

    def setUp(self):
        build_PDF._init_styles()

    @staticmethod
    def _find_keep_in_frame(flowable):
        """Cerca ricorsivamente il primo KeepInFrame nell'albero di Flowable/Table
        restituito da _build_product_card (Table -> _cellvalues, contenitori -> _content)."""
        if isinstance(flowable, KeepInFrame):
            return flowable
        rows = getattr(flowable, "_cellvalues", None) or getattr(flowable, "_content", None)
        if not rows:
            return None
        for entry in rows:
            cells = entry if isinstance(entry, (list, tuple)) else [entry]
            for cell in cells:
                found = TestBuildProductCardLongName._find_keep_in_frame(cell)
                if found is not None:
                    return found
        return None

    def _card_name_width(self):
        """Larghezza reale a disposizione del Paragraph del nome: SPAN su 2 colonne
        da USABLE_WIDTH/6 - TABLE_GAP (0.2cm), meno il padding minimo (3pt) della
        riga del nome. Replica l'aritmetica di _build_product_card()."""
        return 2 * (build_PDF.USABLE_WIDTH / 6 - 0.2 * cm) - 2 * 3

    def _make_card_name_flowable(self, name):
        row = {
            build_PDF.XLS_COMPANY: "Cantina San Donaci",
            build_PDF.XLS_ITEM: name,
            build_PDF.XLS_SIZE: "0,75 l",
            build_PDF.XLS_BADGE: "",
            build_PDF.XLS_CATEGORY: "Rosati",
        }
        card = build_PDF._build_product_card(row, "", "€ 5.50")
        return self._find_keep_in_frame(card)

    def test_item_name_is_wrapped_in_keepinframe_shrink(self):
        kif = self._make_card_name_flowable(self.LONG_NAME)
        self.assertIsNotNone(kif, "il nome prodotto deve essere avvolto in un KeepInFrame")
        self.assertEqual(kif.mode, "shrink")
        self.assertAlmostEqual(kif.maxHeight, self.NAME_ROW_HEIGHT)

    def test_long_name_stays_within_the_name_cell(self):
        kif = self._make_card_name_flowable(self.LONG_NAME)
        kif.canv = Canvas(io.BytesIO())  # wrap() ha bisogno di un canvas per le metriche
        _w, h = kif.wrap(self._card_name_width(), self.NAME_ROW_HEIGHT)
        # il nome della segnalazione (3 righe) non deve mai sforare la cella,
        # che ora e' abbastanza alta da contenerlo (di norma senza nemmeno scalare).
        self.assertLessEqual(h, self.NAME_ROW_HEIGHT + 1.0)

    def test_overflowing_name_is_shrunk_to_fit(self):
        kif = self._make_card_name_flowable(self.OVERFLOW_NAME)
        kif.canv = Canvas(io.BytesIO())
        _w, h = kif.wrap(self._card_name_width(), self.NAME_ROW_HEIGHT)
        # un nome che sfora anche NAME_ROW_HEIGHT deve essere scalato per rientrare.
        self.assertLessEqual(h, self.NAME_ROW_HEIGHT + 1.0)
        self.assertGreater(getattr(kif, "_scale", 1.0), 1.0)

    def test_short_name_is_not_scaled(self):
        kif = self._make_card_name_flowable("Rosato")
        kif.canv = Canvas(io.BytesIO())
        _w, h = kif.wrap(self._card_name_width(), self.NAME_ROW_HEIGHT)
        self.assertLessEqual(h, self.NAME_ROW_HEIGHT + 1.0)
        self.assertEqual(getattr(kif, "_scale", 1.0), 1.0)  # nessuno shrink: nessuna regressione


class TestBuildProductCardSizeRow(unittest.TestCase):
    """La riga formato/prezzo ha altezza fissa: un valore di 'Formato' lungo
    (che va a capo su 2 righe) non deve piu' far crescere la scheda oltre la
    cella della griglia 3x3 (bordo deformato / sovrapposizioni)."""

    def setUp(self):
        build_PDF._init_styles()

    def _card(self, size):
        row = {
            build_PDF.XLS_COMPANY: "Acme",
            build_PDF.XLS_ITEM: "Prodotto",
            build_PDF.XLS_SIZE: size,
            build_PDF.XLS_BADGE: "",
            build_PDF.XLS_CATEGORY: "Cat",
        }
        return build_PDF._build_product_card(row, "", "€ 2053.90")

    def _inner_table(self, card):
        # _build_product_card ritorna table_item_big: riga 1 = table_item annidato
        return card._cellvalues[1][0]

    def test_only_the_image_row_is_variable_height(self):
        inner = self._inner_table(self._card("Confezione da 10"))
        # indice 0 = immagine (contenuto a dimensione fissa); le righe azienda,
        # nome e formato/prezzo sono tutte ad altezza fissa -> footprint costante.
        self.assertIsNone(inner._rowHeights[0])
        self.assertTrue(all(h is not None for h in inner._rowHeights[1:]),
                        f"attese righe fisse, trovato {inner._rowHeights}")

    def test_size_and_price_are_wrapped_in_keepinframe(self):
        inner = self._inner_table(self._card("Confezione da 10"))
        size_cell, price_cell = inner._cellvalues[3]
        self.assertIsInstance(size_cell, KeepInFrame)
        self.assertIsInstance(price_cell, KeepInFrame)

    def test_long_and_short_size_give_the_same_row_heights(self):
        short = self._inner_table(self._card("1 pz"))
        long = self._inner_table(self._card("Confezione da 10"))
        self.assertEqual(short._rowHeights, long._rowHeights)


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

    def _write_excel(self, n_rows, item_name=None):
        rows = [
            {
                "Cat_Merc": "CatA",
                "Azienda": "Acme",
                "Nome_Art": item_name if item_name is not None else f"Widget{i}",
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

    def test_build_pdf_returns_path_and_invokes_progress_callback(self):
        self._write_excel(2)

        events = []
        result = build_PDF.build_pdf(progress_cb=events.append)

        self.assertTrue(str(result).endswith("_Catalog.pdf"))
        self.assertTrue(Path(result).is_file())
        # una notifica 'rows' per riga Excel + la 'done' finale a fraction 1.0
        row_events = [e for e in events if e.get("phase") == "rows"]
        self.assertEqual(len(row_events), 2)
        self.assertEqual(row_events[-1]["index"], 2)
        self.assertEqual(row_events[-1]["total"], 2)
        self.assertIn("product", row_events[0])
        self.assertTrue(any(e.get("phase") == "done"
                            and e.get("fraction") == 1.0 for e in events))
        # le fraction sono monotone non decrescenti e nel range [0, 1]
        fracs = [e["fraction"] for e in events if "fraction" in e]
        self.assertEqual(fracs, sorted(fracs))
        self.assertGreaterEqual(min(fracs), 0.0)
        self.assertLessEqual(max(fracs), 1.0)

    def test_four_rows_flushes_full_group_and_trailing_row(self):
        self._write_excel(4)  # 1 gruppo completo da 3 + 1 riga finale pendente

        build_PDF.build_pdf()

        pdfs = list(Path(self._tmp_dir.name).glob("*.pdf"))
        self.assertEqual(len(pdfs), 1)
        self.assertGreater(pdfs[0].stat().st_size, 0)
        self.assertEqual(build_PDF.raw_1x3_counter, 0)
        self.assertEqual(build_PDF.raw_1x3_items, ["", "", ""])

    def test_long_product_name_produces_non_empty_pdf(self):
        # Un nome che va a 3 righe non deve rompere la build ne' lasciare stato
        # a meta': il KeepInFrame(shrink) in _build_product_card lo fa rientrare
        # nella cella a altezza fissa senza toccare il footprint della scheda.
        self._write_excel(1, item_name="Cantina San Donaci - Assina Susumaniello Rosato")

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
