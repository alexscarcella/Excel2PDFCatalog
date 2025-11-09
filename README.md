# Excel2PDFCatalog

Short description
-----------------
Excel2PDFCatalog is a Python tool that reads product/catalog data from an Excel file and generates one PDF catalog. It provides a minimal UI to select the Excel file and image folders and a PDF builder that composes pages from rows and linked images.

Key features
------------
- Read and parse Excel sheets (pandas / openpyxl).
- Configurable column-to-field mapping.
- PDF generation with customizable layout (reportlab).
- Support for per-product image folders.
- Simple UI for selecting inputs/outputs and starting the conversion.
- Persistent settings via JSON configuration.

Requirements
------------
- Python 3.8+
- Libraries listed in app/requirements.txt (notably: reportlab, pillow, pandas, openpyxl)

Installation and run (Windows)
------------------------------
1. Create and activate a virtual environment:
   .venv\Scripts\activate

2. Install dependencies:
   pip install -r app/requirements.txt
   (if needed: pip install reportlab pillow pandas openpyxl)

3. Run from project root:
   python Excel2PDFCatalog.py

4. Alternatively, launch via VS Code debug (.vscode/launch.json).

Configuration
-------------
- app/config.json: runtime defaults and options.
- Excel2PDFCatalog.config: column mapping and project-specific rules.
Edit these files to match your Excel layout, image folder structure, and output preferences.

Project structure (summary)
---------------------------
- Excel2PDFCatalog.py — main entrypoint (starts UI / workflow)
- app/config_utils.py — load/save configuration
- app/ui_interface.py — UI logic for file selection and starting the process
- app/build_PDF.py — PDF generation (build_pdf function)
- app/requirements.txt — dependency list
- .vscode/launch.json — VS Code debug configuration

Usage
-----
1. Start the app.
2. Select the Excel file and image folder(s) via the UI.
3. Set output folder and other options if needed.
4. Click "Go" to generate PDFs; output files are saved to the configured folder.

Troubleshooting
---------------
- Ensure image references in Excel match filenames in the provided folders.
- If library errors occur, reinstall dependencies inside the active virtualenv.
- Check the VS Code terminal/output for detailed error messages.

Notes
-----
Designed as an internal, editable tool. Modify code and configs to fit specific catalog formats or layout requirements.