"""Test per app/excel_config.py: fallback sui default, round-trip save/load,
accessor tipizzati. Isola i path del file INI in una cartella temporanea (stesso
approccio di tests/test_config_utils.py._ConfigFileTestCase)."""
import configparser
import os
import tempfile
import unittest

import app.excel_config as excel_config


class _ExcelConfigTestCase(unittest.TestCase):
    def setUp(self):
        self._orig_config_path = excel_config.CONFIG_PATH
        self._orig_bundled_path = excel_config.BUNDLED_PATH
        self._orig_columns = dict(excel_config.columns)
        self._orig_layout = dict(excel_config.layout)
        self._orig_system = dict(excel_config.system)
        self._tmp = tempfile.TemporaryDirectory()
        excel_config.CONFIG_PATH = os.path.join(self._tmp.name, "Excel2PDFCatalog.config")
        # "bundled" inesistente: cosi' i test controllano il ramo "solo default"
        # senza che _seed_writable_copy() copi il file reale del repo.
        excel_config.BUNDLED_PATH = os.path.join(self._tmp.name, "bundled-missing.config")

    def tearDown(self):
        excel_config.CONFIG_PATH = self._orig_config_path
        excel_config.BUNDLED_PATH = self._orig_bundled_path
        excel_config.columns.clear()
        excel_config.columns.update(self._orig_columns)
        excel_config.layout.clear()
        excel_config.layout.update(self._orig_layout)
        excel_config.system.clear()
        excel_config.system.update(self._orig_system)
        self._tmp.cleanup()

    def _write(self, text):
        with open(excel_config.CONFIG_PATH, "w", encoding="utf-8") as f:
            f.write(text)


class TestLoad(_ExcelConfigTestCase):
    def test_missing_file_falls_back_to_defaults(self):
        excel_config.columns["CATEGORY"] = "DIRTY"
        excel_config.layout["MARGIN"] = 99.0
        excel_config.load()
        self.assertEqual(excel_config.columns["CATEGORY"], "Cat_Merc")
        self.assertEqual(excel_config.margin_cm(), 2.0)
        self.assertEqual(excel_config.card_border_width(), 2.0)
        self.assertEqual(excel_config.locale_name(), "it_IT.UTF-8")

    def test_partial_excel_section_keeps_defaults_for_missing_keys(self):
        self._write("[Excel]\nXLS_COLUMN_CATEGORY = MyCat\n")
        excel_config.load()
        self.assertEqual(excel_config.columns["CATEGORY"], "MyCat")
        self.assertEqual(excel_config.columns["COMPANY"], "Azienda")  # default

    def test_invalid_numbers_fall_back_to_defaults(self):
        self._write("[Layout]\nMARGIN = abc\nCARD_BORDER_WIDTH =\n")
        excel_config.load()
        self.assertEqual(excel_config.margin_cm(), 2.0)
        self.assertEqual(excel_config.card_border_width(), 2.0)

    def test_valid_values_are_read(self):
        self._write(
            "[Excel]\nXLS_COLUMN_ITEM = Name\n"
            "[Layout]\nMARGIN = 3\nCARD_BORDER_WIDTH = 1.5\n"
            "[System]\nLOCALE = en_US.UTF-8\n"
        )
        excel_config.load()
        self.assertEqual(excel_config.column("ITEM"), "Name")
        self.assertEqual(excel_config.margin_cm(), 3.0)
        self.assertEqual(excel_config.card_border_width(), 1.5)
        self.assertEqual(excel_config.locale_name(), "en_US.UTF-8")


class TestSave(_ExcelConfigTestCase):
    def test_round_trip(self):
        excel_config.load()
        excel_config.columns["CATEGORY"] = "Reparto"
        excel_config.layout["MARGIN"] = 2.5
        excel_config.layout["CARD_BORDER_WIDTH"] = 4.0
        excel_config.system["LOCALE"] = "de_DE.UTF-8"
        self.assertTrue(excel_config.save())

        excel_config.columns["CATEGORY"] = "x"          # sporca lo stato in memoria
        excel_config.layout["MARGIN"] = 99.0
        excel_config.load()
        self.assertEqual(excel_config.columns["CATEGORY"], "Reparto")
        self.assertEqual(excel_config.margin_cm(), 2.5)
        self.assertEqual(excel_config.card_border_width(), 4.0)
        self.assertEqual(excel_config.locale_name(), "de_DE.UTF-8")

    def test_save_writes_all_three_sections(self):
        excel_config.load()
        self.assertTrue(excel_config.save())
        parser = configparser.ConfigParser()
        parser.read(excel_config.CONFIG_PATH, encoding="utf-8")
        self.assertEqual(set(parser.sections()), {"Excel", "Layout", "System"})
        self.assertIn("CARD_BORDER_WIDTH", parser["Layout"])
        self.assertIn("XLS_BADGE", parser["Excel"])

    def test_save_returns_false_on_oserror(self):
        excel_config.CONFIG_PATH = self._tmp.name        # una directory -> OSError
        self.assertFalse(excel_config.save())


class TestAccessors(_ExcelConfigTestCase):
    def test_required_column_names_excludes_description(self):
        excel_config.load()
        names = excel_config.required_column_names()
        self.assertIn(excel_config.column("CATEGORY"), names)
        self.assertNotIn(excel_config.column("DESCRIPTION"), names)

    def test_accessor_types(self):
        excel_config.load()
        self.assertIsInstance(excel_config.margin_cm(), float)
        self.assertIsInstance(excel_config.card_border_width(), float)
        self.assertIsInstance(excel_config.all_columns(), dict)
        self.assertIsInstance(excel_config.locale_name(), str)

    def test_common_locales_is_a_non_empty_string_list_with_the_default(self):
        self.assertTrue(excel_config.COMMON_LOCALES)
        self.assertTrue(all(isinstance(v, str) and v for v in excel_config.COMMON_LOCALES))
        self.assertIn(excel_config.SYSTEM_DEFAULTS["LOCALE"], excel_config.COMMON_LOCALES)


if __name__ == "__main__":
    unittest.main()
