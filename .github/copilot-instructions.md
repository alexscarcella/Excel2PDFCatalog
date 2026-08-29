<!-- Copilot / AI agent instructions for Excel2PDFCatalog -->
# Excel2PDFCatalog — AI Agent Instructions

These concise notes help an AI coding agent be productive in this repository. Focus on the files and patterns below when changing behavior, debugging, or adding features. `CLAUDE.md` at the repo root has the fuller architecture reference.

- **Purpose**: converts a product-list Excel file into a PDF catalog using a tabbed Tkinter/`ttk` desktop UI (`Excel2PDFCatalog.py` → `app/ui_interface.py`) and a ReportLab PDF builder (`app/build_PDF.py`). The UI is bilingual (Italian/English, switchable at runtime) and stdlib-only — no UI dependency beyond `tkinter`.

- **Run / debug (Windows PowerShell)**:
  - Create venv and install deps:
    ```powershell
    python -m venv .venv
    .\.venv\Scripts\activate
    pip install -r app/requirements.txt
    ```
  - Run app: `python Excel2PDFCatalog.py`
  - Run tests (stdlib `unittest`, no extra dep): `python -m unittest discover -s tests -v`
  - Logs: `./logs/app.log` from source (rotating handler in `app/logger.py`); a per-user data dir when frozen (`~/Library/Application Support/Excel2PDFCatalog`, `%LOCALAPPDATA%\Excel2PDFCatalog`).

- **Key files / responsibilities**:
  - `Excel2PDFCatalog.py` — entrypoint. Installs a `sys.excepthook` writing `crash.log` before any other import, then `config_utils.load_config()` + `ui_interface.build_UI_and_GO()`.
  - `app/ui_interface.py` — the whole UI in `build_UI_and_GO()`: a `ttk.Notebook` (Sources / Catalog / Options / Colors / Excel columns tabs) + a persistent status/action bar + a menu. Still imperative, nested-closure style; callbacks write straight into `app/config_utils` module state (and `app/excel_config` for the Options "Layout" section + "Excel columns" tab). `_init_style()` forces the `clam` theme + platform font; `_set_window_icon()` loads `assets/icon/`.
  - `app/config_utils.py` — runtime state + `load_config()` / `save_config()` (JSON `config.json`). In-memory: `language`, `excel_file`, `txt_intro_file`, `title`/`subtitle`/`footer`, and dicts `colors_dictionary` / `path_dictionary` / `flags_dictionary`. `COLOR_DEFAULTS` / `FLAG_DEFAULTS` snapshot defaults for the UI reset buttons.
  - `app/i18n.py` — bilingual layer (no Tk, no deps): `t(key, **kw)` (fallback EN → key), `set_language()` + `on_language_change()` hooks, `field_label()` / `field_hint()` (translated dict-key labels, fallback `.replace('_',' ').capitalize()`), and `TRANSLATIONS` / `COLOR_GROUPS` / `FLAG_ORDER`. Only display strings are translated; dict keys stay English.
  - `app/excel_config.py` — Tk-free layer over `Excel2PDFCatalog.config` (INI): dicts `columns` / `layout` / `system`, `load()` / `save()` (per-key default fallback; writable copy via `writable_path()`), typed accessors, plus `COLUMN_KEYS` / `COMMON_LOCALES` for the "Excel columns" tab. Auto-`load()`s at import; `config_utils.save_config()` also calls `save()`.
  - `app/build_PDF.py` — PDF assembly with ReportLab. Pulls the column mapping, page geometry and locale from `app/excel_config.py` via `_init_excel_mapping()` / `_init_layout()` / `_init_locale()` — run at import **and** at the top of `build_pdf()` (UI edits apply without restart). Registers the `fonts/` TTF. Consumes `config_utils` state at build time.
  - `app/paths_utils.py` — `resource_path()` (read-only bundled assets) / `writable_path()` (runtime files). Route every filesystem path through these so source and PyInstaller-frozen builds both work.
  - `app/images_utils.py` — `load_image_path()` (tries `.png`/`.jpg`/`.jpeg`) and `generate_image()` placeholder blobs.
  - `Excel2PDFCatalog.config` — INI: Excel column names (`XLS_COLUMN_*` + `XLS_BADGE`) + `MARGIN` / `CARD_BORDER_WIDTH` / `LOCALE`. Owned by `app/excel_config.py`; UI-editable.
  - `fonts/` — custom TTF; `assets/icon/` — app/window icon (`make_icon.py` regenerates it).

- **Important repository conventions & patterns**:
  - `config_utils` is the single source of runtime UI state: the UI writes directly to its module-level variables/dicts, which `build_PDF` reads at build time. Prefer editing state there over threading params.
  - `path_dictionary` values are `pathlib.Path`; stringified in `config.json`, re-`Path()`-ed on load. Missing saved paths fall back to defaults instead of failing.
  - `colors_dictionary` values are hex strings referenced directly by `build_PDF.py` `ParagraphStyle`s and canvas fills.
  - The UI generates its Colors/Options/Folders controls by **iterating those dicts**, so a new key needs no widget code — it renders via `i18n.field_label()`. But: add its default in `config_utils.py`, a `field.<KEY>` (+ `hint.<KEY>` for a flag) string to **both** `it` and `en` in `i18n.TRANSLATIONS` (a test asserts key parity), and — for a color — a group in `i18n.COLOR_GROUPS`.
  - Excel-to-field mapping is `Excel2PDFCatalog.config`, owned by `app/excel_config.py`; adding/renaming a key means editing `COLUMN_KEYS` / `LAYOUT_DEFAULTS` / `SYSTEM_DEFAULTS` there (+ `build_PDF._init_excel_mapping()` / `_init_layout()` if it feeds a module constant) and `field.<KEY>` / `hint.<KEY>` in both `it` and `en`.
  - Logging: shared `AppLogger` (`app/logger.py`). Use `logger.info/warning/error`.

- **PDF layout notes**:
  - `build_pdf()` builds a `story` list of Flowables across four PageTemplates: `Cover`, `Body`, `Category`, `Matrix_3x3` (rebuilt each call by `_init_layout()` from `excel_config.margin_cm()`). Pagination is driven by pushing `NextPageTemplate` + `PageBreak`; products flow through `flush_1x3_row()` into a 3-per-row grid. Per-row work is split into `_clean_row_fields` / `_format_price` / `_insert_category_page` / `_insert_company_page` / `_load_product_image` / `_build_product_card` (card border thickness from `excel_config.card_border_width()`).
  - Fonts: the referenced TTF must exist in `fonts/` and match the `registerFont` call.

- **Configuration persistence**:
  - `config.json` (repo root when run from source, per-user data dir when frozen) — generated by `config_utils.save_config()`, read by `load_config()`. Stores `language`, `excel_file`, `txt_intro_file`, `title`/`subtitle`/`footer`, every color, every path, every flag. The UI saves it after a build and on language change.
  - `Excel2PDFCatalog.config` (INI) is a *different* file — Excel column mapping + `MARGIN` / `CARD_BORDER_WIDTH` / `LOCALE`, managed by `app/excel_config.py` (writable copy under the per-user data dir when frozen). Do not conflate with `config.json`.

- **Cross-cutting checks when editing**:
  - New/renamed `path_dictionary` key → update `config_utils.py` default and every path composition in `build_PDF.py`; the UI picks it up automatically.
  - New/renamed color or flag key → also add the `i18n` strings (both languages) and, for colors, `i18n.COLOR_GROUPS`.
  - New/renamed `Excel2PDFCatalog.config` key → update `COLUMN_KEYS` / `LAYOUT_DEFAULTS` / `SYSTEM_DEFAULTS` in `app/excel_config.py`, wire it into `build_PDF._init_excel_mapping()` / `_init_layout()` if it feeds a module global (so it re-reads at build time, not only at import), add `field.<KEY>` / `hint.<KEY>` in both `it` and `en`, and extend `tests/test_excel_config.py`.
  - Never hardcode paths against `cwd` / `__file__` — use `paths_utils.resource_path()` / `writable_path()`.
  - New dependency → update `app/requirements.txt`, the `--collect-all` / `--hidden-import` lines in `.github/workflows/build.yml`, and mention it in the README. Keep the UI stdlib-only.
  - Renaming/moving icon files → keep `assets/icon/`, the `--icon` + `--add-data` lines in `build.yml`, and `_set_window_icon()` in sync.

- **Developer workflow tips**:
  - `tests/` is a stdlib `unittest` suite (`config_utils`, `excel_config`, `i18n`, `build_PDF`, `images_utils`) — run it before and after changes. There is no lint tooling and no CI on push; the only workflow is a manual `workflow_dispatch` PyInstaller packaging job.
  - The Tkinter rendering path has no automated coverage — validate UI changes by running the GUI, switching language, and generating a PDF from `example_excel/Product list example.xlsx`, then checking `logs/app.log`.
