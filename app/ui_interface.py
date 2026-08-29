import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from tkinter import colorchooser
from app.logger import logger
import app.config_utils as config_utils
import app.build_PDF as build_PDF
from pathlib import Path

FRAME_PADDING = 5

# REFACTOR (revisione batch E, punto 15): build_UI_and_GO() era un'unica funzione
# di ~300 righe che mescolava costruzione dei widget, gestione eventi e validazione.
# E' stata scomposta nelle funzioni _build_*_section sottostanti (una per area
# della finestra), ciascuna annidata dentro build_UI_and_GO() per continuare a
# condividere per closure le callback (update_color, choose_color, browse_folder,
# ecc.) esattamente come nella versione originale. Layout (grid/colonne/righe) e
# wiring dei callback sono preservati identici; l'unica differenza voluta e'
# l'unificazione dei due file-picker (Excel + intro TXT), prima duplicati a mano,
# in un unico helper generico basato su una lista di specifiche - sullo stesso
# schema gia' usato per il loop su path_dictionary.

def build_UI_and_GO():
     logger.info("Build UI...")

     def browse_file_generic(attr, filetypes, dialog_title, label_widget):
          selected_file = filedialog.askopenfilename(filetypes=filetypes, title=dialog_title)
          if selected_file:
               setattr(config_utils, attr, selected_file)
               label_widget.config(text=selected_file)
               logger.info(f"File selected ({attr}) - {selected_file}")

     def browse_folder(kk, ll):
          selected_folder = filedialog.askdirectory()
          if selected_folder:
               config_utils.path_dictionary[kk] = selected_folder
               ll.config(text=config_utils.path_dictionary[kk])
               logger.info(f"Output folder selected - {config_utils.path_dictionary[kk]}")

     def save_config():
          conferma = messagebox.askyesno("Confirmation", "Are you sure you want to perform this operation?")
          if conferma:
               if config_utils.save_config():
                    messagebox.showinfo("Executed", "Operation complete!")
               else:
                    messagebox.showerror("Error", "Failed to save the configuration file. Check the log for details.")

     def start_build_pdf():
          # FIX (revisione batch B, punto 7): Tkinter intercetta le eccezioni dei
          # callback dei widget (Tk.report_callback_exception) e non invoca mai il
          # sys.excepthook custom installato in Excel2PDFCatalog.py per le build
          # "windowed" - senza questo try/except, un fallimento di build_pdf() (o di
          # check_parameters()) faceva sembrare che il pulsante non facesse nulla:
          # nessun dialogo, nessuna riga in logs/app.log, nessuna riga in crash.log.
          try:
               if not check_parameters(): return

               logger.info(f"Execute with this parameters:")
               logger.info(f"--> excel_file: {config_utils.excel_file}")
               logger.info(f"--> txt_intro_file: {config_utils.txt_intro_file}")
               logger.info(f"--> title: {config_utils.title}")
               logger.info(f"--> subtitle: {config_utils.subtitle}")
               logger.info(f"--> footer: {config_utils.footer}")
               conferma = messagebox.askyesno("Confirmation", "Are you sure you want to perform this operation?")
               if conferma:
                    build_PDF.build_pdf()
                    messagebox.showinfo("Executed", "Operation complete!")
                    if not config_utils.save_config():
                         messagebox.showerror("Error", "Failed to save the configuration file. Check the log for details.")
          except Exception as e:
               logger.error("Build failed: %s", e, exc_info=True)
               messagebox.showerror("Error", f"Build failed: {e}")

     def choose_color(col, entry, lbl):
          # Apri il color chooser
          colore = colorchooser.askcolor(title="Select a color:")
          if colore[1]:  # colore[0] = (R,G,B), colore[1] = "#rrggbb"
               entry.delete(0, tk.END)
               entry.insert(0, colore[1])
               logger.info(f"Choosed color by control: {colore[1]}")
               update_color(col, entry, lbl)

     def update_color(col, entry, lbl, *args):
          # FIX (revisione batch B, punto 9): il valore veniva scritto in
          # colors_dictionary PRIMA di essere validato - un colore non valido
          # restava comunque nel dizionario (solo il campo diventava rosso),
          # rischiando di finire in config.json o di far crashare _init_styles()
          # senza alcuna traccia nel log (l'except era un 'pass' silenzioso).
          candidate = entry.get()
          try:
               lbl.config(bg=candidate)  # valida il colore prima di salvarlo
               config_utils.colors_dictionary[col] = candidate
               logger.info(f"color changing... {col}->{config_utils.colors_dictionary[col]}")
               entry.config(bg="white")
               logger.info(f"color changed")
          except tk.TclError:
               logger.warning(f"Invalid color value for {col}: {candidate!r}")
               entry.config(bg="red")

     def _build_text_fields_section(parent, grid_row):
          """Campi di testo Title/Sottotitolo/Footer, con trace_add su config_utils."""
          def update_title(*args):
               config_utils.title = entry_var_title.get()
               logger.info(f"title changed: {config_utils.title}")

          def update_subtitle(*args):
               config_utils.subtitle = entry_var_subtitle.get()
               logger.info(f"subtitle changed: {config_utils.subtitle}")

          def update_footer(*args):
               config_utils.footer = entry_var_footer.get()
               logger.info(f"footer changed: {config_utils.footer}")

          tk.Label(parent, text="Title:", anchor="e", justify=tk.LEFT).grid(row=grid_row, column=0, sticky="w")
          entry_var_title = tk.StringVar()
          entry_var_title.set(config_utils.title)
          entry_var_title.trace_add("write", update_title)
          entry_title = tk.Entry(parent, textvariable=entry_var_title, width=50)
          entry_title.grid(row=grid_row, column=1, sticky="e", padx=FRAME_PADDING)
          grid_row = grid_row + 1

          tk.Label(parent, text="Sottotitolo:", anchor="e", justify=tk.LEFT).grid(row=grid_row, column=0, sticky="w")
          entry_var_subtitle = tk.StringVar()
          entry_var_subtitle.set(config_utils.subtitle)
          entry_var_subtitle.trace_add("write", update_subtitle)
          entry_subtitle = tk.Entry(parent, textvariable=entry_var_subtitle, width=50)
          entry_subtitle.grid(row=grid_row, column=1, sticky="e", padx=FRAME_PADDING)
          grid_row = grid_row + 1

          tk.Label(parent, text="Footer:", anchor="e", justify=tk.LEFT).grid(row=grid_row, column=0, sticky="w")
          entry_var_footer = tk.StringVar()
          entry_var_footer.set(config_utils.footer)
          entry_var_footer.trace_add("write", update_footer)
          entry_footer = tk.Entry(parent, textvariable=entry_var_footer, width=50)
          entry_footer.grid(row=grid_row, column=1, sticky="e", padx=FRAME_PADDING)
          grid_row = grid_row + 1

          return grid_row

     def _build_flags_section(parent, grid_row):
          """Un Checkbutton per ogni voce di flags_dictionary."""
          grid_row = grid_row + 1
          tk.Label(parent, text="OPTIONS:").grid(row=grid_row, column=0, sticky="w", columnspan=2)
          grid_row = grid_row + 1
          chk_vars = {}
          for k, v in config_utils.flags_dictionary.items():
               chk_var = tk.BooleanVar(value=v)
               chk_vars[k] = chk_var  # <-- salvalo, altrimenti il garbage collector lo distrugge
               def update_flag(key=k, var=chk_var):
                    config_utils.flags_dictionary[key] = var.get()
                    logger.info(f"{key} changed: {config_utils.flags_dictionary[key]}")
               chk = tk.Checkbutton(
                    parent,
                    text=k.replace("_", " ").capitalize(),
                    variable=chk_var,
                    command=update_flag
               )
               chk.grid(row=grid_row, column=0, sticky="w", columnspan=2)
               grid_row = grid_row + 1
          # Separator orizzontale
          separator = ttk.Separator(parent, orient='horizontal')
          separator.grid(row=grid_row, column=0, columnspan=2, sticky="ew", padx=FRAME_PADDING, pady=FRAME_PADDING)
          return grid_row, chk_vars

     def _build_colors_section(parent):
          """Uno swatch + entry + bottone 'scegli colore' per ogni voce di colors_dictionary."""
          grid_row = 0
          for k, v in config_utils.colors_dictionary.items():
               cvs_color = tk.Canvas(parent, width=50, height=20, bg=config_utils.colors_dictionary[k], highlightthickness=1, highlightbackground="black")
               cvs_color.grid(row=grid_row, column=0, pady=0, padx=FRAME_PADDING, sticky="w")
               entry_var_color = tk.StringVar()
               entry_var_color.set(config_utils.colors_dictionary[k])
               entry_color = tk.Entry(parent, textvariable=entry_var_color, width=10, bg="white", foreground="black")
               # In Tkinter, se scrivessi:
               # command=choose_color(col, lbl, cvs) oppure choose_color(c, e, v)
               # ogni funzione verrebbe eseguita subito al momento della creazione del bottone, invece di aspettare il click.
               # Con lambda, invece, si crea una funzione che verrà chiamata solo al click.
               # "c" prenda il valore corrente di "k" al momento della creazione del bottone, "e" prenda l'entry, "v" prenda la canvas.
               # Questo è fondamentale se stai creando più controlli in un ciclo:
               # senza i parametri di default, tutti i bottoni finirebbero per usare l’ultimo valore di "k".
               entry_color.bind("<KeyRelease>", lambda event, c=k, e=entry_color, v=cvs_color: update_color(c, e, v))
               entry_color.grid(row=grid_row, column=1, sticky="e", padx=FRAME_PADDING)
               bt = tk.Button(parent, text=f"{k.replace('_',' ').capitalize()}", width=30, command=lambda c=k, e=entry_color, v=cvs_color: choose_color(c, e, v))
               bt.grid(row=grid_row, column=2, pady=0, sticky="w")
               grid_row = grid_row + 1

     def _build_file_pickers_section(parent, grid_row):
          """Selettori per il file Excel e il file TXT di intro, generati da un'unica
          lista di specifiche invece di due blocchi duplicati a mano."""
          file_picker_specs = [
               {
                    "label": "Select the XLSX file with the list of products:",
                    "button_text": "Select the file",
                    "filetypes": [("Excel files", "*.xlsx")],
                    "dialog_title": "Select the XLSX file:",
                    "attr": "excel_file",
               },
               {
                    "label": "Select the .TXT file with the INTRO:",
                    "button_text": "Select the text file",
                    "filetypes": [("Text files", "*.txt")],
                    "dialog_title": "Select the INTRO TXT file:",
                    "attr": "txt_intro_file",
               },
          ]
          for spec in file_picker_specs:
               tk.Label(parent, text=spec["label"], anchor="e", justify=tk.LEFT).grid(row=grid_row, column=0, sticky="w", columnspan=2)
               grid_row = grid_row + 1
               current_value = getattr(config_utils, spec["attr"])
               label_widget = tk.Label(parent, text=f"{current_value}", fg="blue", justify=tk.LEFT, wraplength=400)
               tk.Button(parent, width=20, text=spec["button_text"],
                         command=lambda s=spec, lw=label_widget: browse_file_generic(s["attr"], s["filetypes"], s["dialog_title"], lw)
               ).grid(row=grid_row, column=0, sticky="e", padx=FRAME_PADDING)
               label_widget.grid(row=grid_row, column=1, sticky="w")
               grid_row = grid_row + 1
          return grid_row

     # imposto la finestra
     root = tk.Tk()
     root.title(f"Excel2PDFCatalog - v{config_utils.__version__}")

     # ----------------------------------------------------------------------
     # ----------------------------------------------------------------------

     # Contenitore di sinistra
     frame_left = tk.Frame(root, padx=FRAME_PADDING, pady=FRAME_PADDING, relief="solid")
     frame_left.pack(side="left", anchor="nw", fill="both")

     # Separatore verticale
     separator = ttk.Separator(root, orient=tk.VERTICAL)
     separator.pack(side="left", anchor="nw", fill="y", pady=FRAME_PADDING, padx=0)

     # Contenitore di destra
     frame_right = tk.Frame(root, padx=FRAME_PADDING, pady=FRAME_PADDING, relief="solid")
     frame_right.pack(side="left", fill="both", anchor="nw")

     # a sinistra, contenitore etichette e opzioni
     frame_options = tk.Frame(frame_left, padx=0, pady=0, relief="solid")
     frame_options.pack(fill="x", anchor="nw")

     # a sinistra, contenitore colori
     frame_colors = tk.Frame(frame_left, padx=FRAME_PADDING, pady=FRAME_PADDING, relief="solid")
     frame_colors.pack(fill="x", anchor="center")

     # ----------------------------------------------------------------------
     # -------------- frame sn opzioni --------------------------------------
     # ----------------------------------------------------------------------
     grid_row = _build_text_fields_section(frame_options, 0)

     # ----------------------------------------------------------------------
     # -------------- checkboxes --------------------------------------------
     # ----------------------------------------------------------------------
     grid_row, chk_vars = _build_flags_section(frame_options, grid_row)

     # ----------------------------------------------------------------------
     # -------------- frame sn colori --------------------------------------
     # ----------------------------------------------------------------------
     _build_colors_section(frame_colors)

     # ----------------------------------------------------------------------
     # ---------------frame dx - file ---------------------------------------
     # ----------------------------------------------------------------------
     grid_row = 0
     grid_row = _build_file_pickers_section(frame_right, grid_row)
     # Separator orizzontale
     separator = ttk.Separator(frame_right, orient='horizontal')  # oppure 'vertical'
     separator.grid(row=grid_row, column=0, columnspan=2, sticky="ew", padx=0, pady=FRAME_PADDING)
     grid_row = grid_row + 1
     # ----------------------------------------------------------------------
     # ---------------frame dx - path ---------------------------------------
     # ----------------------------------------------------------------------
     for k, v in config_utils.path_dictionary.items():
          tk.Label(frame_right, text=f"{k.replace('_',' ').capitalize()}:", anchor="nw", justify=tk.LEFT, borderwidth=0, relief="solid").grid(row=grid_row, column=0, sticky="w", columnspan=2)
          grid_row= grid_row + 1
          folder_label = tk.Label(frame_right, text=f"{str(v)}", fg="blue", justify=tk.LEFT, wraplength=400, borderwidth=0, relief="solid")
          folder_label.grid(row=grid_row, column=1, sticky="w", padx=FRAME_PADDING)
          bt_path = tk.Button(frame_right, width=20, text="Select the folder", command=lambda kkk=k, lll=folder_label: browse_folder(kkk, lll))
          bt_path.grid(row=grid_row, column=0, sticky="w", padx=FRAME_PADDING)
          grid_row= grid_row + 1
     # Separator orizzontale
     separator = ttk.Separator(frame_right, orient='horizontal')  # oppure 'vertical'
     separator.grid(row=grid_row, column=0, columnspan=3, sticky="ew", padx=0, pady=FRAME_PADDING)
     grid_row= grid_row + 1
     # notes
     long_texts = ("NOTES:\n"
     "1. The catalogue is created following the order of the products in the Excel file.\n"
     "2. We recommend sorting the products in the Excel file at least by the 'category' and 'producer' columns.\n"
     "3. Excel cells with no content are not allowed: in this case, the PDF will not be produced.\n"
     "4. The field containing the price must be numeric.\n"
     "5. Close the Excel sheet before generating the PDF.\n"
     "6. All products images must be in <excel col image> (with extension) 1:1 format (square). Supported format: png, jpg, jpeg.\n"
     "7. The logo is a logo.png with 1:1 format (square).\n"
     "8. The intro text is a .txt file with UTF-8 encoding. Some HTML tags are supported\n"
     )
     tk.Label(frame_right, text=long_texts, justify=tk.LEFT, wraplength=480, borderwidth=0, relief="solid").grid(row=grid_row, column=0, columnspan=2, sticky="w", pady=FRAME_PADDING)
     grid_row= grid_row + 1
     # Separator orizzontale
     separator = ttk.Separator(frame_right, orient='horizontal')  # oppure 'vertical'
     separator.grid(row=grid_row, column=0, columnspan=2, sticky="ew", padx=FRAME_PADDING, pady=FRAME_PADDING)
     grid_row= grid_row + 1
     # Pulsante ESEGUI
     grid_row= grid_row + 1
     tk.Button(frame_right, width=15, height=3, text="Save config", command=save_config).grid(row=grid_row, column=0, pady=FRAME_PADDING, padx=FRAME_PADDING)
     tk.Button(frame_right, width=40, height=3, text="Save and build PDF", command=start_build_pdf).grid(row=grid_row, column=1, pady=FRAME_PADDING, padx=FRAME_PADDING)
     # ----------------------------------------------------------------------
     # ----------------------------------------------------------------------

     root.update_idletasks()   # forza il calcolo delle dimensioni in base ai widget
     root.minsize(root.winfo_width(), root.winfo_height())
     root.geometry(f"{root.winfo_width()}x{root.winfo_height()}")

     root.mainloop()

def check_parameters():
     check = True
     if not Path(config_utils.excel_file).exists():
          check = False
          # FIX (revisione batch B, punto 6): tkinter.filedialog non ha 'showerror'
          # (esiste solo su tkinter.messagebox, usato correttamente qui sotto) -
          # prima di questa fix questa riga sollevava AttributeError.
          messagebox.showerror("Error", f"Configured file not found: {config_utils.excel_file}")
     for k, v in config_utils.path_dictionary.items():
           if not Path(v).exists():
                check = False
                messagebox.showerror("Error", f"Configured path not found: {k} -> {str(v)}")
     return check
