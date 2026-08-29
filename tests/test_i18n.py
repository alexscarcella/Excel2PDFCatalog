"""Test per app/i18n.py: fallback delle traduzioni, hook di cambio lingua,
parita' fra le tabelle IT/EN e copertura dei colori nei gruppi della UI."""
import unittest

import app.i18n as i18n


class _I18nTestCase(unittest.TestCase):
    def setUp(self):
        self._lang = i18n.get_language()

    def tearDown(self):
        i18n.clear_hooks()
        i18n.set_language(self._lang)


class TestTranslate(_I18nTestCase):
    def test_known_key_differs_by_language(self):
        i18n.set_language("it")
        it_value = i18n.t("tab.sources")
        i18n.set_language("en")
        en_value = i18n.t("tab.sources")
        self.assertTrue(it_value and en_value)
        self.assertNotEqual(it_value, en_value)

    def test_unknown_key_falls_back_to_key_itself(self):
        self.assertEqual(i18n.t("not.a.real.key"), "not.a.real.key")

    def test_format_placeholders_are_applied(self):
        i18n.set_language("en")
        self.assertEqual(
            i18n.t("problem.path_missing", name="Output"),
            "folder not found (Output)",
        )

    def test_it_and_en_tables_have_the_same_keys(self):
        self.assertEqual(set(i18n.TRANSLATIONS["it"]), set(i18n.TRANSLATIONS["en"]))


class TestLanguageHooks(_I18nTestCase):
    def test_hooks_fire_on_every_language_change(self):
        seen = []
        i18n.on_language_change(lambda: seen.append(i18n.get_language()))
        i18n.set_language("en")
        i18n.set_language("it")
        self.assertEqual(seen, ["en", "it"])

    def test_clear_hooks_removes_all(self):
        seen = []
        i18n.on_language_change(lambda: seen.append(1))
        i18n.clear_hooks()
        i18n.set_language("en")
        self.assertEqual(seen, [])

    def test_unknown_language_is_coerced_to_a_supported_one(self):
        i18n.set_language("de")
        self.assertIn(i18n.get_language(), i18n.LANGUAGES)


class TestFieldHelpers(_I18nTestCase):
    def test_field_label_uses_translation_when_present(self):
        i18n.set_language("en")
        self.assertEqual(i18n.field_label("HIDE_PRICES"), "Hide prices")

    def test_field_label_falls_back_to_humanised_key(self):
        self.assertEqual(i18n.field_label("SOME_BRAND_NEW_KEY"), "Some brand new key")

    def test_field_hint_is_empty_when_undefined(self):
        self.assertEqual(i18n.field_hint("SOME_BRAND_NEW_KEY"), "")

    def test_detect_default_returns_a_supported_language(self):
        self.assertIn(i18n.detect_default(), i18n.LANGUAGES)


class TestUiMetadata(_I18nTestCase):
    def test_color_groups_cover_every_default_colour(self):
        import app.config_utils as config_utils

        grouped = {key for _gid, keys in i18n.COLOR_GROUPS for key in keys}
        self.assertTrue(set(config_utils.COLOR_DEFAULTS).issubset(grouped))

    def test_every_grouped_colour_key_exists_in_defaults(self):
        import app.config_utils as config_utils

        grouped = {key for _gid, keys in i18n.COLOR_GROUPS for key in keys}
        self.assertTrue(grouped.issubset(set(config_utils.COLOR_DEFAULTS)))


if __name__ == "__main__":
    unittest.main()
