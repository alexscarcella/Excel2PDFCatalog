# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Excel2PDFCatalog is a Windows/macOS desktop tool (Tkinter UI + ReportLab PDF engine) that converts a product-list Excel file into a printable PDF catalog. It ships as a source app and as PyInstaller-built standalone executables (see `.github/workflows/build.yml`).

## Commands

```powershell
# setup
python -m venv .venv
.venv\Scripts\activate
pip install -r app/requirements.txt

# run
python Excel2PDFCatalog.py

# tests (stdlib unittest, no extra dependency)
python -m unittest discover -s tests -v
# single test module
python -m unittest tests.test_config_utils -v
```

`tests/` has a minimal `unittest` suite for `config_utils.py` (load/save fallback behavior) and `images_utils.py` (`load_image_path`) — no framework beyond stdlib is required. There is no lint or build tooling configured for local development, and no CI running on push — the only workflow is a manual `workflow_dispatch` PyInstaller packaging job for releases. There's no coverage for the ReportLab/Tkinter side (`build_PDF.py`, `ui_interface.py`); validate changes there by running the GUI and generating a PDF against `example_excel/Product list example.xlsx`, checking `logs/app.log` for warnings/errors.

## Architecture

**Three-module core, coupled through shared mutable state in `app/config_utils.py`:**

- `Excel2PDFCatalog.py` — entrypoint: calls `config_utils.load_config()` then `ui_interface.build_UI_and_GO()`.
- `app/config_utils.py` — the single source of runtime state. Module-level globals (`excel_file`, `txt_intro_file`, `title`, `subtitle`, `footer`, and the dicts `colors_dictionary`, `path_dictionary`, `flags_dictionary`) are written directly by the UI and read directly by the PDF builder — there's no explicit object passed between them. `load_config()`/`save_config()` (de)serialize these globals to `config.json` in the working directory. `path_dictionary` values are `pathlib.Path` in memory, stringified on save.
- `app/ui_interface.py` — `build_UI_and_GO()` builds the entire Tkinter window imperatively in one function (file/folder pickers, text fields with `trace_add` bindings, per-flag checkboxes generated from `flags_dictionary`, per-color pickers generated from `colors_dictionary`) and wires the "Save and build PDF" button to `build_PDF.build_pdf()`. `check_parameters()` verifies the configured Excel file and all `path_dictionary` entries exist before a build is allowed.
- `app/build_PDF.py` — PDF assembly with ReportLab. At **import time** it reads `Excel2PDFCatalog.config` via `configparser` for the Excel column-name mapping (`XLS_COLUMN_*`) and layout constants (margin, locale), and registers the custom TTF font from `fonts/`. `build_pdf()` reads the Excel file with pandas, iterates rows, and appends ReportLab Flowables to a module-level `story` list.

**Two distinct config files — do not conflate them:**
- `Excel2PDFCatalog.config` (INI, `configparser`) — maps Excel column headers to internal field names (`XLS_COLUMN_CATEGORY`, `XLS_COLUMN_ITEM`, `XLS_COLUMN_PRICE`, etc.) plus `MARGIN` and `LOCALE`. Read once at import of `build_PDF.py`.
- `config.json` (JSON, generated) — UI/runtime state: title/subtitle/footer, colors, folder paths, boolean flags. Written by `config_utils.save_config()`, read by `config_utils.load_config()`.

**PDF layout model (ReportLab):** the document uses four named `PageTemplate`s registered on one `BaseDocTemplate` — `Cover`, `Body`, `Category`, `Matrix_3x3` — each with its own `onPage` canvas callback (`cover_on_page`, `body_on_page`, `category_on_page`, `matrix_3x3_on_page`) that paints background color and header/footer text from `colors_dictionary`. Pagination is driven by pushing `NextPageTemplate(...)` + `PageBreak()` onto `story` as the Excel rows are scanned. Products are grouped into a 3-per-row grid: `raw_1x3_items`/`raw_1x3_counter` accumulate up to 3 product tables, flushed via `flush_1x3_row()` into a `KeepTogether` table row — a new `Category` title page is emitted whenever the category column value changes, and (if `BREAK_PAGE_COMPANY` is set) a company divider page whenever the company column value changes.

**Product images:** looked up in `PRODUCTS_IMAGES_FOLDER_PATH` via `images_utils.load_image_path()`, which tries `.png`/`.jpg`/`.jpeg` in that order against the filename from the Excel image column. If missing, falls back to a procedurally generated placeholder blob image (`images_utils.generate_image()`, written under `tmp/`) when `GENERATE_RANDOM_PRODUCTS_IMAGE` is set, otherwise to `PRODUCTS_IMAGES_FOLDER_PATH/default.png`.

**Logging:** shared `AppLogger` in `app/logger.py`, rotating file handler at `logs/app.log` (1MB × 5 backups) plus console. Use `logger.info/warning/error` — this remains the primary debugging surface for the ReportLab/Tkinter code paths that the `tests/` suite doesn't cover.

**Path resolution (`app/paths_utils.py`):** every filesystem path in the app goes through this module instead of being built directly, because the same code must work running from source and as a frozen PyInstaller bundle (onedir on macOS). `resource_path(rel_path)` resolves *read-only bundled* assets (`Excel2PDFCatalog.config`, `fonts/`, `example_excel/`, `example_catalog/`, `img_products/`, `img_general/`) — from `cwd` when running from source, from `sys._MEIPASS` when frozen. `writable_path(rel_path)` resolves *runtime-writable* files (`config.json`, `logs/app.log`, `tmp/`, `crash.log`, `startup.log`) — from `cwd` normally, but from `~/Library/Application Support/Excel2PDFCatalog` when frozen on macOS (a `.app` launched from Finder/Dock has its home directory as `cwd`, not the app bundle). `Excel2PDFCatalog.py` installs a global `sys.excepthook` that writes tracebacks to `writable_path("crash.log")` before any other import, since a windowed PyInstaller build has no visible stdout/stderr. When adding a new file path anywhere in the app, route it through one of these two helpers rather than joining against `cwd` or `__file__` directly.

**`build_pdf()` internals:** the per-row loop is decomposed into helpers in `app/build_PDF.py` — `_clean_row_fields` (fills/logs missing Excel cells), `_format_price`, `_insert_category_page`/`_insert_company_page` (pagination side effects on the module-level `story` list), `_load_product_image` (also sanitizes the image filename from Excel via `Path(...).name` to prevent path traversal), and `_build_product_card` (builds the ReportLab `Table` for one product). `build_pdf()` itself just orchestrates these per row.

## Cross-cutting gotchas when changing things

- Renaming a `colors_dictionary` / `path_dictionary` / `flags_dictionary` key requires updating the default in `config_utils.py` **and** every direct reference in `build_PDF.py` (styles, canvas fills) **and** `ui_interface.py` generates its controls by iterating these dicts, so new keys need no UI code — but key names double as UI labels via `.replace('_',' ').capitalize()`.
- Renaming an `XLS_COLUMN_*` mapping requires updating `Excel2PDFCatalog.config` and the corresponding `config.get(...)` call in `build_PDF.py` (both must match).
- `build_PDF.py` does substantial work at **module import time** (reading the INI config, registering the font, computing page geometry) rather than inside `build_pdf()` — keep this in mind if adding tests or reordering imports.
- Never hardcode a path relative to `cwd` or `__file__` for bundled or runtime files — use `paths_utils.resource_path()` / `paths_utils.writable_path()` (see Architecture above) so behavior stays correct in the PyInstaller-frozen builds, not just when running from source.
