"""
Test minimi per app/config_utils.py (punto 9 della revisione: il progetto non
aveva alcuna suite di test). Coprono in particolare il comportamento corretto
introdotto per risolvere il punto critico #1: load_config()/save_config() non
devono piu' terminare il processo (sys.exit) su un config.json incompleto o
non scrivibile, ma ricadere sui valori di default.
"""
import json
import os
import tempfile
import unittest

import app.config_utils as config_utils


class TestParseBool(unittest.TestCase):
    def test_native_bool_is_returned_as_is(self):
        self.assertTrue(config_utils._parse_bool(True))
        self.assertFalse(config_utils._parse_bool(False))

    def test_string_variants_are_parsed_case_insensitively(self):
        self.assertTrue(config_utils._parse_bool("True"))
        self.assertTrue(config_utils._parse_bool("true"))
        self.assertTrue(config_utils._parse_bool("  TRUE  "))
        self.assertFalse(config_utils._parse_bool("False"))
        self.assertFalse(config_utils._parse_bool("false"))
        self.assertFalse(config_utils._parse_bool("qualcosa d'altro"))


class _ConfigFileTestCase(unittest.TestCase):
    """Isola CONFIG_FILE e i dizionari globali di config_utils in una cartella
    temporanea, cosi' i test non toccano il config.json reale del progetto."""

    def setUp(self):
        self._original_config_file = config_utils.CONFIG_FILE
        self._original_flags = dict(config_utils.flags_dictionary)
        self._original_colors = dict(config_utils.colors_dictionary)
        self._original_paths = dict(config_utils.path_dictionary)
        self._original_scalars = (
            config_utils.excel_file, config_utils.txt_intro_file,
            config_utils.title, config_utils.subtitle, config_utils.footer,
        )
        self._tmp_dir = tempfile.TemporaryDirectory()
        config_utils.CONFIG_FILE = os.path.join(self._tmp_dir.name, "config.json")

    def tearDown(self):
        config_utils.CONFIG_FILE = self._original_config_file
        config_utils.flags_dictionary.clear()
        config_utils.flags_dictionary.update(self._original_flags)
        config_utils.colors_dictionary.clear()
        config_utils.colors_dictionary.update(self._original_colors)
        config_utils.path_dictionary.clear()
        config_utils.path_dictionary.update(self._original_paths)
        (config_utils.excel_file, config_utils.txt_intro_file,
         config_utils.title, config_utils.subtitle, config_utils.footer) = self._original_scalars
        self._tmp_dir.cleanup()


class TestLoadConfig(_ConfigFileTestCase):
    def test_missing_keys_fall_back_to_defaults_without_crashing(self):
        default_hide_prices = self._original_flags["HIDE_PRICES"]
        default_cover_color = self._original_colors["COVER_TITLE_COLOR"]
        # config.json volutamente incompleto: manca un flag e un colore, come
        # accadrebbe dopo un aggiornamento dell'app che ne introduce di nuovi.
        partial_config = {
            "excel_file": "x.xlsx",
            "txt_intro_file": "intro.txt",
            "title": "T", "subtitle": "S", "footer": "F",
        }
        with open(config_utils.CONFIG_FILE, "w") as f:
            json.dump(partial_config, f)

        config_utils.load_config()  # non deve sollevare ne' terminare il processo

        self.assertEqual(config_utils.flags_dictionary["HIDE_PRICES"], default_hide_prices)
        self.assertEqual(config_utils.colors_dictionary["COVER_TITLE_COLOR"], default_cover_color)
        self.assertEqual(config_utils.title, "T")

    def test_corrupted_json_keeps_all_defaults(self):
        with open(config_utils.CONFIG_FILE, "w") as f:
            f.write("{questo non e' json valido")

        config_utils.load_config()  # non deve sollevare ne' terminare il processo

        self.assertEqual(config_utils.flags_dictionary, self._original_flags)
        self.assertEqual(config_utils.colors_dictionary, self._original_colors)

    def test_missing_file_creates_one_with_defaults(self):
        self.assertFalse(os.path.exists(config_utils.CONFIG_FILE))
        config_utils.load_config()
        self.assertTrue(os.path.exists(config_utils.CONFIG_FILE))


class TestSaveConfig(_ConfigFileTestCase):
    def test_save_returns_true_and_writes_file_on_success(self):
        self.assertTrue(config_utils.save_config())
        self.assertTrue(os.path.exists(config_utils.CONFIG_FILE))

    def test_save_returns_false_instead_of_exiting_on_io_error(self):
        # Puntare CONFIG_FILE a una directory forza un errore di scrittura reale
        # (OSError), lo scenario che prima causava sys.exit(1) nell'intera app.
        config_utils.CONFIG_FILE = self._tmp_dir.name
        self.assertFalse(config_utils.save_config())


if __name__ == "__main__":
    unittest.main()
