# i18n.py
# Livello di localizzazione dell'interfaccia (italiano / inglese), senza dipendenze
# esterne e senza Tkinter: puo' essere importato anche dai test.
#
# - t(key, **kw)          -> stringa tradotta nella lingua attiva (fallback: EN, poi la key stessa)
# - set_language(lang)    -> cambia lingua e richiama tutti gli hook di ri-traduzione registrati
# - get_language()        -> "it" | "en"
# - on_language_change(fn)-> registra un hook; clear_hooks() li rimuove tutti
# - detect_default()      -> deduce la lingua dal locale di sistema ("it" se it-*, altrimenti "en")
# - field_label(key)/field_hint(key) -> etichette/descrizioni dei campi generati dai dizionari
#                            di config_utils (con fallback "Nome_chiave" -> "Nome chiave")
#
# NOTA: si traducono SOLO le stringhe mostrate all'utente. Le CHIAVI dei dizionari
# (COVER_TITLE_COLOR, BREAK_PAGE_COMPANY, OUTPUT_PDF_FOLDER_PATH, ...) restano in
# inglese perche' vengono serializzate in config.json e lette da build_PDF.py.

LANGUAGES = ("it", "en")
_DEFAULT = "it"

_lang = _DEFAULT
_hooks = []


# ---------------------------------------------------------------------------
# Metadati di presentazione (indipendenti dalla lingua)
# ---------------------------------------------------------------------------

# Ordine e raggruppamento dei 19 colori, per regione del PDF prodotto.
COLOR_GROUPS = [
    ("cover", ["COVER_TITLE_COLOR", "COVER_SUBTITLE_COLOR", "COVER_BACKGROUND_COLOR"]),
    ("intro", ["BODY_BACKGROUND_COLOR", "PARAGRAPH_TITLE1_COLOR", "PARAGRAPH_TITLE2_COLOR",
               "PARAGRAPH_COLOR", "FOOTER_COLOR"]),
    ("category", ["CATEGORY_TITLE_COLOR", "CATEGORY_BACKGROUND_COLOR", "COMPANY_TITLE_COLOR"]),
    ("grid", ["PRODUCTS_BACKGROUND_COLOR"]),
    ("card", ["TABLE_COMPANY_NAME_COLOR", "TABLE_ITEM_NAME_COLOR", "TABLE_ITEM_PRICE_COLOR",
              "TABLE_ITEM_SIZE_COLOR", "TABLE_ITEM_NEWS_COLOR", "TABLE_BACKGROUND_COLOR",
              "TABLE_BORDER_COLOR"]),
]

# Ordine di visualizzazione delle opzioni (flag). Le chiavi non elencate qui
# vengono comunque mostrate, in coda.
FLAG_ORDER = [
    "FULL_PAGE_CATEGORY",
    "BREAK_PAGE_COMPANY",
    "ADD_PRODUCT_DESCRIPTION",
    "HIDE_PRICES",
    "GENERATE_RANDOM_PRODUCTS_IMAGE",
]


# ---------------------------------------------------------------------------
# Tabella di traduzione
# ---------------------------------------------------------------------------

TRANSLATIONS = {
    "it": {
        "topbar.subtitle": "Da Excel a catalogo PDF",
        "lang.it": "Italiano",
        "lang.en": "English",

        "tab.sources": "Sorgenti",
        "tab.catalog": "Catalogo",
        "tab.options": "Opzioni",
        "tab.colors": "Colori",
        "tab.excelcols": "Colonne Excel",

        "menu.file": "File",
        "menu.file.save": "Salva configurazione",
        "menu.file.reset": "Ripristina tutto ai valori predefiniti",
        "menu.file.quit": "Esci",
        "menu.language": "Lingua",
        "menu.help": "Aiuto",
        "menu.help.notes": "Note…",
        "menu.help.about": "Informazioni…",

        "btn.browse": "Sfoglia…",
        "btn.save_config": "Salva configurazione",
        "btn.build": "Salva e genera PDF",

        "sources.files": "File",
        "sources.folders": "Cartelle",
        "sources.none_selected": "(nessuna selezione)",
        "sources.excel.label": "File Excel (.xlsx) con l'elenco dei prodotti",
        "sources.excel.dialog": "Seleziona il file Excel (.xlsx)",
        "sources.intro.label": "File di testo (.txt) con l'introduzione",
        "sources.intro.dialog": "Seleziona il file .txt di introduzione",

        "status.missing": "non trovato",
        "status.ready": "Pronto.",
        "status.saved": "Configurazione salvata.",
        "status.save_failed": "Salvataggio della configurazione non riuscito. Controlla il log.",
        "status.building": "Generazione del PDF in corso…",
        "status.build_ok": "PDF generato correttamente.",
        "status.problems": "Configurazione incompleta ({n}): {first}",

        "problem.excel_missing": "file Excel non trovato",
        "problem.path_missing": "cartella non trovata ({name})",

        "catalog.texts": "Testi del catalogo",
        "catalog.title": "Titolo",
        "catalog.subtitle": "Sottotitolo",
        "catalog.footer": "Piè di pagina",
        "catalog.title.hint": "Appare grande al centro della copertina.",
        "catalog.subtitle.hint": "Appare sotto il titolo, in copertina.",
        "catalog.footer.hint": "Appare in fondo alla pagina introduttiva.",

        "colors.reset_all": "Ripristina i colori predefiniti",
        "colors.reset_one": "Ripristina questo colore",
        "colorgroup.cover": "Copertina",
        "colorgroup.intro": "Pagine introduttive",
        "colorgroup.category": "Pagine categoria / produttore",
        "colorgroup.grid": "Griglia prodotti",
        "colorgroup.card": "Scheda prodotto",
        "colorgroup.other": "Altri colori",

        "dialog.confirm.title": "Conferma",
        "dialog.confirm.msg": "Vuoi procedere con questa operazione?",
        "dialog.done.title": "Completato",
        "dialog.done.msg": "Operazione completata!",
        "dialog.error.title": "Errore",
        "dialog.build_failed.msg": "Generazione non riuscita: {err}",
        "dialog.save_failed.msg": "Impossibile salvare il file di configurazione. Controlla il log.",
        "dialog.reset.title": "Ripristina impostazioni",
        "dialog.reset.msg": "Ripristinare colori e opzioni ai valori predefiniti?",
        "dialog.about.title": "Informazioni",
        "dialog.about.msg": ("Excel2PDFCatalog {version}\n\n"
                             "Converte un elenco prodotti in formato Excel in un "
                             "catalogo PDF stampabile."),
        "dialog.notes.title": "Note",
        "dialog.pick_color": "Scegli un colore",

        "notes.intro": "NOTE:",
        "notes.1": "Il catalogo viene creato seguendo l'ordine dei prodotti nel file Excel.",
        "notes.2": ("Si consiglia di ordinare i prodotti nel file Excel almeno per le "
                    "colonne 'categoria' e 'produttore'."),
        "notes.3": ("Le celle Excel senza contenuto non sono ammesse: in tal caso il "
                    "PDF non viene prodotto."),
        "notes.4": "Il campo che contiene il prezzo deve essere numerico.",
        "notes.5": "Chiudi il foglio Excel prima di generare il PDF.",
        "notes.6": ("Tutte le immagini dei prodotti devono trovarsi nella cartella immagini, "
                    "col nome della colonna immagine di Excel (con estensione) e in formato "
                    "1:1 (quadrato). Formati supportati: png, jpg, jpeg."),
        "notes.7": "Il logo è un file logo.png in formato 1:1 (quadrato).",
        "notes.8": ("Il testo introduttivo è un file .txt con codifica UTF-8. Sono "
                    "supportati alcuni tag HTML."),

        "field.COVER_TITLE_COLOR": "Titolo copertina",
        "field.COVER_SUBTITLE_COLOR": "Sottotitolo copertina",
        "field.COVER_BACKGROUND_COLOR": "Sfondo copertina",
        "field.FOOTER_COLOR": "Piè di pagina",
        "field.CATEGORY_TITLE_COLOR": "Titolo categoria",
        "field.CATEGORY_BACKGROUND_COLOR": "Sfondo pagina categoria",
        "field.COMPANY_TITLE_COLOR": "Titolo produttore",
        "field.PRODUCTS_BACKGROUND_COLOR": "Sfondo griglia prodotti",
        "field.TABLE_COMPANY_NAME_COLOR": "Nome produttore (scheda)",
        "field.TABLE_ITEM_NAME_COLOR": "Nome prodotto (scheda)",
        "field.TABLE_ITEM_PRICE_COLOR": "Prezzo (scheda)",
        "field.TABLE_ITEM_SIZE_COLOR": "Formato (scheda)",
        "field.TABLE_ITEM_NEWS_COLOR": "Badge / etichetta (es. NOVITÀ)",
        "field.TABLE_BACKGROUND_COLOR": "Sfondo scheda",
        "field.TABLE_BORDER_COLOR": "Bordo scheda",
        "field.BODY_BACKGROUND_COLOR": "Sfondo pagine di testo",
        "field.PARAGRAPH_TITLE1_COLOR": "Titolo paragrafo 1",
        "field.PARAGRAPH_TITLE2_COLOR": "Titolo paragrafo 2",
        "field.PARAGRAPH_COLOR": "Testo paragrafo",

        "field.OUTPUT_PDF_FOLDER_PATH": "Cartella di destinazione del PDF",
        "field.PRODUCTS_IMAGES_FOLDER_PATH": "Cartella immagini prodotti",
        "field.GENERAL_IMAGES_FOLDER_PATH": "Cartella immagini generali (logo)",
        "field.TMP_SYSTEM_FOLDER_PATH": "Cartella temporanea",

        "field.FULL_PAGE_CATEGORY": "Pagina intera per il titolo di categoria",
        "field.BREAK_PAGE_COMPANY": "Cambia pagina a ogni produttore",
        "field.ADD_PRODUCT_DESCRIPTION": "Includi la descrizione del prodotto",
        "field.HIDE_PRICES": "Nascondi i prezzi",
        "field.GENERATE_RANDOM_PRODUCTS_IMAGE": "Genera un'immagine segnaposto se manca la foto",

        "hint.FULL_PAGE_CATEGORY": "Dedica una pagina intera al nome di ogni categoria merceologica.",
        "hint.BREAK_PAGE_COMPANY": "Inserisce un salto pagina ogni volta che cambia l'azienda produttrice.",
        "hint.ADD_PRODUCT_DESCRIPTION": "Aggiunge alla scheda il testo della colonna descrizione, se presente.",
        "hint.HIDE_PRICES": "I prezzi non vengono stampati nelle schede prodotto.",
        "hint.GENERATE_RANDOM_PRODUCTS_IMAGE": ("Se la foto del prodotto non viene trovata, crea un "
                                                "segnaposto colorato invece di usare default.png."),

        "excelcols.intro": ("I nomi qui sotto devono coincidere con l'intestazione (prima riga) "
                            "del foglio .xlsx selezionato."),
        "excelcols.mapping": "Mappatura colonne",
        "excelcols.advanced": "Avanzate",
        "options.layout": "Layout",
        "status.invalid_number": "Valore non valido: inserisci un numero maggiore di zero.",

        "field.XLS_COLUMN_CATEGORY": "Colonna categoria merceologica",
        "field.XLS_COLUMN_COMPANY": "Colonna azienda / produttore",
        "field.XLS_COLUMN_ITEM": "Colonna nome prodotto",
        "field.XLS_COLUMN_SIZE": "Colonna formato",
        "field.XLS_COLUMN_PRICE": "Colonna prezzo",
        "field.XLS_COLUMN_DESCRIPTION": "Colonna descrizione",
        "field.XLS_COLUMN_IMG": "Colonna codice immagine",
        "field.XLS_BADGE": "Colonna badge / etichetta",

        "hint.XLS_COLUMN_CATEGORY": "A ogni cambio di valore viene inserita una nuova pagina di categoria.",
        "hint.XLS_COLUMN_COMPANY": "Usata per il titolo del produttore e (se attivo) per il salto pagina.",
        "hint.XLS_COLUMN_ITEM": "Nome del prodotto mostrato nella scheda.",
        "hint.XLS_COLUMN_SIZE": "Formato/dimensione mostrato in basso a sinistra nella scheda.",
        "hint.XLS_COLUMN_PRICE": "Deve contenere valori numerici.",
        "hint.XLS_COLUMN_DESCRIPTION": "Testo opzionale aggiunto alla scheda se l'opzione relativa è attiva.",
        "hint.XLS_COLUMN_IMG": "Nome del file immagine (senza estensione) nella cartella immagini prodotti.",
        "hint.XLS_BADGE": "Testo della fascetta sopra la scheda (es. NOVITÀ). Può essere vuoto.",

        "field.MARGIN": "Margine pagina (cm)",
        "field.CARD_BORDER_WIDTH": "Spessore bordo scheda (pt)",
        "field.LOCALE": "Locale di sistema",
        "hint.MARGIN": "Margine bianco attorno al contenuto di ogni pagina A4.",
        "hint.CARD_BORDER_WIDTH": "Spessore del riquadro attorno a ogni scheda prodotto, in punti.",
        "hint.LOCALE": ("Scegli dall'elenco o digita un valore specifico della piattaforma "
                        "(es. it_IT.UTF-8 su macOS/Linux, Italian_Italy.1252 su Windows)."),
    },

    "en": {
        "topbar.subtitle": "From Excel to PDF catalog",
        "lang.it": "Italiano",
        "lang.en": "English",

        "tab.sources": "Sources",
        "tab.catalog": "Catalog",
        "tab.options": "Options",
        "tab.colors": "Colours",
        "tab.excelcols": "Excel columns",

        "menu.file": "File",
        "menu.file.save": "Save configuration",
        "menu.file.reset": "Reset everything to defaults",
        "menu.file.quit": "Quit",
        "menu.language": "Language",
        "menu.help": "Help",
        "menu.help.notes": "Notes…",
        "menu.help.about": "About…",

        "btn.browse": "Browse…",
        "btn.save_config": "Save configuration",
        "btn.build": "Save & build PDF",

        "sources.files": "Files",
        "sources.folders": "Folders",
        "sources.none_selected": "(nothing selected)",
        "sources.excel.label": "Excel file (.xlsx) with the product list",
        "sources.excel.dialog": "Select the Excel file (.xlsx)",
        "sources.intro.label": "Text file (.txt) with the intro",
        "sources.intro.dialog": "Select the intro .txt file",

        "status.missing": "not found",
        "status.ready": "Ready.",
        "status.saved": "Configuration saved.",
        "status.save_failed": "Could not save the configuration. Check the log.",
        "status.building": "Building the PDF…",
        "status.build_ok": "PDF built successfully.",
        "status.problems": "Incomplete configuration ({n}): {first}",

        "problem.excel_missing": "Excel file not found",
        "problem.path_missing": "folder not found ({name})",

        "catalog.texts": "Catalog texts",
        "catalog.title": "Title",
        "catalog.subtitle": "Subtitle",
        "catalog.footer": "Footer",
        "catalog.title.hint": "Shown large in the centre of the cover.",
        "catalog.subtitle.hint": "Shown under the title, on the cover.",
        "catalog.footer.hint": "Shown at the bottom of the intro page.",

        "colors.reset_all": "Reset colours to defaults",
        "colors.reset_one": "Reset this colour",
        "colorgroup.cover": "Cover",
        "colorgroup.intro": "Intro pages",
        "colorgroup.category": "Category / producer pages",
        "colorgroup.grid": "Product grid",
        "colorgroup.card": "Product card",
        "colorgroup.other": "Other colours",

        "dialog.confirm.title": "Confirmation",
        "dialog.confirm.msg": "Do you want to proceed with this operation?",
        "dialog.done.title": "Done",
        "dialog.done.msg": "Operation complete!",
        "dialog.error.title": "Error",
        "dialog.build_failed.msg": "Build failed: {err}",
        "dialog.save_failed.msg": "Failed to save the configuration file. Check the log.",
        "dialog.reset.title": "Reset settings",
        "dialog.reset.msg": "Reset colours and options to their default values?",
        "dialog.about.title": "About",
        "dialog.about.msg": ("Excel2PDFCatalog {version}\n\n"
                             "Converts an Excel product list into a printable PDF catalog."),
        "dialog.notes.title": "Notes",
        "dialog.pick_color": "Pick a colour",

        "notes.intro": "NOTES:",
        "notes.1": "The catalogue is created following the order of the products in the Excel file.",
        "notes.2": ("We recommend sorting the products in the Excel file at least by the "
                    "'category' and 'producer' columns."),
        "notes.3": ("Excel cells with no content are not allowed: in this case, the PDF "
                    "will not be produced."),
        "notes.4": "The field containing the price must be numeric.",
        "notes.5": "Close the Excel sheet before generating the PDF.",
        "notes.6": ("All product images must be in the images folder, named after the Excel "
                    "image column (with extension) and in 1:1 format (square). Supported "
                    "formats: png, jpg, jpeg."),
        "notes.7": "The logo is a logo.png file in 1:1 format (square).",
        "notes.8": ("The intro text is a .txt file with UTF-8 encoding. Some HTML tags are "
                    "supported."),

        "field.COVER_TITLE_COLOR": "Cover title",
        "field.COVER_SUBTITLE_COLOR": "Cover subtitle",
        "field.COVER_BACKGROUND_COLOR": "Cover background",
        "field.FOOTER_COLOR": "Footer",
        "field.CATEGORY_TITLE_COLOR": "Category title",
        "field.CATEGORY_BACKGROUND_COLOR": "Category page background",
        "field.COMPANY_TITLE_COLOR": "Producer title",
        "field.PRODUCTS_BACKGROUND_COLOR": "Product grid background",
        "field.TABLE_COMPANY_NAME_COLOR": "Producer name (card)",
        "field.TABLE_ITEM_NAME_COLOR": "Product name (card)",
        "field.TABLE_ITEM_PRICE_COLOR": "Price (card)",
        "field.TABLE_ITEM_SIZE_COLOR": "Size (card)",
        "field.TABLE_ITEM_NEWS_COLOR": "Badge / label (e.g. NEW)",
        "field.TABLE_BACKGROUND_COLOR": "Card background",
        "field.TABLE_BORDER_COLOR": "Card border",
        "field.BODY_BACKGROUND_COLOR": "Text pages background",
        "field.PARAGRAPH_TITLE1_COLOR": "Paragraph title 1",
        "field.PARAGRAPH_TITLE2_COLOR": "Paragraph title 2",
        "field.PARAGRAPH_COLOR": "Paragraph text",

        "field.OUTPUT_PDF_FOLDER_PATH": "PDF output folder",
        "field.PRODUCTS_IMAGES_FOLDER_PATH": "Product images folder",
        "field.GENERAL_IMAGES_FOLDER_PATH": "General images folder (logo)",
        "field.TMP_SYSTEM_FOLDER_PATH": "Temporary folder",

        "field.FULL_PAGE_CATEGORY": "Full page for the category title",
        "field.BREAK_PAGE_COMPANY": "New page for each producer",
        "field.ADD_PRODUCT_DESCRIPTION": "Include the product description",
        "field.HIDE_PRICES": "Hide prices",
        "field.GENERATE_RANDOM_PRODUCTS_IMAGE": "Generate a placeholder image when the photo is missing",

        "hint.FULL_PAGE_CATEGORY": "Devotes a full page to each product-category name.",
        "hint.BREAK_PAGE_COMPANY": "Inserts a page break whenever the producer company changes.",
        "hint.ADD_PRODUCT_DESCRIPTION": "Adds the description-column text to the product card, when present.",
        "hint.HIDE_PRICES": "Prices are not printed on the product cards.",
        "hint.GENERATE_RANDOM_PRODUCTS_IMAGE": ("When a product photo is not found, creates a coloured "
                                                "placeholder instead of using default.png."),

        "excelcols.intro": "The names below must match the header row of the selected .xlsx file.",
        "excelcols.mapping": "Column mapping",
        "excelcols.advanced": "Advanced",
        "options.layout": "Layout",
        "status.invalid_number": "Invalid value: enter a number greater than zero.",

        "field.XLS_COLUMN_CATEGORY": "Product-category column",
        "field.XLS_COLUMN_COMPANY": "Company / producer column",
        "field.XLS_COLUMN_ITEM": "Product-name column",
        "field.XLS_COLUMN_SIZE": "Size column",
        "field.XLS_COLUMN_PRICE": "Price column",
        "field.XLS_COLUMN_DESCRIPTION": "Description column",
        "field.XLS_COLUMN_IMG": "Image-code column",
        "field.XLS_BADGE": "Badge / label column",

        "hint.XLS_COLUMN_CATEGORY": "Every time this value changes a new category page is inserted.",
        "hint.XLS_COLUMN_COMPANY": "Used for the producer title and (if enabled) the page break.",
        "hint.XLS_COLUMN_ITEM": "Product name shown on the card.",
        "hint.XLS_COLUMN_SIZE": "Size shown at the bottom-left of the card.",
        "hint.XLS_COLUMN_PRICE": "Must contain numeric values.",
        "hint.XLS_COLUMN_DESCRIPTION": "Optional text added to the card when the related option is on.",
        "hint.XLS_COLUMN_IMG": "Image file name (without extension) in the product images folder.",
        "hint.XLS_BADGE": "Ribbon text above the card (e.g. NEW). May be empty.",

        "field.MARGIN": "Page margin (cm)",
        "field.CARD_BORDER_WIDTH": "Card border width (pt)",
        "field.LOCALE": "System locale",
        "hint.MARGIN": "White margin around the content of every A4 page.",
        "hint.CARD_BORDER_WIDTH": "Thickness of the frame around each product card, in points.",
        "hint.LOCALE": ("Pick from the list or type a platform-specific value "
                        "(e.g. it_IT.UTF-8 on macOS/Linux, Italian_Italy.1252 on Windows)."),
    },
}


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def get_language():
    return _lang


def set_language(lang):
    """Imposta la lingua attiva e notifica gli hook registrati."""
    global _lang
    if lang not in TRANSLATIONS:
        lang = "en" if "en" in TRANSLATIONS else _DEFAULT
    _lang = lang
    for hook in list(_hooks):
        try:
            hook()
        except Exception:  # un hook difettoso non deve bloccare il cambio lingua
            pass
    return _lang


def on_language_change(hook):
    """Registra una callback da eseguire a ogni set_language()."""
    _hooks.append(hook)
    return hook


def clear_hooks():
    """Rimuove tutti gli hook: da chiamare quando si ricostruisce la finestra."""
    _hooks.clear()


def t(key, **kw):
    """Traduci `key` nella lingua attiva. Fallback: inglese, poi la key stessa.
    Se sono passati kwargs, applica str.format()."""
    table = TRANSLATIONS.get(_lang, {})
    text = table.get(key)
    if text is None:
        text = TRANSLATIONS.get("en", {}).get(key, key)
    if kw:
        try:
            text = text.format(**kw)
        except (KeyError, IndexError, ValueError):
            pass
    return text


def field_label(key):
    """Etichetta di un campo generato da un dizionario di config_utils.
    Fallback: 'NOME_CHIAVE' -> 'Nome chiave' (come nella UI storica)."""
    text = t("field." + key)
    if text != "field." + key:
        return text
    return key.replace("_", " ").capitalize()


def field_hint(key):
    """Descrizione breve di un campo (stringa vuota se non definita)."""
    text = t("hint." + key)
    return "" if text == "hint." + key else text


def detect_default():
    """Deduci la lingua iniziale dal locale di sistema: 'it' se it-*, altrimenti 'en'."""
    import locale

    for getter in (locale.getlocale, locale.getdefaultlocale):
        try:
            value = getter()
            code = (value[0] if value else "") or ""
        except Exception:
            code = ""
        if code:
            return "it" if code.lower().startswith("it") else "en"
    return _DEFAULT
