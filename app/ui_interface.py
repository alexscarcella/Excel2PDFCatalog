import platform
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from tkinter import colorchooser
from tkinter import font as tkfont
from pathlib import Path

from app.logger import logger
import app.config_utils as config_utils
import app.build_PDF as build_PDF
from app import i18n
from app.i18n import t

# REDESIGN (revisione UI): la finestra unica costruita con widget `tk.*` grezzi e'
# stata sostituita da un layout a schede `ttk.Notebook` in ordine di lavoro
# (Sorgenti -> Catalogo -> Opzioni -> Colori) con una barra inferiore sempre
# visibile (stato + Salva / Genera PDF) e un menu. L'interfaccia e' bilingue
# IT/EN, con cambio lingua a runtime (vedi app/i18n.py) e nessuna nuova
# dipendenza: solo tkinter/ttk della standard library, per non toccare la build
# PyInstaller. La generazione dei controlli a partire dai dizionari di
# config_utils (colori/percorsi/flag) e la scrittura diretta su quei globali sono
# invariate; e' cambiata solo la presentazione (raggruppamento + etichette
# tradotte, con fallback "NOME_CHIAVE" -> "Nome chiave" per chiavi non mappate).

# Scala di spaziatura, al posto dell'unico FRAME_PADDING storico.
PAD_XS, PAD_S, PAD_M, PAD_L, PAD_XL = 2, 4, 8, 16, 24

_PATH_MAXLEN = 72          # lunghezza max del percorso mostrato (poi ellissi al centro)
_BLUE = "#1a4f8b"          # colore dei percorsi selezionati


def _ellipsize_middle(text, max_len=_PATH_MAXLEN):
    """Accorcia una stringa lunga inserendo '…' al centro (utile per i percorsi)."""
    text = str(text or "")
    if len(text) <= max_len:
        return text
    keep = max_len - 1
    head = keep // 2
    tail = keep - head
    return text[:head] + "…" + text[-tail:]


class Tooltip:
    """Tooltip minimale in sola standard library. `text_provider` puo' essere una
    stringa o un callable: viene valutato all'apertura, cosi' il testo resta
    aggiornato al valore/lingua correnti."""

    def __init__(self, widget, text_provider, delay=500):
        self.widget = widget
        self.text_provider = text_provider
        self.delay = delay
        self._after_id = None
        self._tip = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _event=None):
        self._cancel()
        self._after_id = self.widget.after(self.delay, self._show)

    def _cancel(self):
        if self._after_id is not None:
            self.widget.after_cancel(self._after_id)
            self._after_id = None

    def _show(self):
        if self._tip is not None:
            return
        try:
            text = self.text_provider() if callable(self.text_provider) else str(self.text_provider)
        except Exception:
            text = ""
        if not text:
            return
        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self._tip = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tk.Label(tw, text=text, justify="left", background="#ffffe0",
                 relief="solid", borderwidth=1, padx=6, pady=3).pack()

    def _hide(self, _event=None):
        self._cancel()
        if self._tip is not None:
            self._tip.destroy()
            self._tip = None


def _init_style(root):
    """Tema + stili nominati, identici su Windows/macOS/Linux. Si forza 'clam'
    (disponibile ovunque e completamente ri-stilizzabile) per evitare l'aspetto
    datato dei widget `tk` nativi, particolarmente su macOS."""
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    # Font di base per piattaforma: riconfigurando i font nominati di Tk la
    # modifica si propaga a tutti i widget classici; per i ttk serve lo style.
    system = platform.system()
    base = tkfont.nametofont("TkDefaultFont")
    if system == "Windows":
        base.configure(family="Segoe UI", size=10)
    elif system == "Darwin":
        base.configure(family="Helvetica Neue", size=13)
    try:
        tkfont.nametofont("TkTextFont").configure(
            family=base.cget("family"), size=base.cget("size"))
    except tk.TclError:
        pass
    family, size = base.cget("family"), base.cget("size")
    style.configure(".", font=base)

    heading_font = (family, size + 3, "bold")
    hint_font = (family, max(8, size - 1))
    bold_font = (family, size, "bold")

    accent, accent_hi, accent_lo = "#2563eb", "#1d4ed8", "#93b4f5"
    grey, red, green = "#6b7280", "#c0392b", "#1e7d34"

    style.configure("Heading.TLabel", font=heading_font)
    style.configure("Hint.TLabel", font=hint_font, foreground=grey)
    style.configure("Status.TLabel", foreground=grey)
    style.configure("StatusError.TLabel", foreground=red)
    style.configure("StatusOK.TLabel", foreground=green)
    style.configure("Found.TLabel", foreground=green)
    style.configure("Missing.TLabel", foreground=red)
    style.configure("Path.TLabel", foreground=_BLUE)
    style.configure("Invalid.TEntry", fieldbackground="#ffe3e3")

    style.configure("Accent.TButton", font=bold_font, padding=(PAD_L, 10))
    style.map(
        "Accent.TButton",
        background=[("disabled", accent_lo), ("pressed", accent_hi),
                    ("active", accent_hi), ("!disabled", accent)],
        foreground=[("disabled", "#eef2ff"), ("!disabled", "#ffffff")],
    )
    style.configure("Swatch.TButton", padding=0)
    return style


def _bind_mousewheel(canvas):
    """Rotellina del mouse attiva solo mentre il puntatore e' sopra il canvas
    scrollabile (Windows/macOS usano <MouseWheel>, Linux <Button-4/5>)."""
    def _on_wheel(event):
        if event.num == 4:
            canvas.yview_scroll(-3, "units")
        elif event.num == 5:
            canvas.yview_scroll(3, "units")
        else:
            step = event.delta
            step = int(-step / 120) if platform.system() == "Windows" else -step
            canvas.yview_scroll(step, "units")

    def _enter(_event):
        canvas.bind_all("<MouseWheel>", _on_wheel)
        canvas.bind_all("<Button-4>", _on_wheel)
        canvas.bind_all("<Button-5>", _on_wheel)

    def _leave(_event):
        canvas.unbind_all("<MouseWheel>")
        canvas.unbind_all("<Button-4>")
        canvas.unbind_all("<Button-5>")

    canvas.bind("<Enter>", _enter, add="+")
    canvas.bind("<Leave>", _leave, add="+")


def build_UI_and_GO():
    logger.info("Build UI...")
    i18n.clear_hooks()

    root = tk.Tk()
    root.title(f"Excel2PDFCatalog - {config_utils.__version__}")
    _init_style(root)

    # --- stato condiviso tra i builder annidati -----------------------------
    tk_vars = []                     # riferimenti vivi ai Var (il GC li distruggerebbe)
    root._e2pc_keep = tk_vars
    color_vars = {}                  # key -> StringVar (tab Colori)
    flag_vars = {}                   # key -> BooleanVar (tab Opzioni)
    validation_refreshers = []       # callables zero-arg: riaggiornano l'icona di una riga

    # ==================================================================
    # Callback che scrivono direttamente su config_utils (come nella UI storica)
    # ==================================================================
    def browse_file_generic(attr, filetypes, dialog_title, on_done):
        selected = filedialog.askopenfilename(filetypes=filetypes, title=dialog_title)
        if selected:
            setattr(config_utils, attr, selected)
            logger.info("File selected (%s) - %s", attr, selected)
            on_done(selected)
            _refresh_validation()

    def browse_folder(key, on_done):
        selected = filedialog.askdirectory()
        if selected:
            config_utils.path_dictionary[key] = Path(selected)
            logger.info("Folder selected (%s) - %s", key, selected)
            on_done(selected)
            _refresh_validation()

    # ==================================================================
    # Validazione (sostituisce la raffica di messagebox di check_parameters)
    # ==================================================================
    def _collect_problems():
        problems = []
        if not config_utils.excel_file or not Path(config_utils.excel_file).exists():
            problems.append(("excel_file", t("problem.excel_missing")))
        for key, value in config_utils.path_dictionary.items():
            if not value or not Path(value).exists():
                problems.append((key, t("problem.path_missing", name=i18n.field_label(key))))
        return problems

    def _refresh_validation():
        problems = _collect_problems()
        for refresh in validation_refreshers:
            refresh()
        if problems:
            _set_status(t("status.problems", n=len(problems), first=problems[0][1]), "error")
        else:
            _set_status(t("status.ready"), "normal")
        return problems

    def _validate_and_report():
        problems = _refresh_validation()
        if problems:
            notebook.select(sources_tab)
        return not problems

    def _set_status(text, kind="normal"):
        style = {"normal": "Status.TLabel",
                 "error": "StatusError.TLabel",
                 "ok": "StatusOK.TLabel"}.get(kind, "Status.TLabel")
        status_label.configure(text=text, style=style)

    # ==================================================================
    # Azioni della barra inferiore / menu
    # ==================================================================
    def save_config_action():
        if not messagebox.askyesno(t("dialog.confirm.title"), t("dialog.confirm.msg")):
            return
        if config_utils.save_config():
            _set_status(t("status.saved"), "ok")
            messagebox.showinfo(t("dialog.done.title"), t("dialog.done.msg"))
        else:
            _set_status(t("status.save_failed"), "error")
            messagebox.showerror(t("dialog.error.title"), t("dialog.save_failed.msg"))

    def start_build_pdf():
        # FIX storico (revisione batch B, punto 7): Tkinter intercetta le eccezioni
        # dei callback dei widget e non invoca il sys.excepthook custom; senza
        # questo try/except un fallimento di build_pdf() non lasciava alcuna
        # traccia visibile. Il wrapper va mantenuto.
        try:
            if not _validate_and_report():
                return
            logger.info("Execute with this parameters:")
            logger.info("--> excel_file: %s", config_utils.excel_file)
            logger.info("--> txt_intro_file: %s", config_utils.txt_intro_file)
            logger.info("--> title: %s", config_utils.title)
            logger.info("--> subtitle: %s", config_utils.subtitle)
            logger.info("--> footer: %s", config_utils.footer)
            if not messagebox.askyesno(t("dialog.confirm.title"), t("dialog.confirm.msg")):
                return
            _set_status(t("status.building"), "normal")
            root.update_idletasks()
            build_PDF.build_pdf()
            _set_status(t("status.build_ok"), "ok")
            messagebox.showinfo(t("dialog.done.title"), t("dialog.done.msg"))
            if not config_utils.save_config():
                messagebox.showerror(t("dialog.error.title"), t("dialog.save_failed.msg"))
        except Exception as e:
            logger.error("Build failed: %s", e, exc_info=True)
            _set_status(t("status.build_failed", err=e), "error")
            messagebox.showerror(t("dialog.error.title"), t("dialog.build_failed.msg", err=e))

    def reset_all_defaults():
        if not messagebox.askyesno(t("dialog.reset.title"), t("dialog.reset.msg")):
            return
        for key, value in config_utils.COLOR_DEFAULTS.items():
            config_utils.colors_dictionary[key] = value
            if key in color_vars:
                color_vars[key].set(value)          # -> valida, ridipinge, riscrive
        for key, value in config_utils.FLAG_DEFAULTS.items():
            config_utils.flags_dictionary[key] = value
            if key in flag_vars:
                flag_vars[key].set(value)
        _refresh_validation()

    def set_language(code):
        i18n.set_language(code)                       # esegue tutti gli hook di ri-traduzione
        config_utils.language = i18n.get_language()
        lang_var.set(config_utils.language)
        config_utils.save_config()                    # la lingua e' una preferenza: persistila subito

    def show_notes():
        win = tk.Toplevel(root)
        win.title(t("dialog.notes.title"))
        win.transient(root)
        body = t("notes.intro") + "\n\n" + "\n".join(
            f"{i}. {t(f'notes.{i}')}" for i in range(1, 9))
        text = tk.Text(win, wrap="word", width=82, height=18, padx=PAD_M, pady=PAD_M,
                       relief="flat")
        text.insert("1.0", body)
        text.configure(state="disabled")
        text.pack(fill="both", expand=True)
        ttk.Button(win, text="OK", command=win.destroy).pack(pady=PAD_M)

    def show_about():
        messagebox.showinfo(
            t("dialog.about.title"),
            t("dialog.about.msg", version=config_utils.__version__))

    # ==================================================================
    # Costruttori di riga riutilizzabili
    # ==================================================================
    def _make_path_row(parent, row, label_getter, value_getter, on_browse):
        """Riga percorso: etichetta + [Sfoglia] + percorso (ellissi + tooltip) +
        icona ✔/✕. Ritorna una funzione di ri-traduzione."""
        lbl = ttk.Label(parent, text=label_getter())
        lbl.grid(row=row, column=0, columnspan=3, sticky="w", pady=(PAD_S, PAD_XS))

        path_var = tk.StringVar()
        tk_vars.append(path_var)
        btn = ttk.Button(parent, text=t("btn.browse"))
        btn.grid(row=row + 1, column=0, sticky="w", padx=(0, PAD_M), pady=(0, PAD_M))
        path_lbl = ttk.Label(parent, textvariable=path_var, style="Path.TLabel")
        path_lbl.grid(row=row + 1, column=1, sticky="ew")
        glyph = ttk.Label(parent)
        glyph.grid(row=row + 1, column=2, sticky="e", padx=(PAD_M, 0))
        Tooltip(path_lbl, lambda: str(value_getter() or ""))

        def render(_value=None):
            value = str(value_getter() or "")
            path_var.set(_ellipsize_middle(value) if value else t("sources.none_selected"))
            update_glyph()

        def update_glyph():
            value = value_getter()
            ok = bool(value) and Path(value).exists()
            glyph.configure(text="✔" if ok else "✕ " + t("status.missing"),
                            style="Found.TLabel" if ok else "Missing.TLabel")

        validation_refreshers.append(update_glyph)
        btn.configure(command=lambda: on_browse(render))
        render()

        def retranslate():
            lbl.configure(text=label_getter())
            btn.configure(text=t("btn.browse"))
            render()

        return retranslate

    def _make_color_row(parent, row, key):
        current = config_utils.colors_dictionary[key]
        var = tk.StringVar(value=current)
        tk_vars.append(var)
        color_vars[key] = var

        swatch = tk.Label(parent, width=4, relief="solid", bd=1, cursor="hand2")
        swatch.grid(row=row, column=0, padx=(0, PAD_M), pady=PAD_XS, sticky="w")
        entry = ttk.Entry(parent, textvariable=var, width=12)
        entry.grid(row=row, column=1, padx=(0, PAD_M), pady=PAD_XS, sticky="w")
        name_lbl = ttk.Label(parent, text=i18n.field_label(key))
        name_lbl.grid(row=row, column=2, sticky="w")
        reset_btn = ttk.Button(parent, text="↺", width=3,
                               command=lambda: var.set(config_utils.COLOR_DEFAULTS[key]))
        reset_btn.grid(row=row, column=3, padx=(PAD_M, 0), sticky="e")
        Tooltip(reset_btn, lambda: t("colors.reset_one"))

        def paint(valid):
            if valid:
                try:
                    swatch.configure(background=config_utils.colors_dictionary[key])
                    entry.configure(style="TEntry")
                    return
                except tk.TclError:
                    pass
            entry.configure(style="Invalid.TEntry")

        def on_write(*_args):
            candidate = var.get().strip()
            try:
                root.winfo_rgb(candidate)     # accetta #rgb/#rrggbb e nomi colore, come la UI storica
            except tk.TclError:
                logger.warning("Invalid color value for %s: %r", key, candidate)
                paint(False)
                return
            config_utils.colors_dictionary[key] = candidate
            logger.info("color changed %s -> %s", key, candidate)
            paint(True)

        var.trace_add("write", on_write)

        def pick(_event=None):
            try:
                initial = config_utils.colors_dictionary.get(key)
                chosen = colorchooser.askcolor(color=initial, title=t("dialog.pick_color"))
            except tk.TclError:
                chosen = colorchooser.askcolor(title=t("dialog.pick_color"))
            if chosen and chosen[1]:
                var.set(chosen[1])

        swatch.bind("<Button-1>", pick)
        paint(True)

        return lambda: name_lbl.configure(text=i18n.field_label(key))

    # ==================================================================
    # Schede
    # ==================================================================
    def _build_sources_tab(parent):
        wrap = ttk.Frame(parent, padding=PAD_L)
        wrap.pack(fill="both", expand=True)
        wrap.columnconfigure(0, weight=1)
        retrans = []

        files_lf = ttk.Labelframe(wrap, text=t("sources.files"), padding=PAD_M)
        files_lf.grid(row=0, column=0, sticky="ew", pady=(0, PAD_L))
        files_lf.columnconfigure(1, weight=1)
        retrans.append(lambda: files_lf.configure(text=t("sources.files")))

        retrans.append(_make_path_row(
            files_lf, 0,
            label_getter=lambda: t("sources.excel.label"),
            value_getter=lambda: config_utils.excel_file,
            on_browse=lambda done: browse_file_generic(
                "excel_file", [("Excel", "*.xlsx")], t("sources.excel.dialog"), done)))
        retrans.append(_make_path_row(
            files_lf, 2,
            label_getter=lambda: t("sources.intro.label"),
            value_getter=lambda: config_utils.txt_intro_file,
            on_browse=lambda done: browse_file_generic(
                "txt_intro_file", [("Text", "*.txt")], t("sources.intro.dialog"), done)))

        folders_lf = ttk.Labelframe(wrap, text=t("sources.folders"), padding=PAD_M)
        folders_lf.grid(row=1, column=0, sticky="ew")
        folders_lf.columnconfigure(1, weight=1)
        retrans.append(lambda: folders_lf.configure(text=t("sources.folders")))

        grid_row = 0
        for key in config_utils.path_dictionary:
            retrans.append(_make_path_row(
                folders_lf, grid_row,
                label_getter=(lambda k=key: i18n.field_label(k)),
                value_getter=(lambda k=key: config_utils.path_dictionary.get(k)),
                on_browse=(lambda done, k=key: browse_folder(k, done))))
            grid_row += 2

        i18n.on_language_change(lambda: [fn() for fn in retrans])

    def _build_catalog_tab(parent):
        wrap = ttk.Frame(parent, padding=PAD_L)
        wrap.pack(fill="both", expand=True)
        wrap.columnconfigure(0, weight=1)

        lf = ttk.Labelframe(wrap, text=t("catalog.texts"), padding=PAD_M)
        lf.grid(row=0, column=0, sticky="ew")
        lf.columnconfigure(1, weight=1)
        retrans = [lambda: lf.configure(text=t("catalog.texts"))]

        specs = [("title", "catalog.title", "catalog.title.hint"),
                 ("subtitle", "catalog.subtitle", "catalog.subtitle.hint"),
                 ("footer", "catalog.footer", "catalog.footer.hint")]
        grid_row = 0
        for attr, label_key, hint_key in specs:
            lbl = ttk.Label(lf, text=t(label_key))
            lbl.grid(row=grid_row, column=0, sticky="w", padx=(0, PAD_M), pady=(PAD_S, 0))
            var = tk.StringVar(value=getattr(config_utils, attr) or "")
            tk_vars.append(var)

            def _bind(a, v):
                def _update(*_args):
                    setattr(config_utils, a, v.get())
                    logger.info("%s changed: %s", a, v.get())
                v.trace_add("write", _update)

            _bind(attr, var)
            ttk.Entry(lf, textvariable=var).grid(
                row=grid_row, column=1, sticky="ew", pady=(PAD_S, 0))
            hint = ttk.Label(lf, text=t(hint_key), style="Hint.TLabel")
            hint.grid(row=grid_row + 1, column=1, sticky="w", pady=(0, PAD_M))

            def _mk_retrans(_lbl=lbl, _hint=hint, _lk=label_key, _hk=hint_key):
                def _r():
                    _lbl.configure(text=t(_lk))
                    _hint.configure(text=t(_hk))
                return _r

            retrans.append(_mk_retrans())
            grid_row += 2

        i18n.on_language_change(lambda: [fn() for fn in retrans])

    def _build_options_tab(parent):
        wrap = ttk.Frame(parent, padding=PAD_L)
        wrap.pack(fill="both", expand=True)
        wrap.columnconfigure(0, weight=1)
        retrans = []

        order = [k for k in i18n.FLAG_ORDER if k in config_utils.flags_dictionary]
        order += [k for k in config_utils.flags_dictionary if k not in order]

        grid_row = 0
        for key in order:
            var = tk.BooleanVar(value=config_utils.flags_dictionary[key])
            tk_vars.append(var)
            flag_vars[key] = var

            def _bind(k, v):
                def _update():
                    config_utils.flags_dictionary[k] = v.get()
                    logger.info("%s changed: %s", k, v.get())
                return _update

            chk = ttk.Checkbutton(wrap, text=i18n.field_label(key), variable=var,
                                  command=_bind(key, var))
            chk.grid(row=grid_row, column=0, sticky="w", pady=(PAD_M, 0))
            hint = ttk.Label(wrap, text=i18n.field_hint(key), style="Hint.TLabel")
            hint.grid(row=grid_row + 1, column=0, sticky="w", padx=(PAD_L, 0), pady=(0, PAD_S))

            def _mk_retrans(_chk=chk, _hint=hint, _key=key):
                def _r():
                    _chk.configure(text=i18n.field_label(_key))
                    _hint.configure(text=i18n.field_hint(_key))
                return _r

            retrans.append(_mk_retrans())
            grid_row += 2

        i18n.on_language_change(lambda: [fn() for fn in retrans])

    def _build_colors_tab(parent):
        outer = ttk.Frame(parent)
        outer.pack(fill="both", expand=True)
        canvas = tk.Canvas(outer, highlightthickness=0, bd=0, height=430)
        vsb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas, padding=(PAD_M, PAD_M, PAD_M, 0))
        window = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        inner.bind("<Configure>",
                   lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfigure(window, width=e.width))
        _bind_mousewheel(canvas)

        retrans = []
        groups = [(gid, list(keys)) for gid, keys in i18n.COLOR_GROUPS]
        grouped = {k for _gid, keys in groups for k in keys}
        leftover = [k for k in config_utils.colors_dictionary if k not in grouped]
        if leftover:
            groups.append(("other", leftover))

        for gid, keys in groups:
            keys = [k for k in keys if k in config_utils.colors_dictionary]
            if not keys:
                continue
            lf = ttk.Labelframe(inner, text=t("colorgroup." + gid), padding=PAD_M)
            lf.pack(fill="x", pady=(PAD_S, PAD_M))
            lf.columnconfigure(2, weight=1)
            retrans.append(lambda _lf=lf, _gid=gid: _lf.configure(text=t("colorgroup." + _gid)))
            for row, key in enumerate(keys):
                retrans.append(_make_color_row(lf, row, key))

        btn_row = ttk.Frame(inner)
        btn_row.pack(fill="x", pady=PAD_M)
        reset_btn = ttk.Button(btn_row, text=t("colors.reset_all"), command=reset_all_defaults)
        reset_btn.pack(side="right")
        retrans.append(lambda: reset_btn.configure(text=t("colors.reset_all")))

        i18n.on_language_change(lambda: [fn() for fn in retrans])

    # ==================================================================
    # Guscio: barra superiore, notebook, barra inferiore, menu
    # ==================================================================
    main = ttk.Frame(root)
    main.pack(fill="both", expand=True)

    topbar = ttk.Frame(main, padding=(PAD_L, PAD_M, PAD_L, PAD_S))
    topbar.pack(fill="x")
    subtitle_label = ttk.Label(topbar, text=t("topbar.subtitle"), style="Heading.TLabel")
    subtitle_label.pack(side="left")

    lang_var = tk.StringVar(value=i18n.get_language())
    tk_vars.append(lang_var)
    lang_box = ttk.Frame(topbar)
    lang_box.pack(side="right")
    lang_buttons = []
    for code, key in (("it", "lang.it"), ("en", "lang.en")):
        rb = ttk.Radiobutton(lang_box, text=t(key), value=code, variable=lang_var,
                             style="Toolbutton", command=lambda c=code: set_language(c))
        rb.pack(side="left")
        lang_buttons.append((rb, key))

    footer = ttk.Frame(main, padding=(PAD_L, PAD_S, PAD_L, PAD_M))
    footer.pack(fill="x", side="bottom")
    status_label = ttk.Label(footer, text=t("status.ready"), style="Status.TLabel", anchor="w")
    status_label.pack(side="left", fill="x", expand=True)
    btn_build = ttk.Button(footer, text=t("btn.build"), style="Accent.TButton",
                           command=start_build_pdf)
    btn_build.pack(side="right", padx=(PAD_M, 0))
    btn_save = ttk.Button(footer, text=t("btn.save_config"), command=save_config_action)
    btn_save.pack(side="right")

    notebook = ttk.Notebook(main)
    notebook.pack(fill="both", expand=True, padx=PAD_M, pady=PAD_M)
    sources_tab = ttk.Frame(notebook)
    catalog_tab = ttk.Frame(notebook)
    options_tab = ttk.Frame(notebook)
    colors_tab = ttk.Frame(notebook)
    notebook.add(sources_tab, text=t("tab.sources"))
    notebook.add(catalog_tab, text=t("tab.catalog"))
    notebook.add(options_tab, text=t("tab.options"))
    notebook.add(colors_tab, text=t("tab.colors"))

    _build_sources_tab(sources_tab)
    _build_catalog_tab(catalog_tab)
    _build_options_tab(options_tab)
    _build_colors_tab(colors_tab)

    def _build_menu():
        menubar = tk.Menu(root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label=t("menu.file.save"), command=save_config_action)
        file_menu.add_command(label=t("menu.file.reset"), command=reset_all_defaults)
        file_menu.add_separator()
        file_menu.add_command(label=t("menu.file.quit"), command=root.destroy)
        menubar.add_cascade(label=t("menu.file"), menu=file_menu)

        lang_menu = tk.Menu(menubar, tearoff=0)
        lang_menu.add_radiobutton(label=t("lang.it"), value="it", variable=lang_var,
                                  command=lambda: set_language("it"))
        lang_menu.add_radiobutton(label=t("lang.en"), value="en", variable=lang_var,
                                  command=lambda: set_language("en"))
        menubar.add_cascade(label=t("menu.language"), menu=lang_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label=t("menu.help.notes"), command=show_notes)
        help_menu.add_command(label=t("menu.help.about"), command=show_about)
        menubar.add_cascade(label=t("menu.help"), menu=help_menu)
        root.config(menu=menubar)

    _build_menu()
    try:  # su macOS intercetta Cmd-Q
        root.createcommand("tk::mac::Quit", root.destroy)
    except tk.TclError:
        pass

    def _retranslate_shell():
        root.title(f"Excel2PDFCatalog - {config_utils.__version__}")
        subtitle_label.configure(text=t("topbar.subtitle"))
        for rb, key in lang_buttons:
            rb.configure(text=t(key))
        notebook.tab(sources_tab, text=t("tab.sources"))
        notebook.tab(catalog_tab, text=t("tab.catalog"))
        notebook.tab(options_tab, text=t("tab.options"))
        notebook.tab(colors_tab, text=t("tab.colors"))
        btn_build.configure(text=t("btn.build"))
        btn_save.configure(text=t("btn.save_config"))
        _build_menu()
        _refresh_validation()

    i18n.on_language_change(_retranslate_shell)

    _refresh_validation()

    root.update_idletasks()
    root.minsize(900, 640)
    width = max(1000, root.winfo_reqwidth())
    height = max(680, min(root.winfo_reqheight(), 900))
    root.geometry(f"{width}x{height}")

    root.mainloop()


def check_parameters():
    """Verifica che il file Excel configurato e tutte le cartelle di
    path_dictionary esistano. Mantenuta per compatibilita' e per i chiamanti
    esterni/documentazione; la UI usa la validazione inline della barra di stato."""
    check = True
    if not Path(config_utils.excel_file).exists():
        check = False
        messagebox.showerror("Error", f"Configured file not found: {config_utils.excel_file}")
    for k, v in config_utils.path_dictionary.items():
        if not Path(v).exists():
            check = False
            messagebox.showerror("Error", f"Configured path not found: {k} -> {str(v)}")
    return check
