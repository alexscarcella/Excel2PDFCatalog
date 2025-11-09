import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from tkinter import colorchooser
from app.logger import logger
import app.config_utils as config_utils
import app.build_PDF as build_PDF

def build_UI_and_GO():

     def browse_file():
          selected_file = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")], title="Select the XLSX file:")
          if selected_file:
                    config_utils.excel_file = selected_file
                    file_label.config(text=config_utils.excel_file)
                    logger.info(f"File Excel selected - {config_utils.excel_file}")

     def browse_folder(kk, ll):
          selected_folder = filedialog.askdirectory()
          if selected_folder:
               # config_utils.output_folder = selected_folder
               config_utils.path_dictionary[kk] = selected_folder
               ll.config(text=config_utils.path_dictionary[kk])
               logger.info(f"Output folder selected - {config_utils.path_dictionary[kk]}")         

     def save_config():
          conferma = messagebox.askyesno("Confirmation", "Are you sure you want to perform this operation?")
          if conferma:
               config_utils.save_config()
               messagebox.showinfo("Executed", "Operation complete!")

     def start_build_pdf():
          logger.info(f"Execute with this parameters:")
          logger.info(f"--> excel_file: {config_utils.excel_file}")
          logger.info(f"--> break_page_company: {config_utils.break_page_company}")
          logger.info(f"--> output_folder: {config_utils.output_folder}")
          logger.info(f"--> title: {config_utils.title}")
          logger.info(f"--> subtitle: {config_utils.subtitle}")
          logger.info(f"--> footer: {config_utils.footer}")
          conferma = messagebox.askyesno("Confirmation", "Are you sure you want to perform this operation?")
          if conferma:
               if config_utils.excel_file == None: 
                    logger.warning(f"No XSLX file selected!")
               else:
                    build_PDF.build_pdf(
                         config_utils.excel_file, 
                         config_utils.output_folder, 
                         config_utils.break_page_company,
                         config_utils.title,
                         config_utils.subtitle,
                         config_utils.footer
                         )
                    messagebox.showinfo("Executed", "Operation complete!")
                    config_utils.save_config()

     def update_break_page_company():
          config_utils.break_page_company = chk1.get()
          logger.info(f"break_page_company changed: {config_utils.break_page_company}")
     
     def update_title(*args):
          config_utils.title = entry_var_title.get()
          logger.info(f"title changed: {config_utils.title}")

     def update_subtitle(*args):
          config_utils.subtitle = entry_var_subtitle.get()
          logger.info(f"subtitle changed: {config_utils.subtitle}")
     
     def update_footer(*args):
          config_utils.footer = entry_var_footer.get()
          logger.info(f"footer changed: {config_utils.footer}")

     def choose_color(col, entry, lbl):
          # Apri il color chooser
          colore = colorchooser.askcolor(title="Select a color:")
          if colore[1]:  # colore[0] = (R,G,B), colore[1] = "#rrggbb"
               entry.delete(0, tk.END)
               entry.insert(0, colore[1])
               logger.info(f"Choosed color by control: {colore[1]}")
               update_color(col, entry, lbl)

     def update_color(col, entry, lbl, *args):
          try:
               config_utils.colors_dictionary[col] = entry.get()
               logger.info(f"color changing... {col}->{config_utils.colors_dictionary[col]}")
               lbl.config(bg=config_utils.colors_dictionary[col])
               entry.config(bg="white")
               logger.info(f"color changed")
          except tk.TclError:
               # Se il colore non è valido, ignora
               # logger.error(f"Label color error {col}, {colors_var_array[col]}", exc_info=True)
               entry.config(bg="red")
               pass

     # imposto la finestra
     FRAME_PADDING = 5
     root = tk.Tk()
     root.title(f"Excel2PDFCatalog - v{config_utils.__version__}")

     # ----------------------------------------------------------------------
     # ----------------------------------------------------------------------

     # Frame principale con layout orizzontale
     # main_frame = tk.Frame(root, borderwidth=1, relief="solid")
     # main_frame.pack(fill=tk.BOTH, expand=True, anchor="nw")

     # Contenitore di sinistra
     frame_left = tk.Frame(root, padx=FRAME_PADDING, pady=FRAME_PADDING, relief="solid")
     # frame_left.config(bg="red", borderwidth=2)
     frame_left.pack(side="left", anchor="nw", fill="both")

     # Separatore verticale
     separator = ttk.Separator(root, orient=tk.VERTICAL)
     separator.pack(side="left", anchor="nw", fill="y", pady=FRAME_PADDING, padx=0)

     # Contenitore di destra
     frame_right = tk.Frame(root, padx=FRAME_PADDING, pady=FRAME_PADDING, relief="solid")
     # frame_right.config(bg="yellow", borderwidth=2)
     frame_right.pack(side="left", fill="both", anchor="nw")

     # a sinistra, contenitore etichette e opzioni
     frame_options = tk.Frame(frame_left, padx=0, pady=0, relief="solid")
     # frame_left.config(bg="cyan", borderwidth=2)
     frame_options.pack(fill="x", anchor="nw")

     # a sinistra, contenitore colori
     frame_colors = tk.Frame(frame_left, padx=FRAME_PADDING, pady=FRAME_PADDING, relief="solid")
     # frame_colors.config(bg="green", borderwidth=2)
     frame_colors.pack(fill="x", anchor="center")

     # ----------------------------------------------------------------------
     # -------------- frame sn opzioni --------------------------------------
     # ----------------------------------------------------------------------
     grid_row = 0
     # Campi di input di testo - TITOLO
     tk.Label(frame_options, text="Title:", anchor="e", justify=tk.LEFT).grid(row=grid_row, column=0, sticky="w")
     entry_var_title = tk.StringVar()
     entry_var_title.set(config_utils.title)
     entry_var_title.trace_add("write", update_title)
     entry_title = tk.Entry(frame_options, textvariable=entry_var_title, width=50)
     entry_title.grid(row=grid_row, column=1, sticky="e", padx=FRAME_PADDING)
     grid_row= grid_row + 1

     # Campi di input di testo - SOTTOTITOLO
     tk.Label(frame_options, text="Sottotitolo:", anchor="e", justify=tk.LEFT).grid(row=grid_row, column=0, sticky="w")
     entry_var_subtitle = tk.StringVar()
     entry_var_subtitle.set(config_utils.subtitle)
     entry_var_subtitle.trace_add("write", update_subtitle)
     entry_subtitle = tk.Entry(frame_options, textvariable=entry_var_subtitle, width=50)
     entry_subtitle.grid(row=grid_row, column=1, sticky="e", padx=FRAME_PADDING)
     grid_row= grid_row + 1

     # Campi di input di testo - FOOTER
     tk.Label(frame_options, text="Footer:", anchor="e", justify=tk.LEFT).grid(row=grid_row, column=0, sticky="w")
     entry_var_footer = tk.StringVar()
     entry_var_footer.set(config_utils.footer)
     entry_var_footer.trace_add("write", update_footer)
     entry_footer = tk.Entry(frame_options, textvariable=entry_var_footer, width=50)
     entry_footer.grid(row=grid_row, column=1, sticky="e", padx=FRAME_PADDING)
     grid_row= grid_row + 1

     # Checkboxes
     tk.Label(frame_options, text="OPTIONS:").grid(row=grid_row, column=0, sticky="w", columnspan=2)
     grid_row= grid_row + 1
     if config_utils.break_page_company == True:
           chk1 = tk.BooleanVar(value=True)
     else:
           chk1 = tk.BooleanVar(value=False)
     chk_break_page_company = tk.Checkbutton(
          frame_options, 
          text="Change page by producer:", 
          variable=chk1, 
          command=update_break_page_company
          )
     chk_break_page_company.grid(row=grid_row, column=0, sticky="w", columnspan=2)
     grid_row= grid_row + 1
     # Separator orizzontale
     separator = ttk.Separator(frame_options, orient='horizontal')  # oppure 'vertical'
     separator.grid(row=grid_row, column=0, columnspan=2, sticky="ew", padx=FRAME_PADDING, pady=FRAME_PADDING)

     # ----------------------------------------------------------------------
     # -------------- frame sn colori --------------------------------------
     # ----------------------------------------------------------------------
     grid_row = 0
     for k, v in config_utils.colors_dictionary.items():
          cvs_color = tk.Canvas(frame_colors, width=50, height=20, bg=config_utils.colors_dictionary[k], highlightthickness=1, highlightbackground="black")
          cvs_color.grid(row=grid_row, column=0, pady=0, padx=FRAME_PADDING, sticky="w")
          entry_var_color = tk.StringVar()
          entry_var_color.set(config_utils.colors_dictionary[k])
          entry_color = tk.Entry(frame_colors, textvariable=entry_var_color, width=10, bg="white")
          # In Tkinter, se scrivessi:
          # command=choose_color(col, lbl, cvs) oppure choose_color(c, e, v)
          # ogni funzione verrebbe eseguita subito al momento della creazione del bottone, invece di aspettare il click.
          # Con lambda, invece, si crea una funzione che verrà chiamata solo al click.
          # "c" prenda il valore corrente di "k" al momento della creazione del bottone, "e" prenda l'entry, "v" prenda la canvas.
          # Questo è fondamentale se stai creando più controlli in un ciclo: 
          # senza i parametri di default, tutti i bottoni finirebbero per usare l’ultimo valore di "k".
          entry_color.bind("<KeyRelease>",lambda event, c=k, e=entry_color, v=cvs_color: update_color(c, e, v))
          entry_color.grid(row=grid_row, column=1, sticky="e", padx=FRAME_PADDING)
          bt = tk.Button(frame_colors, text=f"{k.replace("_"," ").capitalize()}", width=30, command=lambda c=k, e=entry_color, v=cvs_color: choose_color(c, e, v))
          bt.grid(row=grid_row, column=2, pady=0, sticky="w")
          grid_row= grid_row + 1

     # ----------------------------------------------------------------------
     # ---------------frame dx - file ---------------------------------------
     # ----------------------------------------------------------------------
     grid_row = 0
     # Selezione file
     tk.Label(frame_right, text="Select the XLSX file with the list of products:", anchor="e", justify=tk.LEFT).grid(row=grid_row, column=0, sticky="w", columnspan=2)
     grid_row= grid_row + 1
     tk.Button(frame_right, width=20, text="Select the file", command=browse_file).grid(row=grid_row, column=0, sticky="e", padx=FRAME_PADDING)
     file_label = tk.Label(frame_right, text=f"{config_utils.excel_file}", fg="blue", justify=tk.LEFT, wraplength=400)
     file_label.grid(row=grid_row, column=1, sticky="w")
     file_label.config(text=config_utils.excel_file)
     grid_row= grid_row + 1
     # Separator orizzontale
     separator = ttk.Separator(frame_right, orient='horizontal')  # oppure 'vertical'
     separator.grid(row=grid_row, column=0, columnspan=2, sticky="ew", padx=0, pady=FRAME_PADDING)
     grid_row= grid_row + 1
     # ----------------------------------------------------------------------
     # ---------------frame dx - path ---------------------------------------
     # ----------------------------------------------------------------------
     for k, v in config_utils.path_dictionary.items():
          tk.Label(frame_right, text=f"{k.replace("_"," ").capitalize()}:", anchor="nw", justify=tk.LEFT, borderwidth=0, relief="solid").grid(row=grid_row, column=0, sticky="w", columnspan=2)
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
     "6. All images must be in .png format.\n"
     "7. The product images are in the folder “img_products” and must be square.\n"
     "8. Other images are in the folder “img_general”.")
     tk.Label(frame_right, text=long_texts, justify=tk.LEFT, wraplength=480, borderwidth=0, relief="solid").grid(row=grid_row, column=0, columnspan=2, sticky="w", pady=FRAME_PADDING)
     grid_row= grid_row + 1
     # Separator orizzontale
     separator = ttk.Separator(frame_right, orient='horizontal')  # oppure 'vertical'
     separator.grid(row=grid_row, column=0, columnspan=2, sticky="ew", padx=FRAME_PADDING, pady=FRAME_PADDING)
     grid_row= grid_row + 1
     # Pulsante ESEGUI
     grid_row= grid_row + 1
     tk.Button(frame_right, width=15, height=3, text="Save config", command=save_config).grid(row=grid_row, column=0, pady=FRAME_PADDING, padx=FRAME_PADDING)
     tk.Button(frame_right, width=20, height=3, text="Save and build PDF", bg="green", fg="white", command=start_build_pdf).grid(row=grid_row, column=1, pady=FRAME_PADDING, padx=FRAME_PADDING)
     # ----------------------------------------------------------------------
     # ----------------------------------------------------------------------
     
     root.update_idletasks()   # forza il calcolo delle dimensioni in base ai widget
     root.minsize(root.winfo_width(), root.winfo_height())
     root.geometry(f"{root.winfo_width()}x{root.winfo_height()}")
     #root.resizable(False, False)

     root.mainloop()


