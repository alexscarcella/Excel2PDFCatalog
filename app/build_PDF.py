import sys
import datetime
import warnings
import pandas as pd
import locale
import configparser
import random
import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether, PageBreak, NextPageTemplate
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from app.logger import logger
from pathlib import Path
from app.images_utils import generate_image, resize_image
import app.config_utils as config_utils

# -------------------------------------------------
warnings.simplefilter("ignore")
# -------------------------------------------------
# Crea un oggetto ConfigParser
config = configparser.ConfigParser()
config.read('Excel2PDFCatalog.config')
#---------------------------------------------------
# Mapping foglio EXCEL
XLS_CATEGORY = config.get("Excel","XLS_COLUMN_CATEGORY")
XLS_COMPANY = config.get("Excel","XLS_COLUMN_COMPANY")
XLS_ITEM = config.get("Excel","XLS_COLUMN_ITEM")
XLS_SIZE = config.get("Excel","XLS_COLUMN_SIZE")
XLS_PRICE = config.get("Excel","XLS_COLUMN_PRICE")
XLS_COLUMN_DESCRIPTION = config.get("Excel","XLS_COLUMN_DESCRIPTION")
XLS_COLUMN_IMG = config.get("Excel","XLS_COLUMN_IMG")
# immagini
# PRODUCTS_IMAGES_SUBFOLDER = config.get("Resources","PRODUCTS_IMAGES_SUBFOLDER")
# OTHER_IMAGES_SUBFOLDER = config.get("Resources","OTHER_IMAGES_SUBFOLDER")
#---------------------------------------------------
# dimensioni foglio 
PAGE_WIDTH, PAGE_HEIGHT  = A4
PAGE_MARGIN = int(config.get("Layout","MARGIN")) * cm
#---------------------------------------------------
# fonts
pdfmetrics.registerFont(TTFont("Bandi Regular", "./fonts/Core Bandi Face W01 Regular.ttf"))
font_primary = "Bandi Regular"
#---------------------------------------------------
# styles
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='CoverTitle', fontName=font_primary, fontSize=50, leading=42, alignment=TA_CENTER, spaceAfter=10, textColor=config_utils.colors_dictionary["COVER_TITLE_COLOR"]))
styles.add(ParagraphStyle(name="CoverSubtitle", fontName=font_primary, fontSize=20, alignment=TA_CENTER, textColor=config_utils.colors_dictionary["COVER_SUBTITLE_COLOR"] , spaceAfter=20))
styles.add(ParagraphStyle(name="Footer", fontName=font_primary, fontSize=10, alignment=TA_CENTER, textColor=config_utils.colors_dictionary["FOOTER_COLOR"], spaceAfter=0))
styles.add(ParagraphStyle(name="CategoryTitle", fontName=font_primary, fontSize=54, alignment=TA_CENTER, textColor=config_utils.colors_dictionary["CATEGORY_TITLE_COLOR"], spaceAfter=20))
styles.add(ParagraphStyle(name="CompanyTitle", fontName=font_primary, fontSize=48, alignment=TA_CENTER, textColor=config_utils.colors_dictionary["COMPANY_TITLE_COLOR"], spaceAfter=20))
styles.add(ParagraphStyle(name="TableCompanyName", fontName=font_primary, fontSize=8, alignment=TA_CENTER, textColor=config_utils.colors_dictionary["TABLE_COMPANY_NAME_COLOR"], spaceAfter=0, spaceBefore=0, textTransform='uppercase'))
styles.add(ParagraphStyle(name="TableItem", fontName=font_primary, fontSize=11, alignment=TA_CENTER, textColor=config_utils.colors_dictionary["TABLE_ITEM_NAME_COLOR"], spaceAfter=0))
styles.add(ParagraphStyle(name="TableItemPrice", fontName=font_primary, fontSize=12, alignment=2, textColor=config_utils.colors_dictionary["TABLE_ITEM_PRICE_COLOR"], spaceAfter=0))
styles.add(ParagraphStyle(name="TableItemSize", fontName=font_primary, fontSize=10, alignment=0, textColor=config_utils.colors_dictionary["TABLE_ITEM_SIZE_COLOR"], spaceAfter=0))
styles.add(ParagraphStyle(name="TableItemNews", fontName=font_primary, fontSize=10, alignment=2, textColor=config_utils.colors_dictionary["TABLE_ITEM_NEWS_COLOR"], spaceAfter=0))
styles.add(ParagraphStyle(name="ParTitle1", fontName=font_primary, fontSize=30, alignment=0, textColor=config_utils.colors_dictionary["PARAGRAPH_TITLE1_COLOR"], spaceAfter=0))
styles.add(ParagraphStyle(name="ParTitle2", fontName=font_primary, fontSize=20, alignment=0, textColor=config_utils.colors_dictionary["PARAGRAPH_TITLE2_COLOR"], spaceAfter=0))
styles.add(ParagraphStyle(name="Par", fontName=font_primary, fontSize=10, alignment=0, textColor=config_utils.colors_dictionary["PARAGRAPH_COLOR"], spaceAfter=0))
#---------------------------------------------------
locale.setlocale(locale.LC_ALL, config.get("System","LOCALE"))
# Calcola larghezza disponibile
USABLE_WIDTH = PAGE_WIDTH - PAGE_MARGIN - PAGE_MARGIN
USABLE_HEIGHT = PAGE_HEIGHT - PAGE_MARGIN - PAGE_MARGIN
#-----------------------------------------------------
# oggetti per la griglia 3x3 dei prodotti
raw_1x3_counter = 0
raw_1x3_items = ["","",""]
raw_1x3 = Table([raw_1x3_items[0], raw_1x3_items[1], raw_1x3_items[2]])
story = []

#===========================================================================
# ---------- CANVAS da associare ai template di pagina ---------------------
#===========================================================================
def cover_on_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(config_utils.colors_dictionary["COVER_BACKGROUND_COLOR"])
    canvas.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, stroke=0, fill=1)
    # img_logo_path = f"./{config_utils.path_dictionary["GENERAL_IMAGES_FOLDER_PATH"]}/logo.png"
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
    canvas.drawString(PAGE_MARGIN, PAGE_HEIGHT - PAGE_MARGIN // 2, 'Sezione 2')
    canvas.drawRightString(PAGE_WIDTH - PAGE_MARGIN, PAGE_MARGIN // 2, f'Pagina {doc.page}')
    canvas.restoreState()

def category_on_page(canvas, doc):
    # semplice header e footer per le pagine di testo a tutta larghezza
    canvas.saveState()
    canvas.setFillColor(config_utils.colors_dictionary["CATEGORY_BACKGROUND_COLOR"])
    canvas.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, stroke=0, fill=1)
    canvas.setFillColor(config_utils.colors_dictionary["CATEGORY_TITLE_COLOR"])
    canvas.setFont(font_primary, 8)
    canvas.drawRightString(PAGE_WIDTH - PAGE_MARGIN, PAGE_MARGIN // 2, f'Pagina {doc.page}')
    canvas.restoreState()

def matrix_3x3_on_page(canvas, doc):
    # header/footer per la sezione a colonne
    canvas.saveState()
    canvas.setFillColor(config_utils.colors_dictionary["PRODUCTS_BACKGROUND_COLOR"])
    canvas.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, stroke=0, fill=1)
    canvas.setFont(font_primary, 8)
    #canvas.drawString(MARGIN, PAGE_HEIGHT - MARGIN // 2, 'Sezione 3')
    canvas.drawRightString(PAGE_WIDTH - PAGE_MARGIN, PAGE_MARGIN // 2, f'Pagina {doc.page}')
    canvas.restoreState()

#=======================================================
# ---------- definizione dei frame ---------------------
#=======================================================
# frame per la copertina a tutta larghezza (una colonna sola)
cover_frame = Frame(
        PAGE_MARGIN,
        PAGE_MARGIN,
        USABLE_WIDTH,
        USABLE_HEIGHT,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        id='cover_frame',
        showBoundary=0  # metti a 0 per nascondere i bordi
    )
# Frame per le pagine a tutta larghezza (una colonna sola)
body_frame = Frame(
    PAGE_MARGIN,
    PAGE_MARGIN,
    USABLE_WIDTH,
    USABLE_HEIGHT,
    leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
    id='body_frame',
    showBoundary=0  # metti a 0 per nascondere i bordi
    )
# matrix 3x3 frame a tutta larghezza (una colonna sola)
matrix_3x3_frame = Frame(
    PAGE_MARGIN,
    PAGE_MARGIN,
    USABLE_WIDTH,
    USABLE_HEIGHT,
    leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
    id='matrix_3x3',
    showBoundary=0  # metti a 0 per nascondere i bordi
    )

#=========================================================
# ---------- definizione dei template di pagina ----------
#=========================================================
# la copertina (prima pagina)
cover_page_template = PageTemplate(id='Cover', frames=[cover_frame], onPage=cover_on_page)
# corpo testo (una colonna)
body_page_template = PageTemplate(id='Body', frames=[body_frame], onPage=body_on_page)
# titolo categoria (pagina a una colonna) definita da 'category_on_page'
category_page_template = PageTemplate(id='Category', frames=[body_frame], onPage=category_on_page)
# colonne (i frame passati in lista verranno riempiti in sequenza)
matrix_3x3_page_template = PageTemplate(id='Matrix_3x3', frames=[matrix_3x3_frame], onPage=matrix_3x3_on_page)

#=========================================================
# ---------- costruzione dei documento -------------------
#=========================================================
def insert_cover(title, subtitle, footer):
    global story
    # La prima PageTemplate nella lista sara' usata per la prima pagina (Cover).
    story.append(Spacer(1, 21 * cm))
    story.append(Paragraph(f"{title}", styles['CoverTitle']))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(f"{subtitle}", styles['CoverSubtitle']))
    # story.append(Spacer(1, 1 * cm))
    # story.append(Paragraph(f"{footer}", styles['Footer']))
    logger.info("insert_cover OK")
    # Forziamo un cambio di template e una nuova pagina per la sezione successiva

def insert_body(footer):
    global story
    # Impostiamo il template Body dalla prossima pagina
    story.append(NextPageTemplate('Body'))
    story.append(PageBreak())
    story.append(Paragraph('Inizio della sezione testo', styles['ParTitle1']))
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph('Sotto titolo della sezione', styles['ParTitle2']))
    story.append(Spacer(1, 1 * cm))
    long_para = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vestibulum eu lorem eu enim congue porta a a lacus. "
    "Curabitur non justo purus. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia curae; "
    "Nam risus dolor, faucibus eget eleifend at, fermentum et risus. Etiam lacinia purus in vulputate tincidunt. "
    "Duis posuere rhoncus augue, et scelerisque nibh porta eu. Ut a nisi non odio scelerisque iaculis. "
    "Nam pretium massa at urna convallis hendrerit quis in lacus. Maecenas quis elementum mi, non tincidunt nisl. "
    "Aliquam blandit finibus dapibus.\n\n"
    )
    # aggiungiamo molti paragrafi per occupare più pagine
    for i in range(1):
        story.append(Paragraph(long_para * 6, styles['Par']))
        story.append(Spacer(1, 0.5 * cm))
    story.append(Spacer(1, 4 * cm))
    story.append(Paragraph(f"{footer}", styles['Footer']))
    logger.info("insert_body OK")

def build_TableOfContents():
    global story
    # Sommario
    story.append(NextPageTemplate('Body'))
    story.append(PageBreak())
    toc = TableOfContents()
    toc.levelStyles = [
        styles['CategoryTitle']
    ]
    story.append(Paragraph("Sommario", styles['Heading1']))
    story.append(toc)
    story.append(PageBreak())

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
        ('GRID', (0,0), (-1,-1), 0, config_utils.colors_dictionary["PRODUCTS_BACKGROUND_COLOR"])
    ]))
    story.append(KeepTogether(raw_1x3))
    raw_1x3_items = ["","",""]
    raw_1x3 = Table([[raw_1x3_items[0], raw_1x3_items[1], raw_1x3_items[2]]],
                    colWidths=[USABLE_WIDTH/3, USABLE_WIDTH/3, USABLE_WIDTH/3],
                    rowHeights=[USABLE_HEIGHT/3])
    raw_1x3_counter = 0

# metodo che costruisce il file PDF
# i parametri:
# file: Path del file del foglio excel da processare
# brk: booleano che determina se inserire o meno un salto pagina tra le aziende
def build_pdf(file_path, folder_path, brk: bool, title, subtitle, footer):
    global raw_1x3_counter
    #
    logger.info("Init 'build_pdf'...")
    # file di output 
    formatted_datetime =  datetime.datetime.now().strftime("%Y%m%d_%H%M%S") # Formato Giorno/Mese/Anno
    pdf_file_name = str(Path(folder_path) / f"{formatted_datetime}_Catalog.pdf")
    #
    doc = BaseDocTemplate(pdf_file_name, pagesize=A4, leftMargin=PAGE_MARGIN, rightMargin=PAGE_MARGIN, topMargin=PAGE_MARGIN, bottomMargin=PAGE_MARGIN, title=None, author=None)
    doc.addPageTemplates([cover_page_template, body_page_template, category_page_template, matrix_3x3_page_template])
    #
    insert_cover(title, subtitle, footer) 
    #
    insert_body(footer)
    # leggo il file:
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        logger.error("FILE EXCEL ERROR!! ", exc_info=True)
        sys.exit
    #
    previous_category = "" # la variabile che mi permette di capire se c'e' un cambio di categoria in modo da inserire una pagina con il titolo
    previous_company = "" # la variabile che mi permette di capire se c'e' un cambio di azienda in modo da inserire un titolo
    TABLE_GAP = 0.3 * cm
    #
    for _, r in df.iterrows():     # scorro le righe nel file
        # verifico che non ci siano campi nullli o non validi:
        if (r[XLS_CATEGORY] == "" or pd.isna(r[XLS_CATEGORY])):
            logger.warning(f"{r[XLS_ITEM]} - XLS_CATEGORY not defined")
            r[XLS_CATEGORY] = "--------"
        if (r[XLS_COMPANY] == "" or pd.isna(r[XLS_COMPANY])):
            logger.warning(f"{r[XLS_ITEM]} - XLS_COMPANY not defined")
            r[XLS_COMPANY] = "--------"
        try:
            formatted_price=f"€ {float(r[XLS_PRICE])}"
        except:
            formatted_price = 0
            logger.warning(f"{r[XLS_ITEM]} - XLS_PRICE not defined")
        # -----------------------------------------------  
        # ---------- verifico per inserire la pagina del titolo della categoria
        if previous_category != r[XLS_CATEGORY]:
            if raw_1x3_items[0] != "": 
                flush_1x3_row() # se ho prodotti residui nella riga, li pubblico 
            #
            story.append(NextPageTemplate('Category'))
            story.append(PageBreak())
            previous_category = r[XLS_CATEGORY]
            previous_company=""
            logger.info(f"Category: {r[XLS_CATEGORY]}")
            story.append(Spacer(1, 5 * cm))
            story.append(Paragraph(r[XLS_CATEGORY], styles['CategoryTitle']))
            story.append(NextPageTemplate('Matrix_3x3'))
            if brk == False:
                story.append(PageBreak())
        # -----------------------------------------------  
        # ---------- verifico per inserire il titolo del produttore
        if brk == True:
            if previous_company != r[XLS_COMPANY]:
                if raw_1x3_items[0] != "": 
                    flush_1x3_row() # se ho prodotti residui nella riga, li pubblico
                #
                story.append(PageBreak())
                previous_company = r[XLS_COMPANY]
                logger.info(f"     Company: {r[XLS_COMPANY]}")
                story.append(Paragraph(r[XLS_COMPANY], styles['CompanyTitle']))
                story.append(Spacer(1, 6*cm))
        else:
            if previous_company != r[XLS_COMPANY]:
                if raw_1x3_items[0] != "": 
                    flush_1x3_row() # se ho prodotti residui nella riga, li pubblico
                #
                previous_company = r[XLS_COMPANY]
                logger.info(f"     Company: {r[XLS_COMPANY]}")

        # ------------------------------------------------------  
        # --------- Leggo le informazioni del singolo prodotto
        IMAGE_SIZE = 4.4 * cm
        try:
            img_file_path = f"./{config_utils.path_dictionary["PRODUCTS_IMAGES_FOLDER_PATH"]}/{r[XLS_COLUMN_IMG]}.png"
            if os.path.exists(img_file_path):
                img = Image(img_file_path, IMAGE_SIZE, IMAGE_SIZE)
            else:        
                img_file_path = f"./tmp/{r[XLS_COLUMN_IMG]}.png"
                logger.warning(f"Product image not founded! Build new file... {img_file_path}")
                generate_image(800, 20, img_file_path)
                img = Image(img_file_path, IMAGE_SIZE, IMAGE_SIZE)
        except:
            logger.error("Product image not founded! ", exc_info=True)

        
        formatted_company = f"<b><i>{r[XLS_COMPANY]}</i></b>"
        formatted_item = f"<b>{r[XLS_ITEM]}</b>"
        
        formatted_size=f"{r[XLS_SIZE]}"
        info = [
            [img,""],
            [Paragraph(formatted_company, styles['TableCompanyName']),""],
            [Paragraph(formatted_item, styles['TableItem']),""],
            [Paragraph(formatted_size, styles['TableItemSize']), Paragraph(formatted_price, styles['TableItemPrice'])]
        ]
        table_item = Table(info, colWidths=[USABLE_WIDTH/6-TABLE_GAP, USABLE_WIDTH/6-TABLE_GAP], rowHeights=[None, 0.5*cm, 1.1*cm, None])
        table_item.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), config_utils.colors_dictionary["TABLE_BACKGROUND_COLOR"]),
            ("VALIGN", (0, 0), (-1,-1), "MIDDLE"),
            ('ALIGN',(0,0),(0,-1),'CENTER'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0.2 * cm),
            ('TOPPADDING', (0,0), (-1,-1), 0.3 * cm),
            ('RIGHTPADDING', (0,0), (-1,-1), 0.3 * cm),
            ('LEFTPADDING', (0,0), (-1,-1), 0.3 * cm),
            ('GRID', (0,0), (-1,-1), 0, config_utils.colors_dictionary["TABLE_BACKGROUND_COLOR"]),
            ('BOX', (0, 0), (-1, -1), 2, config_utils.colors_dictionary["TABLE_BORDER_COLOR"]),
            ('SPAN',(0,0),(-1,0)),
            ('SPAN',(0,1),(-1,1)),
            ('SPAN',(0,2),(-1,2)),
            ('ROUNDEDCORNERS', [10,10,10,10])
            # ('TEXTCOLOR', (0,0), (-1,-1), foreground_light),
            # ('ALIGN',(0,0),(-1,-1),'LEFT'),
            # ('ALIGN',(-1,-1),(-1,-1),'RIGHT'),
            # ('FONTNAME', (0,0), (-1, -1), 'Helvetica'),
            # ('FONTSIZE', (0,0), (-1,-1), 9),
        ]))
        logger.info(f"            {r[XLS_CATEGORY]} - {r[XLS_COMPANY]} - {r[XLS_ITEM]} - {r[XLS_SIZE]} - OK")
        
        # inserisco una tabella più grande, che contenga la scheda
        # ed abbia una prima riga per inserire le info, tipo "NOVITà"
        numero = random.randint(1, 5)
        if numero<2:
            formatted_news = f"<b>novità!</b>"
        else:
            formatted_news = ""
        table_item_big_info = [
            [Paragraph(formatted_news, styles['TableItemNews'])],   # riga 1
            [table_item]                                            # riga 2
            ]
        table_item_big=Table(table_item_big_info, rowHeights=[0.3*cm, None])
        table_item_big.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), config_utils.colors_dictionary["PRODUCTS_BACKGROUND_COLOR"]),
            ('GRID', (0,0), (-1,-1), 0, config_utils.colors_dictionary["PRODUCTS_BACKGROUND_COLOR"]),
            ("VALIGN", (0, 0), (0,-1), "BOTTOM"),
            ("VALIGN", (0, 0), (1,-1), "TOP"),
            ('ALIGN',(0,0),(-1,-1),'CENTER'),
            ("VALIGN", (0, 0), (-1,-1), "MIDDLE")
        ]))

        raw_1x3_items[raw_1x3_counter] = table_item_big


        #raw_1x3_items[raw_1x3_counter] = table_item
        raw_1x3_counter = raw_1x3_counter + 1
        if raw_1x3_counter == 3: flush_1x3_row()
    logger.info(f"Read all items in XLSX file")
    
    try:
        doc.build(story)
        logger.info(f"******* END OK --> '{pdf_file_name}' created ")
    except:
        logger.error("", exc_info=True)
        sys.exit()
    
    