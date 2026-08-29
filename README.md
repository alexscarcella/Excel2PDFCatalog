# Excel2PDFCatalog

Excel2PDFCatalog is a Python tool that reads product/catalog data from an Excel file and generates one PDF catalog. It provides a minimal UI to select the Excel file and image folders and a PDF builder that composes pages from rows and linked images.

## Purpose
Excel2PDFCatalog is a lightweight utility designed to **convert Excel spreadsheets into well-formatted PDF catalogs**.  
It is particularly useful for businesses, shops, or individuals who need to quickly generate printable product catalogs from structured Excel data.

## ✨ Key Features
- 📊 **Excel to PDF conversion**: Transform tabular data into a clean, professional PDF layout.
- 🖼️ **Image support**: Include product images referenced in your Excel file.
- 🎨 **Customizable layout**: Adjust fonts, colors, and formatting to match your branding.
- ⚡ **Fast and simple**: Minimal setup required, just point to your Excel file and generate.
- 🛠️ **Cross-platform**: Works on Windows, macOS, and Linux (Python-based).

## ✨ Other Features
- Excel import: reads Excel files via ***pandas/openpyxl*** with support for common Excel formats and multiple sheets.
- Column-to-field mapping: configurable mapping between Excel columns and product fields (title, description, price, image references).
- UI-driven workflow:
  - File pickers for Excel file, one or more image folders, and output folder.
  - Controls to load/save runtime configuration (***app/config.json***).
  - Simple "Go" button to start PDF generation and a log  showing progress and errors.
- PDF generation:
  - Uses reportlab to layout pages and render text and images.
  - Supports multiple images per product (searches configured image folders).
  - Image resizing and placement logic to fit images into product frames.
- Config files:
  - ***app/config.json*** — runtime parameters (paths, page settings, logging). Generated at runtime.
  - ***Excel2PDFCatalog.config*** — project-specific mapping and rules for interpreting Excel rows.
- Error handling & logging: console output and log messages for missing images, parsing errors, and generation steps.
- Examples & assets:
  - ***example_excel/*** and ***example_catalog/*** provide sample inputs and outputs to validate layout and mapping.
- Portable & editable: code organized to allow quick changes to layout logic, mapping rules, or PDF styling.

## ⚙️ Tech stack used

![Stack Fingerprint](https://stackfingerprint.vercel.app/api/card?repo=alexscarcella/Excel2PDFCatalog&theme=golden&layout=compact&size=xl&icons=mono&pills=round)

## 📦 Download (no Python needed)

Ready-to-run builds are published under [Releases](https://github.com/alexscarcella/Excel2PDFCatalog/releases):

| Your machine | File to download |
|---|---|
| Windows | `Excel2PDFCatalog-Windows-vX.Y.Z.zip` → extract and run the `.exe` |
| Mac with Apple Silicon (M1/M2/M3/M4) | `Excel2PDFCatalog-macOS-AppleSilicon-vX.Y.Z.dmg` |
| Mac with Intel processor | `Excel2PDFCatalog-macOS-Intel-vX.Y.Z.dmg` |

Not sure which Mac you have? Apple menu → *About This Mac*: "Chip Apple M…" means Apple Silicon, "Intel" means Intel.
The two macOS builds are **not** interchangeable: the Apple Silicon build does not run on Intel Macs (Rosetta 2 translates
Intel → Apple Silicon, not the other way around).

On first launch macOS blocks the app because it is not signed with a Developer ID: right-click the app → *Open* → *Open*.

## 🛠️ Requirements (running from source)

- **Python 3.11+**
- Dependencies listed in app/requirements.txt (notably: reportlab, pillow, pandas, openpyxl)

## 🚀 Installation & Run (Windows)

### 1. Create and activate a virtual environment
```bash
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install dependencies
```bash
pip install -r app/requirements.txt
```

### 3. Run the application
```bash
python Excel2PDFCatalog.py
```

👉 Alternatively, launch directly via VS Code using ``.vscode/launch.json``

## ⚙️ Configuration

``config.json`` → to set default folders, page size, and other runtime options. It's possibile to change this parameters via graphic user interface.

``Excel2PDFCatalog.config`` → to change column mappings and product-level rules.

📂 Project Structure

```bash
Excel2PDFCatalog/
├── Excel2PDFCatalog.py        # Main entrypoint (UI + workflow)
├── app/
│   ├── config_utils.py        # Configuration management
│   ├── ui_interface.py        # UI logic
│   ├── build_PDF.py           # PDF generation (build_pdf function)
│   └── requirements.txt       # Dependencies
├── img_products/              # Product images
├── img_general/               # General images
├── example_excel/             # Example Excel files
├── example_catalog/           # Example PDF catalogs
└── fonts/                     # Custom fonts
└── config.json                # Catalogue parameters (generated after the first run)
└── Excel2PDFCatalog.config    # Excel columns mapping and other parameters
```

## ▶️ Usage

The window is organised into tabs, in the order you normally fill them in. The
language selector (top-right) and the bottom action bar are always visible; the
interface is available in **Italian and English**, switchable at runtime (the
choice is saved in `config.json`).

1. Start the app.
2. **Sources / Sorgenti** — pick the Excel file, the intro `.txt` file, and the
   folders (output, product images, general images, temp). A ✔ / ✕ marker next to
   each row tells you whether the path exists.
3. **Catalog / Catalogo** — set the cover title, subtitle and footer.
4. **Options / Opzioni** — toggle the layout flags (each has a one-line
   description).
5. **Colors / Colori** — the colours are grouped by the region of the PDF they
   affect; click a swatch to pick a colour or type a hex value, and use ↺ to
   restore a single default.
6. Click **Save & build PDF / Salva e genera PDF**. If something is missing the
   status bar says what and jumps you back to the Sources tab; otherwise the PDF
   is written to the output folder. Column mapping still lives in
   `Excel2PDFCatalog.config`.

## 📄 Preview

An Excel file with columns Name, Price, Image can produce a PDF catalog with:

- Product title
- Formatted price
- Linked image from img_products/

> **Note:** the screenshots below predate the tabbed `ttk` interface and will be
> refreshed. The layout is now organised into the Sources / Catalog / Options /
> Colors tabs described under [Usage](#️-usage).

### UI Preview (Windows):
<img src="https://github.com/alexscarcella/Excel2PDFCatalog/blob/main/assets/Preview_Windows.png?raw=true" alt="Windows UI Screenshot" width="80%">

### UI Preview (MacOS)
<img src="https://github.com/alexscarcella/Excel2PDFCatalog/blob/main/assets/Preview_MacOS.png?raw=true" alt="MacOS UI Screenshot" width="85%">

## 🛠️ Troubleshooting

- Verify that image filenames referenced in Excel match actual files in the provided image folders.
- If an image is missing, the generator logs a warning and continues (placeholder behavior depends on config).
- Reinstall dependencies inside the active virtualenv if import errors occur.
- Check the VS Code terminal/output for full error traces when debugging.

## 🤝 Contributing

Report bugs or suggest improvements by opening an Issue.
Submit Pull Requests for new features or optimizations.
Improve documentation and examples to help other users.

## 📌 Notes

This project is intended as an internal, editable tool. You can adapt the code and configuration files to fit specific catalog formats or layout requirements.
