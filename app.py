"""VoiceLoom — desktop Kokoro narration workspace."""
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

from voice_catalog import VOICES, BY_ID, LANGUAGES, SAMPLES, ENGLISH_CODES, can_blend
from audio_engine import Engine, Cancelled

BASE = Path(__file__).resolve().parent
BG, PANEL, CARD, BORDER = '#101219', '#181b25', '#202431', '#303647'
TEXT, MUTED, ACCENT, GREEN = '#edf0f7', '#99a3b8', '#aa98ff', '#68dbb4'
PRESETS = {'Natural': (1., .18), 'Audiobook': (.9, .35),
           'Explainer': (1.08, .15), 'Meditation': (.75, .6), 'Fast read': (1.3, .1)}


def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(path)


class App:
    def __init__(self, root, load_model=True, data_dir=None):
        self.root = root
        self.data = Path(data_dir or BASE / 'studio_data')
        self.data.mkdir(parents=True, exist_ok=True)
        self.root.title('VoiceLoom')
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = max(760, min(1320, screen_width - 40))
        window_height = max(580, min(880, screen_height - 60))
        self.root.geometry(f'{window_width}x{window_height}+{max(0, (screen_width - window_width) // 2)}+{max(0, (screen_height - window_height) // 2)}')
        self.root.minsize(min(1100, window_width), min(820, window_height))
        self.root.configure(bg=BG)
        self._compact_layout = False
        self._footer_compact = False
        self._content_view = 'studio'
        self.events = queue.Queue()
        self.engine = Engine()
        self.ready = False
        self.busy = False
        self.closed = False
        self.cancel = threading.Event()
        self.selected = BY_ID['af_heart']
        self.current = None
        self.history = []
        self.favorites = set()
        self.voice_notes = {}
        self._restore_voice_notes()
        self.project_path = None
        self.play_started = None
        self.play_offset = 0.
        self.play_length = 0.
        self.audio = None
        self.pending_save = None
        self._style()
        self._load_branding()
        self._build()
        self.root.bind('<Configure>', self._on_resize, add='+')
        self.root.after_idle(self._responsive_layout)
        self._restore()
        self._pick(self.selected['id'])
        self.root.bind('<Control-Return>', lambda e: self._generate())
        self.root.bind('<Control-s>', lambda e: self._save_project())
        self.root.bind('<Control-o>', lambda e: self._open_project())
        self.root.protocol('WM_DELETE_WINDOW', self._close)
        self.root.after(80, self._poll)
        if load_model:
            self._load()
        else:
            self.status.configure(text='UI preview · model not loaded')

    def _load_branding(self):
        """Keep image references alive for the header and native window icon."""
        self.logo_image = None
        self.window_icon = None
        try:
            self.logo_image = tk.PhotoImage(
                master=self.root, file=str(BASE / 'assets' / 'voice-narrator-logo-64.png'))
            self.window_icon = tk.PhotoImage(
                master=self.root, file=str(BASE / 'assets' / 'voice-narrator-icon-256.png'))
            self.root.iconphoto(True, self.window_icon)
        except (tk.TclError, OSError):
            # Older project copies can still start if branding assets are absent.
            self.logo_image = None

    def _style(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.', background=PANEL, foreground=TEXT, font=('Segoe UI', 10))
        style.configure('TCombobox', fieldbackground=CARD, background=CARD,
                        foreground=TEXT, arrowcolor=MUTED, bordercolor=BORDER,
                        lightcolor=BORDER, darkcolor=BORDER, padding=6)
        style.map('TCombobox', fieldbackground=[('readonly', CARD)],
                  foreground=[('readonly', TEXT)], selectbackground=[('readonly', CARD)])
        style.configure('TNotebook', background=BG, borderwidth=0, bordercolor=PANEL,
                        lightcolor=PANEL, darkcolor=PANEL)
        style.configure('TNotebook.Tab', background=BG, foreground=MUTED, padding=(20, 9),
                        bordercolor=BG, lightcolor=BG, darkcolor=BG)
        style.map('TNotebook.Tab', background=[('selected', PANEL)], foreground=[('selected', ACCENT)])
        style.configure('TProgressbar', background=ACCENT, troughcolor=CARD, borderwidth=0,
                        bordercolor=CARD, lightcolor=ACCENT, darkcolor=ACCENT)
        style.configure('TScale', background=ACCENT, troughcolor=BORDER, bordercolor=PANEL,
                        lightcolor=ACCENT, darkcolor=ACCENT)
        style.configure('Vertical.TScrollbar', background=BORDER, troughcolor=PANEL, borderwidth=0,
                        bordercolor=PANEL, lightcolor=BORDER, darkcolor=BORDER, arrowcolor=MUTED)
        self.root.option_add('*TCombobox*Listbox.background', CARD)
        self.root.option_add('*TCombobox*Listbox.foreground', TEXT)

    def label(self, parent, text, size=10, fg=TEXT, bold=False, **kw):
        return tk.Label(parent, text=text, bg=parent.cget('bg'), fg=fg,
                        font=('Segoe UI', size, 'bold' if bold else 'normal'), **kw)

    def button(self, parent, text, command, primary=False, **kw):
        return tk.Button(parent, text=text, command=command, bg=ACCENT if primary else CARD,
                         fg=BG if primary else TEXT, activebackground='#bcafff' if primary else BORDER,
                         activeforeground=BG if primary else TEXT, disabledforeground='#626b7e',
                         relief='flat', bd=0, padx=13, pady=8, cursor='hand2',
                         font=('Segoe UI', 10, 'bold' if primary else 'normal'), **kw)

    def panel(self, parent, **kw):
        return tk.Frame(parent, bg=PANEL, highlightbackground=BORDER, highlightthickness=1, **kw)

    def combo(self, parent, variable, values, **kw):
        return ttk.Combobox(parent, textvariable=variable, values=values, state='readonly', **kw)

    def _build(self):
        header = tk.Frame(self.root, bg=BG)
        self.header = header
        header.pack(fill='x', padx=24, pady=(18, 14))
        if self.logo_image is not None:
            tk.Label(header, image=self.logo_image, bg=BG, bd=0).pack(
                side='left', padx=(0, 12))
        else:
            self.label(header, '◉', 27, ACCENT, True).pack(side='left', padx=(0, 10))
        titles = tk.Frame(header, bg=BG)
        titles.pack(side='left')
        self.label(titles, 'VoiceLoom', 21, bold=True).pack(anchor='w')
        self.label(titles, 'S T U D I O   /   Make every word resonate', 9, MUTED).pack(anchor='w')
        self.button(header, 'Save project', self._save_project).pack(side='right', padx=(6, 0))
        self.button(header, 'Open project', self._open_project).pack(side='right')
        self.label(header, f"{len(VOICES)} voices  /  {sum(v['code'] in ENGLISH_CODES for v in VOICES)} English", 10, ACCENT).pack(side='right', padx=20)
        self.library_button = self.button(header, 'Voice library →', self._toggle_library)
        body = tk.Frame(self.root, bg=BG)
        self.body = body
        body.pack(fill='both', expand=True, padx=24)
        body.pack_propagate(False)
        sidebar = self.panel(body, width=285)
        self.sidebar = sidebar
        sidebar.pack(side='left', fill='y', padx=(0, 16))
        sidebar.pack_propagate(False)
        self.label(sidebar, 'Voice library', 15, bold=True).pack(anchor='w', padx=16, pady=(16, 2))
        self.library_count = self.label(sidebar, '', 9, MUTED)
        self.library_count.pack(anchor='w', padx=16, pady=(0, 12))
        self.button(sidebar, 'Explore 47 new English voices', self._show_english, True).pack(fill='x', padx=14, pady=(0, 10))
        self.search = tk.StringVar()
        entry = tk.Entry(sidebar, textvariable=self.search, bg=CARD, fg=TEXT,
                         insertbackground=ACCENT, relief='flat', font=('Segoe UI', 11))
        entry.pack(fill='x', padx=14, ipady=9)
        self.label(sidebar, 'Search voice, reminder or channel', 8, MUTED).pack(anchor='w', padx=16, pady=(3, 9))
        self.language = tk.StringVar(value='All languages')
        self.combo(sidebar, self.language, ['All languages', 'English (all accents)'] + list(LANGUAGES.values())).pack(fill='x', padx=14)
        self.source = tk.StringVar(value='All engines')
        self.combo(sidebar, self.source, ['All engines', 'Local · Kokoro', 'Online · Edge English']).pack(fill='x', padx=14, pady=(6, 0))
        filters = tk.Frame(sidebar, bg=PANEL)
        filters.pack(fill='x', padx=14, pady=10)
        self.gender = tk.StringVar(value='All voices')
        self.combo(filters, self.gender, ['All voices', 'Female', 'Male'], width=12).pack(side='left')
        self.fav_only = tk.BooleanVar()
        tk.Checkbutton(filters, text='★ Saved', variable=self.fav_only, command=self._render,
                       bg=PANEL, fg=MUTED, selectcolor=CARD, activebackground=PANEL,
                       activeforeground=TEXT, font=('Segoe UI', 9)).pack(side='right')
        wrap = tk.Frame(sidebar, bg=PANEL)
        wrap.pack(fill='both', expand=True, padx=10, pady=(0, 8))
        self.canvas = tk.Canvas(wrap, bg=PANEL, highlightthickness=0)
        sb = ttk.Scrollbar(wrap, command=self.canvas.yview)
        sb.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)
        self.voice_frame = tk.Frame(self.canvas, bg=PANEL)
        self.voice_window = self.canvas.create_window((0, 0), window=self.voice_frame, anchor='nw')
        self.canvas.configure(yscrollcommand=sb.set)
        self.voice_frame.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfigure(self.voice_window, width=e.width))
        self.root.bind_all('<MouseWheel>', self._wheel, add='+')
        for var in (self.search, self.language, self.gender, self.source):
            var.trace_add('write', lambda *a: self._render())
        self.label(sidebar, 'LOCAL + ONLINE  ·  English collection', 8, MUTED).pack(pady=10)
        right = tk.Frame(body, bg=BG)
        self.right = right
        right.pack(side='left', fill='both', expand=True)
        right.pack_propagate(False)
        active = self.panel(right)
        active.pack(fill='x', pady=(0, 12))
        self.avatar = self.label(active, 'H', 23, ACCENT, True, width=3)
        self.avatar.pack(side='left', padx=12, pady=12)
        info = tk.Frame(active, bg=PANEL)
        info.pack(side='left', fill='x', expand=True, pady=12)
        title_row = tk.Frame(info, bg=PANEL)
        title_row.pack(anchor='w')
        self.active_name = self.label(title_row, 'Heart', 16, bold=True)
        self.active_name.pack(side='left')
        self.note_btn = self.button(title_row, '+ Add reminder', self._edit_voice_note)
        self.note_btn.configure(pady=3, padx=8, font=('Segoe UI', 9))
        self.note_btn.pack(side='left', padx=(12, 0))
        self.active_sub = self.label(info, '', 9, MUTED)
        self.active_sub.pack(anchor='w')
        self.favorite_btn = self.button(active, '☆ Save voice', self._favorite)
        self.favorite_btn.pack(side='right', padx=(4, 14))
        self.preview_btn = self.button(active, '▷ Preview', lambda: self._generate(True))
        self.preview_btn.pack(side='right')
        self._player(right)
        self.notebook = ttk.Notebook(right, height=380)
        self.notebook.pack(fill='both', expand=True)
        self.editor_tab = tk.Frame(self.notebook, bg=PANEL)
        history_tab = tk.Frame(self.notebook, bg=PANEL)
        self.notebook.add(self.editor_tab, text='Script workspace')
        self.notebook.add(history_tab, text='Recent renders')
        self._editor(self.editor_tab)
        self._history_ui(history_tab)
        footer = tk.Frame(self.root, bg=BG)
        self.footer = footer
        footer.pack(fill='x', padx=24, pady=10)
        self.status = self.label(footer, '● Loading speech engine…', 9, MUTED)
        self.status.pack(side='left')
        self.retry_btn = self.button(footer, 'Retry engine', self._load)
        self.shortcuts_label = self.label(footer, 'Ctrl+Enter  Generate     Ctrl+S  Save project', 9, MUTED)
        self.shortcuts_label.pack(side='right')
        self.branding = tk.Frame(footer, bg=BG)
        self.branding.pack(side='right', padx=24)
        self.label(self.branding, 'Made with', 9, ACCENT).pack(side='left')
        tk.Label(self.branding, text='♥', bg=BG, fg='#ef4444',
                 font=('Segoe UI Symbol', 12)).pack(side='left', padx=3)
        self.label(self.branding, 'by Hamza', 9, ACCENT).pack(side='left')
        self.github_btn = tk.Button(
            self.branding, text='GitHub',
            command=lambda: webbrowser.open_new_tab('https://github.com/ihamxaafzal'),
            bg=CARD, fg=TEXT, activebackground=BORDER, activeforeground=TEXT,
            relief='flat', bd=0, padx=8, pady=3, cursor='hand2',
            font=('Segoe UI', 9), takefocus=True)
        self.github_btn.pack(side='left', padx=(8, 0))

    def _on_resize(self, event):
        if event.widget is self.root:
            self._responsive_layout()

    def _responsive_layout(self):
        if self.closed or not hasattr(self, 'body'):
            return
        width = self.root.winfo_width()
        if width <= 1:
            return
        compact = width < 1000
        footer_compact = width < 880
        if compact != self._compact_layout:
            self._compact_layout = compact
            self.header.pack_configure(padx=12 if compact else 24)
            self.body.pack_configure(padx=12 if compact else 24)
            self.footer.pack_configure(padx=12 if compact else 24)
            self.sidebar.pack_forget()
            self.right.pack_forget()
            if compact:
                self.library_button.pack(side='right', padx=6)
                if self._content_view == 'library':
                    self.sidebar.pack(side='left', fill='both', expand=True)
                else:
                    self.right.pack(side='left', fill='both', expand=True)
            else:
                self.library_button.pack_forget()
                self._content_view = 'studio'
                self.sidebar.configure(width=285)
                self.sidebar.pack(side='left', fill='y', padx=(0, 16))
                self.right.pack(side='left', fill='both', expand=True)
        if footer_compact != self._footer_compact:
            self._footer_compact = footer_compact
            if footer_compact:
                self.branding.pack_forget()
                self.shortcuts_label.pack_forget()
            else:
                self.shortcuts_label.pack(side='right')
                self.branding.pack(side='right', padx=24)

    def _toggle_library(self):
        if not self._compact_layout:
            return
        self._content_view = 'library' if self._content_view == 'studio' else 'studio'
        self.library_button.configure(text='Studio →' if self._content_view == 'library' else 'Voice library →')
        self.right.pack_forget()
        self.sidebar.pack_forget()
        if self._content_view == 'library':
            self.sidebar.configure(width=285)
            self.sidebar.pack(side='left', fill='both', expand=True)
        else:
            self.sidebar.configure(width=285)
            self.right.pack(side='left', fill='both', expand=True)

    def _editor(self, p):
        self.editor_canvas = tk.Canvas(p, bg=PANEL, highlightthickness=0)
        editor_scroll = ttk.Scrollbar(p, orient='vertical', command=self.editor_canvas.yview)
        self.editor_canvas.configure(yscrollcommand=editor_scroll.set)
        editor_scroll.pack(side='right', fill='y')
        self.editor_canvas.pack(side='left', fill='both', expand=True)
        editor_content = tk.Frame(self.editor_canvas, bg=PANEL)
        self.editor_window = self.editor_canvas.create_window((0, 0), window=editor_content, anchor='nw')
        editor_content.bind('<Configure>', lambda e: self.editor_canvas.configure(scrollregion=self.editor_canvas.bbox('all')))
        self.editor_canvas.bind('<Configure>', lambda e: self.editor_canvas.itemconfigure(self.editor_window, width=e.width))
        p = editor_content
        p.columnconfigure(0, weight=1)
        p.rowconfigure(1, weight=1)
        toolbar = tk.Frame(p, bg=PANEL)
        toolbar.grid(row=0, column=0, sticky='ew', padx=16, pady=(12, 8))
        self.label(toolbar, '01   Your script', 12, bold=True).pack(side='left')
        self.button(toolbar, 'Import .txt', self._import_text).pack(side='right')
        self.button(toolbar, 'Sample script', self._sample).pack(side='right', padx=5)
        textwrap = tk.Frame(p, bg=CARD)
        textwrap.grid(row=1, column=0, sticky='nsew', padx=16)
        self.txt = tk.Text(textwrap, bg=CARD, fg=TEXT, insertbackground=ACCENT,
                           selectbackground='#504275', wrap='word', undo=True, height=5,
                           relief='flat', padx=14, pady=12, font=('Segoe UI', 12), spacing1=2, spacing3=4)
        scroll = ttk.Scrollbar(textwrap, command=self.txt.yview)
        scroll.pack(side='right', fill='y')
        self.txt.configure(yscrollcommand=scroll.set)
        self.txt.pack(fill='both', expand=True)
        self.txt.insert('1.0', SAMPLES['a'])
        self.txt.bind('<<Modified>>', self._modified)
        self.stats = self.label(p, '', 9, MUTED)
        self.stats.grid(row=2, column=0, sticky='e', padx=18, pady=6)
        settings = tk.Frame(p, bg=PANEL)
        settings.grid(row=3, column=0, sticky='ew', padx=16, pady=(2, 8))
        self.label(settings, '02   Voice direction', 12, bold=True).pack(side='left')
        self.preset = tk.StringVar(value='Natural')
        preset = self.combo(settings, self.preset, list(PRESETS), width=14)
        preset.pack(side='right')
        preset.bind('<<ComboboxSelected>>', self._preset)
        knobs = tk.Frame(p, bg=PANEL)
        knobs.grid(row=4, column=0, sticky='ew', padx=16)
        self.speed = tk.DoubleVar(value=1.)
        self.volume = tk.DoubleVar(value=100.)
        self.pause = tk.DoubleVar(value=.18)
        self._slider(knobs, 'Speed', self.speed, .5, 2., '{:.2f}×')
        self._slider(knobs, 'Volume', self.volume, 0, 150, '{:.0f}%')
        self._slider(knobs, 'Passage pause', self.pause, 0, 1.5, '{:.2f}s')
        mixrow = tk.Frame(p, bg=PANEL)
        mixrow.grid(row=5, column=0, sticky='ew', padx=16, pady=(6, 2))
        self.label(mixrow, 'Blend with', 9, MUTED).pack(side='left', padx=(0, 8))
        self.blend = tk.StringVar(value='None')
        self.blend_combo = self.combo(mixrow, self.blend, ['None'], width=21)
        self.blend_combo.pack(side='left')
        self.blend_ratio = tk.DoubleVar(value=50)
        self._slider(mixrow, 'Second voice mix', self.blend_ratio, 0, 100, '{:.0f}%')
        self.normalize = tk.BooleanVar(value=True)
        tk.Checkbutton(mixrow, text='Normalize', variable=self.normalize, bg=PANEL, fg=MUTED,
                       selectcolor=CARD, activebackground=PANEL, activeforeground=TEXT).pack(side='right')
        output = tk.Frame(p, bg=PANEL)
        output.grid(row=6, column=0, sticky='ew', padx=16, pady=10)
        self.sample_rate = tk.StringVar(value='24000')
        self.channels = tk.StringVar(value='Mono')
        self.bitrate = tk.StringVar(value='192k')
        for title, var, values in [('Sample rate', self.sample_rate, ['24000', '44100', '48000']),
                                   ('Channels', self.channels, ['Mono', 'Stereo']),
                                   ('MP3 bitrate', self.bitrate, ['128k', '192k', '256k', '320k'])]:
            col = tk.Frame(output, bg=PANEL)
            col.pack(side='left', fill='x', expand=True, padx=(0, 10))
            self.label(col, title, 9, MUTED).pack(anchor='w')
            self.combo(col, var, values, width=9).pack(fill='x', pady=(3, 0))
        actions = tk.Frame(p, bg=PANEL)
        actions.grid(row=7, column=0, sticky='ew', padx=16, pady=(0, 12))
        self.gen_btn = self.button(actions, 'Generate narration  →', self._generate, True, state='disabled')
        self.gen_btn.pack(side='left', fill='x', expand=True)
        self.cancel_btn = self.button(actions, 'Cancel', self.cancel.set, state='disabled')
        self.cancel_btn.pack(side='left', padx=(8, 0))
        self.progress = ttk.Progressbar(p, mode='determinate', maximum=100)
        self.progress.grid(row=8, column=0, sticky='ew', padx=16, pady=(0, 8))
        self._stats()

    def _slider(self, parent, text, var, low, high, fmt):
        f = tk.Frame(parent, bg=PANEL)
        f.pack(side='left', fill='x', expand=True, padx=(8, 10))
        line = tk.Frame(f, bg=PANEL)
        line.pack(fill='x')
        self.label(line, text, 9, MUTED).pack(side='left')
        value = self.label(line, fmt.format(var.get()), 9, ACCENT)
        value.pack(side='right')
        ttk.Scale(f, from_=low, to=high, variable=var, orient='horizontal').pack(fill='x', pady=4)
        var.trace_add('write', lambda *a: (value.configure(text=fmt.format(var.get())), self._stats()))

    def _player(self, parent):
        p = self.panel(parent)
        p.pack(fill='x', pady=(12, 0))
        top = tk.Frame(p, bg=PANEL)
        top.pack(fill='x', padx=14, pady=(10, 0))
        self.output_label = self.label(top, 'Your audio will appear here', 10, bold=True)
        self.output_label.pack(side='left')
        self.time_label = self.label(top, '00:00 / 00:00', 9, MUTED)
        self.time_label.pack(side='right')
        self.wave = tk.Canvas(p, height=42, bg=PANEL, highlightthickness=0)
        self.wave.pack(fill='x', padx=14, pady=3)
        self.wave.bind('<Configure>', lambda e: self._draw_wave())
        self.wave.bind('<Button-1>', self._seek)
        row = tk.Frame(p, bg=PANEL)
        row.pack(fill='x', padx=14, pady=(0, 10))
        self.play_btn = self.button(row, '▶ Play', self._play, state='disabled')
        self.play_btn.pack(side='left')
        self.button(row, '■ Stop', self._stop).pack(side='left', padx=6)
        self.button(row, 'Open output folder', self._folder).pack(side='left')
        self.export_buttons = []
        for fmt in ('mp3', 'flac', 'wav'):
            btn = self.button(row, f'Export {fmt.upper()}', lambda f=fmt: self._export(f), state='disabled')
            btn.pack(side='right', padx=(5, 0))
            self.export_buttons.append(btn)

    def _history_ui(self, p):
        self.label(p, 'Recent renders', 15, bold=True).pack(anchor='w', padx=18, pady=(16, 4))
        self.label(p, 'Select a render to listen, export, or restore its script.', 10, MUTED).pack(anchor='w', padx=18)
        self.history_list = tk.Listbox(p, bg=CARD, fg=TEXT, selectbackground='#504275',
                                      relief='flat', font=('Segoe UI', 11), activestyle='none')
        self.history_list.pack(fill='both', expand=True, padx=18, pady=14)
        self.history_list.bind('<<ListboxSelect>>', self._history_pick)
        self.button(p, 'Restore selected script & settings', self._restore_render).pack(anchor='w', padx=18, pady=(0, 16))

    def _wheel(self, e):
        w = self.root.winfo_containing(e.x_root, e.y_root)
        while w:
            if w == self.voice_frame or w == self.canvas:
                self.canvas.yview_scroll(-int(e.delta/120), 'units')
                return 'break'
            if w == getattr(self, 'editor_canvas', None):
                self.editor_canvas.yview_scroll(-int(e.delta/120), 'units')
                return 'break'
            w = getattr(w, 'master', None)

    def _render(self, reset=True):
        position = self.canvas.yview()[0]
        for w in self.voice_frame.winfo_children():
            w.destroy()
        query = self.search.get().lower().strip()
        voices = [v for v in VOICES if (not query or query in (v['name']+' '+v['id']+' '+v['language']+' '+self.voice_notes.get(v['id'], '')).lower())
                  and (self.language.get() == 'All languages' or v['language'] == self.language.get()
                       or (self.language.get() == 'English (all accents)' and v['code'] in ENGLISH_CODES))
                  and (self.source.get() == 'All engines' or
                       (v['engine'] == 'edge') == self.source.get().startswith('Online'))
                  and (self.gender.get() == 'All voices' or v['gender'] == self.gender.get())
                  and (not self.fav_only.get() or v['id'] in self.favorites)]
        self.library_count.configure(text=f'{len(voices)} available  ·  Find your next narrator')
        for v in voices:
            selected = v['id'] == self.selected['id']
            bg = '#302b48' if selected else CARD
            card = tk.Frame(self.voice_frame, bg=bg, highlightbackground=ACCENT if selected else BORDER,
                            highlightthickness=1, cursor='hand2')
            card.pack(fill='x', padx=3, pady=4)
            heading = tk.Frame(card, bg=bg)
            heading.pack(fill='x', padx=10, pady=(7, 1))
            edit = self.button(heading, '✎', lambda vid=v['id']: self._edit_voice_note(vid))
            edit.configure(padx=5, pady=1, font=('Segoe UI', 10))
            edit.pack(side='right')
            title = self.label(heading, ('★ ' if v['id'] in self.favorites else '') + v['name'], 11,
                               ACCENT if selected else TEXT, True)
            title.configure(wraplength=185, justify='left')
            title.pack(side='left', anchor='w')
            note = self.voice_notes.get(v['id'], '')
            reminder = self.label(card, 'Channel / reminder: '+note, 9, GREEN, wraplength=218, justify='left') if note else None
            if reminder:
                reminder.pack(anchor='w', padx=12, pady=(1, 3))
            sub = self.label(card, f"{v['language']} · {v['gender']}\n{'Online · Edge' if v['engine'] == 'edge' else 'Local · Kokoro'}", 9, MUTED, justify='left')
            sub.pack(anchor='w', padx=12, pady=(0, 9))
            for w in (card, heading, title, sub) + ((reminder,) if reminder else ()):
                w.bind('<Button-1>', lambda e, vid=v['id']: self._pick(vid))
        if not voices:
            self.label(self.voice_frame, 'No matching voices.\nTry another filter.', 11, MUTED).pack(pady=30)
        self.voice_frame.update_idletasks()
        self.canvas.yview_moveto(0 if reset else position)

    def _pick(self, vid):
        self.selected = BY_ID[vid]
        v = self.selected
        self.active_name.configure(text=v['name'])
        notice = ('Online · Internet required. Script is sent to Microsoft for speech.'
                  if v['engine'] == 'edge' else 'Local · Speech is generated on this computer.')
        note = self.voice_notes.get(vid, '')
        short_note = note[:65] + ('…' if len(note) > 65 else '')
        self.active_sub.configure(text=f"{v['language']}  /  {v['gender']}  /  {v['id']}\n{notice}" +
                                  ('\nChannel / reminder: '+short_note if note else ''), justify='left')
        self.note_btn.configure(text='✎ Edit reminder' if note else '+ Add reminder')
        self.avatar.configure(text=v['name'][0])
        self.favorite_btn.configure(text='★ Saved voice' if vid in self.favorites else '☆ Save voice')
        options = ['None'] + [x['id'] for x in VOICES if can_blend(v, x)]
        self.blend_combo.configure(values=options, state='disabled' if v['engine'] == 'edge' else 'readonly')
        if self.blend.get() not in options:
            self.blend.set('None')
        self._render(False)
        self._controls()
        if self._compact_layout and self._content_view == 'library':
            self._toggle_library()

    def _restore_voice_notes(self):
        path = self.data / 'voice_notes.json'
        if not path.exists():
            return
        try:
            notes = json.loads(path.read_text(encoding='utf-8'))
            if isinstance(notes, dict):
                self.voice_notes = {vid: note for vid, note in notes.items()
                                    if vid in BY_ID and isinstance(note, str) and note.strip()}
        except (ValueError, OSError):
            pass

    def _save_voice_note(self, vid, note):
        if vid not in BY_ID:
            raise ValueError('Unknown voice.')
        note = ' '.join(note.split())
        if len(note) > 300:
            raise ValueError('Keep the reminder within 300 characters.')
        notes = dict(self.voice_notes)
        if note:
            notes[vid] = note
        else:
            notes.pop(vid, None)
        # Write first, so a disk error cannot make an unsaved note look saved.
        atomic_json(self.data / 'voice_notes.json', notes)
        self.voice_notes = notes
        self._pick(self.selected['id'])

    def _edit_voice_note(self, vid=None):
        vid = vid or self.selected['id']
        note = simpledialog.askstring('Voice reminder · '+BY_ID[vid]['name'],
            'Channel name or personal reminder (up to 300 characters).\n'
            'Example: History Shorts, YouTube main channel\n'
            'Leave blank to remove the reminder.',
            initialvalue=self.voice_notes.get(vid, ''), parent=self.root)
        if note is None:
            return
        try:
            self._save_voice_note(vid, note)
            self.status.configure(text=f"Reminder saved · {BY_ID[vid]['name']}", fg=GREEN)
        except (OSError, ValueError) as e:
            messagebox.showerror('Reminder could not be saved', str(e), parent=self.root)

    def _favorite(self):
        vid = self.selected['id']
        self.favorites.symmetric_difference_update({vid})
        self._pick(vid)
        self._persist()

    def _show_english(self):
        self.search.set('')
        self.fav_only.set(False)
        self.gender.set('All voices')
        self.language.set('English (all accents)')
        self.source.set('Online · Edge English')
        self._pick('en-US-AriaNeural')

    def _sample(self):
        self.txt.delete('1.0', 'end')
        self.txt.insert('1.0', SAMPLES[self.selected['code']])

    def _import_text(self):
        path = filedialog.askopenfilename(filetypes=[('Text files', '*.txt'), ('All files', '*.*')])
        if path:
            try:
                text = Path(path).read_text(encoding='utf-8-sig')
                self.txt.delete('1.0', 'end')
                self.txt.insert('1.0', text)
            except Exception as e:
                messagebox.showerror('Import failed', str(e))

    def _preset(self, e=None):
        speed, pause = PRESETS[self.preset.get()]
        self.speed.set(speed)
        self.pause.set(pause)

    def _stats(self):
        if not hasattr(self, 'stats'):
            return
        text = self.txt.get('1.0', 'end-1c')
        words = len(text.split())
        seconds = int(words / (150 * self.speed.get()) * 60) if hasattr(self, 'speed') else 0
        self.stats.configure(text=f'{words:,} words   ·   {len(text):,} characters   ·   ~{seconds//60}:{seconds%60:02d} estimated')

    def _modified(self, e=None):
        if not self.txt.edit_modified():
            return
        self.txt.edit_modified(False)
        self._stats()
        if self.pending_save:
            self.root.after_cancel(self.pending_save)
        self.pending_save = self.root.after(1500, self._persist)

    def _settings(self):
        return dict(speed=self.speed.get(), volume=self.volume.get(), pause=self.pause.get(),
                    normalize=self.normalize.get(), sample_rate=int(self.sample_rate.get()),
                    channels=self.channels.get(), bitrate=self.bitrate.get(),
                    blend=None if self.blend.get() == 'None' else self.blend.get(),
                    blend_ratio=self.blend_ratio.get(), preset=self.preset.get())

    def _project(self):
        return dict(version=1, text=self.txt.get('1.0', 'end-1c'), voice=self.selected['id'], settings=self._settings())

    def _apply_project(self, doc):
        # Validate before changing any widgets; project JSON is untrusted input.
        if not isinstance(doc, dict) or not isinstance(doc.get('settings', {}), dict):
            raise ValueError('Invalid project format.')
        vid = doc.get('voice', 'af_heart')
        if vid not in BY_ID or not isinstance(doc.get('text', ''), str):
            raise ValueError('Invalid project voice or script.')
        settings = doc.get('settings', {})
        numeric = {'speed': (.5, 2.), 'volume': (0, 150), 'pause': (0, 1.5), 'blend_ratio': (0, 100)}
        for key, (low, high) in numeric.items():
            val = settings.get(key, self._settings()[key])
            if isinstance(val, bool) or not isinstance(val, (int, float)) or not low <= val <= high:
                raise ValueError(f'Invalid {key} setting.')
        for key, allowed in {'sample_rate': [24000, 44100, 48000], 'channels': ['Mono', 'Stereo'],
                             'bitrate': ['128k', '192k', '256k', '320k'], 'preset': list(PRESETS)}.items():
            if key in settings and settings[key] not in allowed:
                raise ValueError(f'Invalid {key} setting.')
        blend = settings.get('blend')
        if blend and (blend not in BY_ID or not can_blend(BY_ID[vid], BY_ID[blend])):
            raise ValueError('Blend voice must be another local Kokoro voice in the same language.')
        if 'normalize' in settings and not isinstance(settings['normalize'], bool):
            raise ValueError('Invalid normalization setting.')
        self._pick(vid)
        self.txt.delete('1.0', 'end')
        self.txt.insert('1.0', doc.get('text', ''))
        for key in numeric:
            if key in settings:
                getattr(self, key).set(settings[key])
        for key in ('sample_rate', 'channels', 'bitrate', 'preset', 'normalize'):
            if key in settings:
                getattr(self, key).set(settings[key])
        self.blend.set(blend or 'None')
        self._stats()

    def _save_project(self):
        path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('Narrator project', '*.json')],
                                          initialfile=Path(self.project_path).name if self.project_path else 'narration.json')
        if path:
            try:
                atomic_json(path, self._project())
                self.project_path = path
                self.status.configure(text=f'Project saved · {Path(path).name}', fg=GREEN)
            except Exception as e:
                messagebox.showerror('Save failed', str(e))

    def _open_project(self):
        path = filedialog.askopenfilename(filetypes=[('Narrator project', '*.json')])
        if path:
            try:
                self._apply_project(json.loads(Path(path).read_text(encoding='utf-8')))
                self.project_path = path
                self.notebook.select(0)
            except Exception as e:
                messagebox.showerror('Cannot open project', str(e))

    def _persist(self):
        self.pending_save = None
        try:
            atomic_json(self.data / 'session.json', dict(project=self._project(), favorites=sorted(self.favorites), history=self.history[:50]))
        except OSError as e:
            self.status.configure(text=f'Autosave unavailable: {e}', fg=MUTED)

    def _restore(self):
        path = self.data / 'session.json'
        if not path.exists():
            return
        try:
            doc = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(doc, dict):
                raise ValueError('Invalid session format.')
            self.favorites = set(doc.get('favorites', [])) & BY_ID.keys()
            self.history = [h for h in doc.get('history', []) if isinstance(h, dict) and Path(h.get('path', '')).is_file()][:50]
            self._apply_project(doc.get('project', {}))
            self._refresh_history()
        except (ValueError, TypeError, KeyError, OSError):
            self.status.configure(text='Previous session could not be restored', fg=MUTED)

    def _load(self):
        if self.busy:
            return
        self.busy = True
        self.retry_btn.pack_forget()
        self.status.configure(text='● Loading speech engine… First run may download model files.', fg=MUTED)
        self._controls()
        def worker():
            try:
                self.engine.load()
                self.events.put(('ready', None))
            except Exception as e:
                self.events.put(('load_error', str(e)))
        threading.Thread(target=worker, daemon=True).start()

    def _controls(self):
        usable = self.ready or self.selected.get('engine') == 'edge'
        state = 'normal' if usable and not self.busy else 'disabled'
        self.gen_btn.configure(state=state, text='Rendering…' if self.busy and self.ready else 'Generate narration  →')
        self.preview_btn.configure(state=state)
        self.cancel_btn.configure(state='normal' if self.busy and usable else 'disabled')

    def _generate(self, preview=False):
        if self.busy or (not self.ready and self.selected.get('engine') != 'edge'):
            return
        text = SAMPLES[self.selected['code']] if preview else self.txt.get('1.0', 'end-1c').strip()
        if not text:
            messagebox.showwarning('Script needed', 'Add a script or use a sample to begin.')
            return
        self._stop()
        self.busy = True
        self.cancel.clear()
        settings = self._settings()
        voice = dict(self.selected)
        self.progress['value'] = 0
        self._controls()
        self.status.configure(text=f"Rendering {voice['name']} · {voice['language']}", fg=ACCENT)
        def worker():
            try:
                result = self.engine.render(text, voice, settings, self.data / 'renders', self.cancel,
                                            lambda value, msg: self.events.put(('progress', (value, msg))))
                result['preview'] = preview
                self.events.put(('done', result))
            except Cancelled:
                self.events.put(('cancelled', None))
            except Exception as e:
                self.events.put(('error', str(e)))
        threading.Thread(target=worker, daemon=True).start()

    def _poll(self):
        if self.closed:
            return
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == 'ready':
                    self.ready, self.busy = True, False
                    self.status.configure(text=f'● Engine ready · {self.engine.device_label}', fg=GREEN)
                    self._controls()
                elif kind == 'progress':
                    self.progress['value'] = value[0]*100
                    self.status.configure(text=value[1], fg=ACCENT)
                elif kind == 'done':
                    self.busy = False
                    self.progress['value'] = 100
                    self.history.insert(0, value)
                    self.history = self.history[:50]
                    self._refresh_history()
                    self._select_audio(value)
                    self._persist()
                    self.status.configure(text=f"✓ Rendered in {value['elapsed']:.1f}s · {value['duration']:.1f}s audio", fg=GREEN)
                    self._controls()
                    if value.get('preview'):
                        self._play()
                elif kind in ('error', 'load_error', 'cancelled'):
                    self.busy = False
                    self.progress['value'] = 0
                    self.status.configure(text='Render cancelled · previous audio kept' if kind == 'cancelled' else f'Error: {value}', fg='#f6a5a5')
                    self._controls()
                    if kind == 'load_error':
                        self.retry_btn.pack(side='left', padx=10)
                    if kind != 'cancelled':
                        messagebox.showerror('Engine unavailable' if kind == 'load_error' else 'Render failed',
                            str(value) + ('\n\nOnline voices need internet access. Try again or select a Local voice.'
                                          if self.selected.get('engine') == 'edge' and kind != 'load_error' else
                                          '\n\nRun setup.bat to check dependencies. Additional languages may need eSpeak NG or Misaki language extras.'))
                elif kind == 'exported':
                    self.status.configure(text=f'Export saved · {value}', fg=GREEN)
                    for b in self.export_buttons:
                        b.configure(state='normal')
                elif kind == 'export_error':
                    for b in self.export_buttons:
                        b.configure(state='normal')
                    messagebox.showerror('Export failed', value)
        except queue.Empty:
            pass
        self._tick()
        self.root.after(80, self._poll)

    def _refresh_history(self):
        self.history_list.delete(0, 'end')
        for h in self.history:
            self.history_list.insert('end', f"  {h['created']}   {h['voice']} · {h['language']}   /   {h['duration']:.1f}s" + ('   [Preview]' if h.get('preview') else ''))

    def _history_pick(self, e=None):
        sel = self.history_list.curselection()
        if sel:
            self._select_audio(self.history[sel[0]])

    def _restore_render(self):
        sel = self.history_list.curselection()
        if sel:
            h = self.history[sel[0]]
            self._apply_project(dict(text=h['text'], voice=h['voice_id'], settings=h['settings']))
            self.notebook.select(0)

    def _select_audio(self, render):
        self._stop()
        try:
            import soundfile as sf
            self.audio, self.audio_sr = sf.read(render['path'], dtype='float32')
            self.current = render
            self.play_length = len(self.audio)/self.audio_sr
            self.output_label.configure(text=f"{render['voice']}  /  {render['sample_rate']:,} Hz  /  {render['channels']}")
            self.play_btn.configure(state='normal')
            for b in self.export_buttons:
                b.configure(state='normal')
            self._draw_wave()
        except Exception as e:
            messagebox.showerror('Cannot load audio', str(e))

    def _play(self):
        if self.audio is None:
            return
        try:
            import sounddevice as sd
            if self.play_started is not None:
                self.play_offset = min(self.play_length, self.play_offset + time.monotonic()-self.play_started)
                sd.stop()
                self.play_started = None
                self.play_btn.configure(text='▶ Resume')
            else:
                if self.play_offset >= self.play_length:
                    self.play_offset = 0
                sd.play(self.audio[int(self.play_offset*self.audio_sr):], self.audio_sr)
                self.play_started = time.monotonic()
                self.play_btn.configure(text='Ⅱ Pause')
        except Exception as e:
            self.play_started = None
            self.status.configure(text=f'Playback unavailable · {e}', fg='#f6a5a5')

    def _stop(self):
        try:
            import sounddevice as sd
            sd.stop()
        except Exception:
            pass
        self.play_started = None
        self.play_offset = 0
        self.play_btn.configure(text='▶ Play')

    @staticmethod
    def _clock(seconds):
        return f'{int(seconds)//60:02d}:{int(seconds)%60:02d}'

    def _tick(self):
        position = self.play_offset
        if self.play_started is not None:
            position += time.monotonic()-self.play_started
            if position >= self.play_length:
                self._stop()
                position = 0
        self.time_label.configure(text=f'{self._clock(position)} / {self._clock(self.play_length)}')
        self.wave.delete('cursor')
        if self.play_length:
            x = position/self.play_length * self.wave.winfo_width()
            self.wave.create_line(x, 2, x, 40, fill=GREEN, width=2, tags='cursor')

    def _draw_wave(self):
        self.wave.delete('all')
        width = max(1, self.wave.winfo_width())
        if self.audio is None:
            self.wave.create_line(0, 21, width, 21, fill=BORDER)
            return
        import numpy as np
        mono = self.audio.mean(axis=1) if self.audio.ndim > 1 else self.audio
        bars = max(1, width//4)
        edges = np.linspace(0, len(mono), bars+1, dtype=int)
        for i in range(bars):
            segment = mono[edges[i]:edges[i+1]]
            peak = max(.03, float(np.max(np.abs(segment)))) if len(segment) else .03
            self.wave.create_line(i*4, 21-peak*19, i*4, 21+peak*19, fill=ACCENT, width=2)

    def _seek(self, e):
        if self.audio is None:
            return
        playing = self.play_started is not None
        self._stop()
        self.play_offset = max(0, min(self.play_length, e.x/max(1, self.wave.winfo_width())*self.play_length))
        if playing:
            self._play()

    def _folder(self):
        folder = self.data / 'renders'
        folder.mkdir(parents=True, exist_ok=True)
        os.startfile(str(folder))

    def _export(self, fmt):
        if not self.current:
            return
        ffmpeg = shutil.which('ffmpeg')
        if fmt == 'mp3' and not ffmpeg:
            messagebox.showinfo('MP3 needs FFmpeg', 'WAV and FLAC export are ready. For MP3, install FFmpeg, add it to PATH, and restart the app.')
            return
        path = filedialog.asksaveasfilename(defaultextension='.'+fmt, filetypes=[(fmt.upper()+' audio', '*.'+fmt)],
                                          initialfile=f"narration_{self.current['voice_id']}.{fmt}")
        if not path:
            return
        source = self.current['path']
        bitrate = self.bitrate.get()
        if Path(path).resolve() == Path(source).resolve():
            return
        for b in self.export_buttons:
            b.configure(state='disabled')
        def worker():
            temp = Path(path).with_name(Path(path).stem + '.exporting.' + fmt)
            try:
                if fmt == 'wav':
                    shutil.copy2(source, temp)
                elif fmt == 'flac':
                    import soundfile as sf
                    audio, sr = sf.read(source)
                    sf.write(str(temp), audio, sr, format='FLAC', subtype='PCM_16')
                else:
                    result = subprocess.run([ffmpeg, '-y', '-i', source, '-b:a', bitrate, str(temp)],
                                            capture_output=True, timeout=300,
                                            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                    if result.returncode:
                        raise RuntimeError(result.stderr.decode(errors='replace')[-1500:])
                temp.replace(path)
                self.events.put(('exported', Path(path).name))
            except Exception as e:
                temp.unlink(missing_ok=True)
                self.events.put(('export_error', str(e)))
        threading.Thread(target=worker, daemon=True).start()

    def _close(self):
        self._persist()
        self.closed = True
        self.cancel.set()
        self._stop()
        self.root.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    app = App(root, load_model='--ui-only' not in sys.argv)
    if '--english' in sys.argv:
        app._show_english()
    root.mainloop()
