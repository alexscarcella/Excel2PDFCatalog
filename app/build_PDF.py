import sys
import datetime
import warnings
import pandas as pd
import locale
import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether, KeepInFrame, NextPageTemplate
from reportlab.platypus import Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from app.logger import logger
from pathlib import Path
from xml.sax.saxutils import escape
from app.images_utils import generate_image, load_image_path
from app.paths_utils import resource_path
import app.config_utils as config_utils
import app.excel_config as excel_config


class CambiaHeader(Flowable):
    def __init__(self, titolo, header_company, colore):
        super().__init__()
        self.titolo = titolo
        self.header_company = header_company
        self.colore = colore
        self.width = 0
        self.height = 0  # non occupa spazio nella pagina

    def draw(self):
        header_state["titolo"] = self.titolo
        header_state["header_company"] = self.header_company
        header_state["colore"] = self.colore


# -------------------------------------------------
# Prima si ignoravano TUTTI i warning (warnings.simplefilter("ignore")), rischiando di
# nascondere anche FutureWarning/DeprecationWarning reali (es. di pandas quando si scrive
# una stringa placeholder in una colonna numerica, vedi _clean_row_fields). Ora si silenzia
# solo l'UserWarning "rumoroso" e non azionabile che openpyxl emette per i fogli senza uno
# stile di default esplicito.
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
# -------------------------------------------------

# Dimensioni pagina A4 (costanti).
PAGE_WIDTH, PAGE_HEIGHT = A4

# I parametri di 'Excel2PDFCatalog.config' (mapping colonne, MARGIN,
# CARD_BORDER_WIDTH, LOCALE) sono gestiti da app/excel_config.py e sono
# modificabili dalla UI. build_PDF.py li rilegge con le tre _init_* qui sotto:
# una volta all'import e di nuovo all'inizio di build_pdf(), cosi' le modifiche
# hanno effetto senza riavviare l'app. Da MARGIN dipendono anche la geometria di
# pagina e i PageTemplate, per questo _init_layout() li ricostruisce.

# Nomi di colonna del foglio Excel: valorizzati da _init_excel_mapping().
XLS_CATEGORY = XLS_COMPANY = XLS_ITEM = XLS_SIZE = XLS_PRICE = ""
XLS_COLUMN_DESCRIPTION = XLS_COLUMN_IMG = XLS_BADGE = ""


def _init_excel_mapping():
    """(Ri)legge da excel_config i nomi di colonna del foglio Excel."""
    global XLS_CATEGORY, XLS_COMPANY, XLS_ITEM, XLS_SIZE, XLS_PRICE
    global XLS_COLUMN_DESCRIPTION, XLS_COLUMN_IMG, XLS_BADGE
    cols = excel_config.all_columns()
    XLS_CATEGORY = cols["CATEGORY"]
    XLS_COMPANY = cols["COMPANY"]
    XLS_ITEM = cols["ITEM"]
    XLS_SIZE = cols["SIZE"]
    XLS_PRICE = cols["PRICE"]
    XLS_COLUMN_DESCRIPTION = cols["DESCRIPTION"]
    XLS_COLUMN_IMG = cols["IMG"]
    XLS_BADGE = cols["BADGE"]


def _init_layout():
    """(Ri)calcola la geometria di pagina (dipende da MARGIN) e ricrea Frame e
    PageTemplate, cosi' un cambio di margine dalla UI ha effetto al build."""
    global PAGE_MARGIN, USABLE_WIDTH, USABLE_HEIGHT
    global cover_frame, body_frame, matrix_3x3_frame
    global cover_page_template, body_page_template, category_page_template, matrix_3x3_page_template

    PAGE_MARGIN = excel_config.margin_cm() * cm
    USABLE_WIDTH = PAGE_WIDTH - PAGE_MARGIN - PAGE_MARGIN
    USABLE_HEIGHT = PAGE_HEIGHT - PAGE_MARGIN - PAGE_MARGIN

    cover_frame = Frame(
        PAGE_MARGIN, PAGE_MARGIN, USABLE_WIDTH, USABLE_HEIGHT,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        id='cover_frame', showBoundary=0)
    body_frame = Frame(
        PAGE_MARGIN, PAGE_MARGIN, USABLE_WIDTH, USABLE_HEIGHT,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        id='body_frame', showBoundary=0)
    matrix_3x3_frame = Frame(
        PAGE_MARGIN, PAGE_MARGIN, USABLE_WIDTH, USABLE_HEIGHT,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        id='matrix_3x3', showBoundary=0)

    cover_page_template = PageTemplate(id='Cover', frames=[cover_frame], onPage=cover_on_page)
    body_page_template = PageTemplate(id='Body', frames=[body_frame], onPage=body_on_page)
    category_page_template = PageTemplate(id='Category', frames=[body_frame], onPage=category_on_page)
    matrix_3x3_page_template = PageTemplate(id='Matrix_3x3', frames=[matrix_3x3_frame], onPage=matrix_3x3_on_page)


def _init_locale():
    """Imposta il locale definito in Excel2PDFCatalog.config (best-effort)."""
    loc = excel_config.locale_name()
    try:
        locale.setlocale(locale.LC_ALL, loc)
    except locale.Error as e:
        logger.warning("Locale '%s' not supported on this system (%s). Using system default.", loc, e)

#---------------------------------------------------
# fonts
try:
    pdfmetrics.registerFont(TTFont("Bandi Regular", resource_path("fonts/Core Bandi Face W01 Regular.ttf")))
    font_primary = "Bandi Regular"
except Exception as e:
    logger.error("Custom font registration failed (%s). Falling back to Helvetica.", e, exc_info=True)
    font_primary = "Helvetica"
#---------------------------------------------------
styles = getSampleStyleSheet()
# styles
def _init_styles():
    global styles
    styles = getSampleStyleSheet()
    logger.info("Styles initialization...")
    styles.add(ParagraphStyle(name='CoverTitle', fontName=font_primary, fontSize=50, leading=42, alignment=TA_CENTER, spaceAfter=10, textColor=config_utils.colors_dictionary["COVER_TITLE_COLOR"]))
    styles.add(ParagraphStyle(name="CoverSubtitle", fontName=font_primary, fontSize=20, alignment=TA_CENTER, textColor=config_utils.colors_dictionary["COVER_SUBTITLE_COLOR"] , spaceAfter=20))
    styles.add(ParagraphStyle(name="Footer", fontName=font_primary, fontSize=10, alignment=TA_CENTER, textColor=config_utils.colors_dictionary["FOOTER_COLOR"], spaceAfter=0))
    styles.add(ParagraphStyle(name="CategoryTitle", fontName=font_primary, fontSize=54, alignment=TA_CENTER, textColor=config_utils.colors_dictionary["CATEGORY_TITLE_COLOR"], spaceAfter=20))
    styles.add(ParagraphStyle(name="CompanyTitle", fontName=font_primary, fontSize=48, alignment=TA_CENTER, textColor=config_utils.colors_dictionary["COMPANY_TITLE_COLOR"], spaceAfter=20))
    styles.add(ParagraphStyle(name="TableCompanyName", fontName=font_primary, fontSize=8, alignment=TA_CENTER, textColor=config_utils.colors_dictionary["TABLE_COMPANY_NAME_COLOR"], spaceAfter=0, spaceBefore=0, textTransform='uppercase'))
    styles.add(ParagraphStyle(name="TableItem", fontName=font_primary, fontSize=11, leading=12, alignment=TA_CENTER, textColor=config_utils.colors_dictionary["TABLE_ITEM_NAME_COLOR"], spaceAfter=0))
    styles.add(ParagraphStyle(name="TableItemPrice", fontName=font_primary, fontSize=12, alignment=2, textColor=config_utils.colors_dictionary["TABLE_ITEM_PRICE_COLOR"], spaceAfter=0))
    styles.add(ParagraphStyle(name="TableItemSize", fontName=font_primary, fontSize=10, alignment=0, textColor=config_utils.colors_dictionary["TABLE_ITEM_SIZE_COLOR"], spaceAfter=0))
    styles.add(ParagraphStyle(name="TableItemBadge", fontName=font_primary, fontSize=10, alignment=2, textColor=config_utils.colors_dictionary["TABLE_ITEM_NEWS_COLOR"], spaceAfter=0))
    styles.add(ParagraphStyle(name="ParTitle1", fontName=font_primary, fontSize=30, alignment=0, textColor=config_utils.colors_dictionary["PARAGRAPH_TITLE1_COLOR"], spaceAfter=0))
    styles.add(ParagraphStyle(name="ParTitle2", fontName=font_primary, fontSize=20, alignment=0, textColor=config_utils.colors_dictionary["PARAGRAPH_TITLE2_COLOR"], spaceAfter=0))
    styles.add(ParagraphStyle(name="Par", fontName=font_primary, fontSize=14, alignment=0, textColor=config_utils.colors_dictionary["PARAGRAPH_COLOR"], spaceAfter=0))
# ---------------------------------------------------
# NB: mapping colonne, geometria di pagina (USABLE_WIDTH/HEIGHT, Frame,
# PageTemplate) e locale sono ora prodotti da _init_excel_mapping() /
# _init_layout() / _init_locale() - vedi la chiamata dopo le callback *_on_page.
#-----------------------------------------------------
# oggetti per la griglia 3x3 dei prodotti
raw_1x3_counter = 0
raw_1x3_items = ["","",""]
raw_1x3 = Table([raw_1x3_items[0], raw_1x3_items[1], raw_1x3_items[2]])
story = []

#===========================================================================
# ---------- CANVAS da associare ai template di pagina ---------------------
#===========================================================================

header_state = {"titolo": "", "header_company": "", "colore": colors.steelblue}

def cover_on_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(config_utils.colors_dictionary["COVER_BACKGROUND_COLOR"])
    canvas.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, stroke=0, fill=1)
    img_logo_path = os.path.join(f"{config_utils.path_dictionary['GENERAL_IMAGES_FOLDER_PATH']}", "logo.png")
    if Path(img_logo_path).exists():
        logger.info(f"Load LOGO image: {img_logo_path} - 13x13")
        canvas.drawImage(f"{img_logo_path}", x = (PAGE_WIDTH - 13 * cm) / 2, y = (PAGE_HEIGHT - 13 * cm) / 2, width = 13 * cm, height = 13 * cm)
    else:
        logger.warning((f"LOGO image: {img_logo_path} does not exists!"))
    canvas.restoreState()

def body_on_page(canvas, doc):
    # semplice header e footer per le pagine di testo a tutta larghezza
    canvas.saveState()
    canvas.setFillColor(config_utils.colors_dictionary["BODY_BACKGROUND_COLOR"])
    canvas.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, stroke=0, fill=1)
    canvas.setFillColor(config_utils.colors_dictionary["PARAGRAPH_COLOR"])
    canvas.setFont(font_primary, 8)
    canvas.drawString(PAGE_MARGIN, PAGE_HEIGHT - PAGE_MARGIN // 2, ' ') # prima c'era scritto "section 2" ma non mi piaceva, quindi lo lascio vuoto
    canvas.drawRightString(PAGE_WIDTH - PAGE_MARGIN, PAGE_MARGIN // 2, f'{doc.page}')
    canvas.restoreState()

def category_on_page(canvas, doc):
    # semplice header e footer per le pagine di testo a tutta larghezza
    canvas.saveState()
    canvas.setFillColor(config_utils.colors_dictionary["CATEGORY_BACKGROUND_COLOR"])
    canvas.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, stroke=0, fill=1)
    canvas.setFillColor(config_utils.colors_dictionary["CATEGORY_TITLE_COLOR"])
    canvas.setFont(font_primary, 8)
    canvas.drawRightString(PAGE_WIDTH - PAGE_MARGIN, PAGE_MARGIN // 2, f'{doc.page}')
    canvas.restoreState()

def matrix_3x3_on_page(canvas, doc):
    # header/footer per la sezione a colonne
    canvas.saveState()
    canvas.setFillColor(config_utils.colors_dictionary["PRODUCTS_BACKGROUND_COLOR"])
    canvas.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, stroke=0, fill=1)
    # canvas.setFont(font_primary, 8)
    # canvas.drawRightString(PAGE_WIDTH - PAGE_MARGIN, PAGE_MARGIN // 2, f'{doc.page}')
    #
    canvas.setFillColor(config_utils.colors_dictionary["COVER_BACKGROUND_COLOR"])
    canvas.rect(0,PAGE_HEIGHT-(1.8*cm), PAGE_WIDTH, PAGE_HEIGHT, stroke=0, fill=1)
    canvas.setFont(font_primary, 18)
    canvas.setFillColor(config_utils.colors_dictionary["BODY_BACKGROUND_COLOR"])
    canvas.drawString(PAGE_MARGIN, PAGE_HEIGHT - (1.2*cm), header_state["titolo"])
    canvas.drawRightString(PAGE_WIDTH - PAGE_MARGIN, PAGE_HEIGHT - (1.2*cm), header_state["header_company"])
    canvas.setFillColor(config_utils.colors_dictionary["CATEGORY_TITLE_COLOR"])
    canvas.setFont(font_primary, 8)
    canvas.drawRightString(PAGE_WIDTH - PAGE_MARGIN, PAGE_MARGIN // 2, f'{doc.page}')
    #
    canvas.restoreState()

#=========================================================
# ---------- init parametri da Excel2PDFCatalog.config ---
#=========================================================
# Prima esecuzione all'import: le callback *_on_page qui sopra sono gia' definite,
# quindi _init_layout() puo' costruire Frame e PageTemplate. build_pdf() richiama
# le stesse _init_* per raccogliere le modifiche fatte nel frattempo dalla UI.
_init_excel_mapping()
_init_layout()
_init_locale()

#=========================================================
# ---------- costruzione dei documento -------------------
#=========================================================
def insert_cover(title, subtitle, footer):
    global story
    # La prima PageTemplate nella lista sara' usata per la prima pagina (Cover).
    story.append(Spacer(1, 21 * cm))
    story.append(Paragraph(escape(f"{title}"), styles['CoverTitle']))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(escape(f"{subtitle}"), styles['CoverSubtitle']))
    logger.info("insert_cover OK")

def insert_body(footer):
    global story
    # Impostiamo il template Body dalla prossima pagina
    story.append(NextPageTemplate('Body'))
    story.append(PageBreak())
    story.append(Paragraph('Condizioni generali di vendita', styles['ParTitle1'])) # rendere dinamico il "Title of the text section"
    story.append(Spacer(1, 3 * cm))
    story.append(Spacer(1, 1 * cm))
    intro_path = Path(config_utils.txt_intro_file)
    if intro_path.exists():
        long_para = intro_path.read_text(encoding='utf-8')
        # FIX (revisione batch A, punto 5): il testo va sanificato PRIMA di
        # aggiungere il tag <br/>, altrimenti escape() lo trasformerebbe in testo visibile.
        long_para = escape(long_para).replace('\n', '<br/>')
        logger.info(f"Load intro text file: {config_utils.txt_intro_file}")
        logger.info(long_para)
        story.append(Paragraph(long_para, styles['Par']))
        story.append(Spacer(1, 4 * cm))
    else:
        logger.error("Intro text file not found: %s", config_utils.txt_intro_file)
    story.append(Paragraph(escape(f"{footer}"), styles['Footer']))
    logger.info("insert_body OK")

def flush_1x3_row():
    global raw_1x3_items
    global story
    global raw_1x3_counter
    global raw_1x3
    logger.info(f"........... FLUSH: {raw_1x3_counter}")
    # impostazione della tabella contenitore che crea una riga di 3 prodotti affiancati
    # quando la pagina e' piena ci sono 3 righe (3 di queste tabella) a creare 
    # una griglia 3x3 sulla pagina
    raw_1x3 = Table([[raw_1x3_items[0], raw_1x3_items[1], raw_1x3_items[2]]],
                        colWidths=[USABLE_WIDTH/3, USABLE_WIDTH/3, USABLE_WIDTH/3],
                        rowHeights=[USABLE_HEIGHT/3])
    raw_1x3.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), config_utils.colors_dictionary["PRODUCTS_BACKGROUND_COLOR"]),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ("VALIGN", (0, 0), (-1,-1), "MIDDLE"),
        # niente 'GRID': tracciava una hairline (spesso visibile) sui bordi
        # verticali fra le 3 colonne e sul perimetro della griglia
    ]))
    story.append(KeepTogether(raw_1x3))
    raw_1x3_items = ["","",""]
    raw_1x3_counter = 0

#=========================================================
# ---------- funzioni di supporto per build_pdf() --------
#=========================================================
# REFACTOR (punto 7 della revisione): il corpo di build_pdf() era un unico
# ciclo di ~180 righe che mescolava validazione dei dati Excel, logica di
# paginazione (categoria/azienda), caricamento immagini e costruzione delle
# tabelle ReportLab. E' stato scomposto nelle funzioni sottostanti, ciascuna
# con una singola responsabilita', per migliorarne leggibilita' e manutenibilita'.
# Il comportamento originale e' stato preservato; le uniche differenze volute
# sono segnalate nei commenti di ogni funzione.

def _clean_row_fields(r):
    """Sanifica i campi obbligatori di una riga Excel: se un valore e' vuoto/NaN,
    lo sostituisce con un default e registra un warning nel log."""
    # MODIFICA (punto 10 della revisione): in origine solo CATEGORY, COMPANY, BADGE
    # e COLUMN_IMG venivano validati; ITEM e SIZE mancanti finivano nel PDF come
    # celle vuote senza alcun warning. Ora vengono sanificati anch'essi, in modo
    # coerente con gli altri campi. ITEM viene controllato per primo perche' il
    # suo valore e' usato nei messaggi di log degli altri controlli.
    if r[XLS_ITEM] == "" or pd.isna(r[XLS_ITEM]):
        logger.warning("XLS_ITEM not defined for a row (category=%s)", r[XLS_CATEGORY])
        r[XLS_ITEM] = "--------"
    if r[XLS_CATEGORY] == "" or pd.isna(r[XLS_CATEGORY]):
        logger.warning(f"{r[XLS_ITEM]} - XLS_CATEGORY not defined")
        r[XLS_CATEGORY] = "--------"
    if r[XLS_COMPANY] == "" or pd.isna(r[XLS_COMPANY]):
        logger.warning(f"{r[XLS_ITEM]} - XLS_COMPANY not defined")
        r[XLS_COMPANY] = "--------"
    if r[XLS_BADGE] == "" or pd.isna(r[XLS_BADGE]):
        logger.warning(f"{r[XLS_ITEM]} - XLS_BADGE not defined")
        r[XLS_BADGE] = ""
    if r[XLS_COLUMN_IMG] == "" or pd.isna(r[XLS_COLUMN_IMG]):
        logger.warning(f"{r[XLS_ITEM]} - XLS_COLUMN_IMG not defined. Set default value.")
        r[XLS_COLUMN_IMG] = "default"
    if r[XLS_SIZE] == "" or pd.isna(r[XLS_SIZE]):  # nuovo controllo (punto 10)
        logger.warning(f"{r[XLS_ITEM]} - XLS_SIZE not defined")
        r[XLS_SIZE] = ""
    return r


def _format_price(r):
    """Formatta il prezzo del prodotto (stringa vuota se nascosto o non valido)."""
    formatted_price = ""
    try:
        if config_utils.flags_dictionary["HIDE_PRICES"] == False:
            # FIX (revisione batch A, punto 2): float('nan') non solleva ValueError,
            # quindi una cella prezzo vuota (NaN in pandas) finiva formattata come
            # la stringa letterale "€ nan" invece di passare per il ramo di warning.
            if pd.isna(r[XLS_PRICE]):
                raise ValueError("price is NaN")
            formatted_price = f"€ {float(r[XLS_PRICE]):.2f}"
    except (ValueError, TypeError, KeyError):
        logger.warning(f"{r[XLS_ITEM]} - XLS_PRICE not defined")
    return formatted_price


def _insert_category_page(category_name):
    """Pubblica la griglia 3x3 residua e, se FULL_PAGE_CATEGORY e' attivo,
    inserisce una pagina dedicata al titolo della categoria, prima di passare
    al template dei prodotti. Va chiamata solo quando la categoria cambia."""
    global story
    if raw_1x3_items[0] != "":
        flush_1x3_row()  # pubblico eventuali prodotti residui della categoria precedente
    if config_utils.flags_dictionary["FULL_PAGE_CATEGORY"] == True:
        story.append(NextPageTemplate('Category'))  # scelgo il nuovo template
        story.append(PageBreak())  # forzo il cambio pagina
        logger.info(f"Category: {category_name}")
        story.append(Spacer(1, 5 * cm))
        story.append(Paragraph(escape(str(category_name)), styles['CategoryTitle']))
    story.append(NextPageTemplate('Matrix_3x3'))  # scelgo il template per i prodotti
    if config_utils.flags_dictionary["BREAK_PAGE_COMPANY"] == False:
        story.append(PageBreak())


def _insert_company_page(r):
    """Se BREAK_PAGE_COMPANY e' attivo, pubblica la griglia residua e forza un
    cambio pagina con l'header azienda/categoria; altrimenti si limita a
    pubblicare la griglia residua. Va chiamata solo quando l'azienda cambia."""
    global story
    if raw_1x3_items[0] != "":
        flush_1x3_row()  # se ho prodotti residui nella riga, li pubblico
    if config_utils.flags_dictionary["BREAK_PAGE_COMPANY"] == True:
        story.append(CambiaHeader(r[XLS_CATEGORY], r[XLS_COMPANY], colors.steelblue))
        story.append(PageBreak())
    logger.info(f"     Company: {r[XLS_COMPANY]}")


def _load_product_image(r):
    """Carica l'immagine del prodotto cercando prima il file corrispondente al
    codice Excel, poi (se abilitato) generandone una casuale, infine ricadendo
    su default.png. Ritorna un oggetto reportlab Image, oppure None."""
    # 4.1 cm (era 4.4): la scheda ha ora due righe ad altezza fissa (nome ~1.8 cm
    # e formato/prezzo ~0.95 cm); ridurre di poco l'immagine mantiene il totale
    # dentro la cella della griglia 3x3 con un margine di sicurezza.
    IMAGE_SIZE = 4.1 * cm
    img = None
    try:
        # FIX SICUREZZA (punto 8 della revisione): il valore della cella Excel veniva
        # concatenato al path senza sanitizzazione, permettendo path traversal in lettura
        # (es. una cella con "../../file" avrebbe potuto far leggere file fuori dalla
        # cartella immagini). Path(...).name tiene solo il nome del file, scartando
        # qualunque componente di percorso.
        safe_image_name = Path(str(r[XLS_COLUMN_IMG])).name
        base_image_file_path = Path(f"{config_utils.path_dictionary['PRODUCTS_IMAGES_FOLDER_PATH']}/{safe_image_name}")
        img_file_path = load_image_path(base_image_file_path)
        if img_file_path is not None:
            logger.info(f"Product image founded! {img_file_path}")
            img = Image(img_file_path, IMAGE_SIZE, IMAGE_SIZE)
        elif config_utils.flags_dictionary["GENERATE_RANDOM_PRODUCTS_IMAGE"] == True:
            img_file_path = f"{config_utils.path_dictionary['TMP_SYSTEM_FOLDER_PATH']}/{safe_image_name}.png"
            logger.warning(f"Product image not founded! Build new file... {img_file_path}")
            generate_image(800, 20, img_file_path)
            img = Image(img_file_path, IMAGE_SIZE, IMAGE_SIZE)
        else:
            img_file_path = Path(f"{config_utils.path_dictionary['PRODUCTS_IMAGES_FOLDER_PATH']}/default.png")
            if Path(img_file_path).exists():
                logger.warning(f"Product image not founded! Load default image: {img_file_path}")
                img = Image(img_file_path, IMAGE_SIZE, IMAGE_SIZE)
            else:
                logger.error(f"Default image not founded! {img_file_path}")
    except (OSError, KeyError):
        logger.error("Product image not founded! ", exc_info=True)
    return img


def _build_product_card(r, img, formatted_price):
    """Costruisce la tabella ReportLab (scheda prodotto) con immagine, azienda,
    nome, formato/prezzo e badge, pronta per essere inserita nella griglia 3x3."""
    TABLE_GAP = 0.2 * cm
    # FIX (revisione batch A, punto 5): i valori Excel vanno sanificati con escape()
    # prima di essere avvolti nei tag <b>/<i> propri dell'app, altrimenti un valore
    # contenente "&"/"<"/">" produce markup non valido e interrompe l'intera build.
    formatted_company = f"<b><i>{escape(str(r[XLS_COMPANY]))}</i></b>"
    formatted_item = f"<b>{escape(str(r[XLS_ITEM]))}</b>"
    formatted_size = f"{escape(str(r[XLS_SIZE]))}"
    formatted_badge = f"{escape(str(r[XLS_BADGE]))}"

    # Nome prodotto: puo' arrivare a 3-4 righe. Gli si assegna quasi tutto lo
    # spazio verticale libero della scheda (NAME_ROW_HEIGHT) e quasi tutta la
    # larghezza (padding orizzontale minimo, vedi TableStyle sotto), cosi' il
    # testo si distribuisce su piu' righe a corpo pieno invece di essere
    # rimpicciolito. Il KeepInFrame(mode='shrink') resta come rete di sicurezza:
    # scala il font SOLO per i nomi che eccedono anche NAME_ROW_HEIGHT, senza mai
    # sforare il bordo arrotondato. L'altezza della cella e' fissa, quindi il
    # footprint della scheda e la griglia 3x3 (9 schede/pagina) non cambiano.
    NAME_ROW_HEIGHT = 1.8 * cm
    name_flowable = KeepInFrame(
        0, NAME_ROW_HEIGHT,
        [Paragraph(formatted_item, styles['TableItem'])],
        mode='shrink', hAlign='CENTER', vAlign='MIDDLE',
    )

    # La riga formato/prezzo (indice 3) ha altezza FISSA (SIZE_ROW_HEIGHT). Se
    # fosse a contenuto libero, un valore di 'Formato' lungo (es. "Confezione da
    # 10") andrebbe a capo su 2 righe e farebbe crescere l'intera scheda oltre la
    # cella della griglia 3x3: il bordo arrotondato si deformava e si
    # sovrapponeva alle schede vicine. Con l'altezza fissa il footprint resta
    # costante; formato e prezzo sono avvolti in un KeepInFrame(mode='shrink')
    # che li rimpicciolisce solo se non entrano nella riga.
    SIZE_ROW_HEIGHT = 0.95 * cm
    size_flowable = KeepInFrame(
        0, SIZE_ROW_HEIGHT, [Paragraph(formatted_size, styles['TableItemSize'])],
        mode='shrink', hAlign='LEFT', vAlign='MIDDLE',
    )
    price_flowable = KeepInFrame(
        0, SIZE_ROW_HEIGHT, [Paragraph(formatted_price, styles['TableItemPrice'])],
        mode='shrink', hAlign='RIGHT', vAlign='MIDDLE',
    )

    info = [
        [img, ""],
        [Paragraph(formatted_company, styles['TableCompanyName']), ""],
        [name_flowable, ""],
        [size_flowable, price_flowable]
    ]
    table_item = Table(info, colWidths=[USABLE_WIDTH/6-TABLE_GAP, USABLE_WIDTH/6-TABLE_GAP], rowHeights=[None, 0.5*cm, NAME_ROW_HEIGHT, SIZE_ROW_HEIGHT])
    table_item.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), config_utils.colors_dictionary["TABLE_BACKGROUND_COLOR"]),
        ("VALIGN", (0, 0), (-1,-1), "MIDDLE"),
        ('ALIGN',(0,0),(0,-1),'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0.2 * cm),
        ('TOPPADDING', (0,0), (-1,-1), 0.3 * cm),
        ('RIGHTPADDING', (0,0), (-1,-1), 0.3 * cm),
        ('LEFTPADDING', (0,0), (-1,-1), 0.3 * cm),
        # la riga del nome (indice 2) sfrutta quasi tutta la larghezza della
        # scheda: padding orizzontale minimo per non forzare a capo troppo presto
        ('LEFTPADDING', (0,2), (-1,2), 3),
        ('RIGHTPADDING', (0,2), (-1,2), 3),
        # riga formato/prezzo (indice 3): padding ridotto su tutti i lati per
        # lasciare piu' spazio utile al testo dentro la riga ad altezza fissa
        ('TOPPADDING', (0,3), (-1,3), 4),
        ('BOTTOMPADDING', (0,3), (-1,3), 3),
        ('LEFTPADDING', (0,3), (-1,3), 4),
        ('RIGHTPADDING', (0,3), (-1,3), 4),
        # NB: niente 'GRID' qui. Con 'ROUNDEDCORNERS' il perimetro tracciato da
        # GRID resta a spigoli vivi e appariva come una sottile riga verticale
        # doppia accanto al bordo arrotondato (piu' evidente sulla fila centrale
        # della griglia). Le linee interne non servono: sarebbero comunque del
        # colore dello sfondo scheda.
        ('BOX', (0, 0), (-1, -1), excel_config.card_border_width(), config_utils.colors_dictionary["TABLE_BORDER_COLOR"]),
        ('SPAN',(0,0),(-1,0)),
        ('SPAN',(0,1),(-1,1)),
        ('SPAN',(0,2),(-1,2)),
        ('ROUNDEDCORNERS', [10,10,10,10])
    ]))
    logger.info(f"            {r[XLS_CATEGORY]} - {r[XLS_COMPANY]} - {r[XLS_ITEM]} - {r[XLS_SIZE]} - OK")

    # inserisco una tabella più grande, che contenga la scheda
    # ed abbia una prima riga per inserire il badge, tipo "NOVITà"
    table_item_big_info = [
        [Paragraph(formatted_badge, styles['TableItemBadge'])],   # riga 1
        [table_item]                                              # riga 2
    ]
    table_item_big = Table(table_item_big_info, rowHeights=[0.3*cm, None])
    table_item_big.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), config_utils.colors_dictionary["PRODUCTS_BACKGROUND_COLOR"]),
        # niente 'GRID': solo hairline inutili del colore dello sfondo
        ("VALIGN", (0, 0), (0,-1), "BOTTOM"),
        ("VALIGN", (0, 0), (1,-1), "TOP"),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ("VALIGN", (0, 0), (-1,-1), "MIDDLE")
    ]))
    return table_item_big


# metodo che costruisce il file PDF
def _emit_progress(cb, **event):
    """Invoca `cb` (se presente) con un dict che descrive l'avanzamento.

    Chiavi: 'phase' ('rows' | 'render' | 'done'), 'fraction' (0.0-1.0 sul
    totale), e per la fase 'rows' anche 'index', 'total', 'category',
    'company', 'product'. Un'eccezione nel callback non blocca la build.
    """
    if cb is None:
        return
    try:
        cb(event)
    except Exception:  # pragma: no cover - il progresso non deve mai far fallire la build
        logger.warning("progress_cb ha sollevato un'eccezione", exc_info=True)


def build_pdf(progress_cb=None):
    """Genera il PDF del catalogo.

    progress_cb: callable opzionale invocato con un dict di avanzamento
    (vedi _emit_progress). La fase 'rows' copre 0-90%% (una notifica per
    riga Excel, con categoria/produttore/prodotto correnti), la fase
    'render' 90-100%% (assemblaggio ReportLab). Serve alla UI per animare
    una barra 0-100%% e un log scorrevole senza bloccare il main thread.

    Ritorna il path del file PDF creato (str).
    """
    global raw_1x3_counter, raw_1x3_items, story, header_state
    #---------------------------------------------------
    #
    logger.info("Init 'build_pdf'...")
    #
    # styles
    _init_styles()
    # (ri)leggo mapping colonne, geometria di pagina e locale da
    # Excel2PDFCatalog.config: cosi' le modifiche fatte dalla UI valgono subito.
    _init_excel_mapping()
    _init_layout()
    _init_locale()
    #
    raw_1x3_counter = 0
    raw_1x3_items = ["","",""]
    story = []
    # FIX (revisione batch D, punto 13): header_state non veniva mai resettato -
    # se una build precedente (nella stessa sessione UI) aveva BREAK_PAGE_COMPANY
    # attivo, il banner categoria/azienda restava quello dell'ultima CambiaHeader
    # anche in una build successiva con il flag disattivato.
    header_state = {"titolo": "", "header_company": "", "colore": colors.steelblue}
    #
    # file di output
    formatted_datetime =  datetime.datetime.now().strftime("%Y%m%d_%H%M%S") # Formato Giorno/Mese/Anno
    pdf_file_name = f"{config_utils.path_dictionary['OUTPUT_PDF_FOLDER_PATH']}/{formatted_datetime}_Catalog.pdf"
    #
    doc = BaseDocTemplate(pdf_file_name, pagesize=A4, leftMargin=PAGE_MARGIN, rightMargin=PAGE_MARGIN, topMargin=PAGE_MARGIN, bottomMargin=PAGE_MARGIN, title=None, author=None)
    doc.addPageTemplates([cover_page_template, body_page_template, category_page_template, matrix_3x3_page_template])
    #
    insert_cover(config_utils.title, config_utils.subtitle, config_utils.footer)
    #
    insert_body(config_utils.footer)
    # leggo il file:
    try:
        df = pd.read_excel(config_utils.excel_file)
    except Exception as e:
        logger.error("FILE EXCEL ERROR!! ", exc_info=True)
        raise
    # FIX (revisione batch A, punto 3): senza questo controllo, una colonna
    # mancante (es. header rinominato dall'utente) faceva risalire un KeyError
    # non gestito dal primo accesso a r[...] dentro _clean_row_fields/_format_price,
    # con un traceback poco chiaro. XLS_COLUMN_DESCRIPTION non e' incluso perche'
    # non viene mai letto durante l'elaborazione delle righe (in excel_config e'
    # l'unica colonna con flag "obbligatoria" a False).
    required_columns = excel_config.required_column_names()
    missing_columns = [c for c in required_columns if c not in df.columns]
    if missing_columns:
        logger.error("Missing required column(s) in Excel file: %s", missing_columns)
        raise ValueError(f"Missing required column(s) in Excel file: {missing_columns}")
    #
    previous_category = "" # la variabile che mi permette di capire se c'e' un cambio di categoria in modo da inserire una pagina con il titolo
    previous_company = "" # la variabile che mi permette di capire se c'e' un cambio di azienda in modo da inserire un titolo
    #
    total_rows = len(df)
    for row_index, (_, r) in enumerate(df.iterrows(), start=1):  # scorro le righe nel file
        r = _clean_row_fields(r)  # verifico che non ci siano campi nulli o non validi
        formatted_price = _format_price(r)
        # notifico la UI della riga in elaborazione (fase 'rows' = 0-90%)
        _emit_progress(
            progress_cb, phase="rows", index=row_index, total=total_rows,
            fraction=(row_index / total_rows * 0.9) if total_rows else 0.0,
            category=str(r[XLS_CATEGORY]), company=str(r[XLS_COMPANY]),
            product=str(r[XLS_ITEM]))

        # ---------- verifico per inserire la pagina del titolo della categoria
        if previous_category != r[XLS_CATEGORY]:
            _insert_category_page(r[XLS_CATEGORY])
            previous_category = r[XLS_CATEGORY]  # aggiorno la variabile di controllo della categoria
            previous_company = ""  # resetto la variabile di controllo della company

        # ---------- verifico per inserire il titolo del produttore
        if previous_company != r[XLS_COMPANY]:  # se l'azienda è diversa dalla precedente
            _insert_company_page(r)
            previous_company = r[XLS_COMPANY]

        # --------- Leggo le informazioni del singolo prodotto e costruisco la scheda
        img = _load_product_image(r)
        raw_1x3_items[raw_1x3_counter] = _build_product_card(r, img, formatted_price)

        raw_1x3_counter = raw_1x3_counter + 1
        if raw_1x3_counter == 3: flush_1x3_row()
    # FIX (revisione batch A, punto 1): senza questa flush, l'ultimo gruppo di
    # 1 o 2 prodotti (quando il conteggio totale non e' multiplo di 3) non veniva
    # mai pubblicato in 'story' - un file con una sola riga produceva un PDF senza
    # nessun prodotto. Stessa guardia gia' usata in _insert_category_page/_insert_company_page.
    if raw_1x3_items[0] != "":
        flush_1x3_row()
    logger.info(f"Read all items in XLSX file")

    if progress_cb is not None:
        size_est = [0]

        def _render_cb(typ, value):
            # ReportLab: 'SIZE_EST' col totale stimato di flowable, poi
            # 'PROGRESS' col conteggio corrente. Mappo la fase 'render' su 90-100%.
            if typ == "SIZE_EST":
                size_est[0] = value or 0
            elif typ == "PROGRESS" and size_est[0]:
                frac = 0.9 + 0.1 * min(1.0, value / size_est[0])
                _emit_progress(progress_cb, phase="render", fraction=frac)

        try:
            doc.setProgressCallBack(_render_cb)
        except Exception:  # pragma: no cover - difensivo, non deve mai bloccare la build
            logger.warning("setProgressCallBack non disponibile", exc_info=True)

    try:
        doc.build(story)
        logger.info(f"******* END OK --> '{pdf_file_name}' created ")
    except Exception as e:
        logger.error("doc.build() failed: %s", e, exc_info=True)
        raise

    _emit_progress(progress_cb, phase="done", fraction=1.0)
    return pdf_file_name
