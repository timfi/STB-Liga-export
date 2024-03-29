# -*- coding: utf-8 -*-
import logging
import logging.config

import os
import sys
from enum import Enum, unique
from collections import namedtuple

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog


from .models import STBDB
# from .processing import cleanup_indexdb_dump, STB_DB_CLEANUP_MAP
from .driver import STBDriver  # , extract_index_db

project_dir = os.path.dirname(os.path.dirname(__file__))


def dfs_to_csv(fut):
    dfs = fut.result()
    for key, df in dfs.items():
        df.to_csv(os.path.join(project_dir, 'exports/' + key + '.csv'), encoding='utf-8', index=True)


Font = namedtuple('Font', ['type', 'size'])


@unique
class Fonts(Enum):
    LARGE_FONT = Font(
        'Verdana',
        12
    )
    SMALL_FONT = Font(
        'Verdana',
        9
    )


class Tab(tk.Frame):
    """Baseclass for notebook tabs"""
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.parent = parent
        for x in range(3):
            self.grid_rowconfigure(x, weight=1)
            self.grid_columnconfigure(x, weight=1)
        getattr(self, 'create_widgets')()


class ExportTab(Tab):
    def create_widgets(self):
        file_path = tk.StringVar()
        selected_file_label = tk.Entry(self, textvariable=file_path, state="readonly")
        selected_file_label.grid(row=1, column=1)

        file_picker_button = ttk.Button(self, text='Datei wählen',
                             command=lambda: STBApp.ask_saveasfilename(file_path, ('Excel Datei', "*.xlsx")))
        file_picker_button.grid(row=1, column=2)
        export_button = ttk.Button(self, text='Daten als excel datei speichern',
                        command=lambda: self.logger.debug('export button pressed <ADD ACTION>'))
        export_button.grid(row=2, column=1)


class VisualisationTab(Tab):
    def create_widgets(self):
        data_choice = tk.StringVar()
        data_option = ttk.OptionMenu(self, variable=data_choice)
        data_option.grid(row=1, column=1)


class STBApp(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.resizable(False, False)
        self.logger = logging.getLogger('STB_App')

        self.logger.info('Creating database...')
        self.db = STBDB()

        self.logger.info('Starting driver...')
        driver_path = os.path.join(project_dir, 'drivers/geckodriver.exe')
        self.driver = STBDriver(path=driver_path, headless=True)

        # self.driver.do(extract_index_db('https://kutu.stb-liga.de', STBDB.DEFAULT_INDEXDB_TABLES), dfs_to_csv)

        self.protocol("WM_DELETE_WINDOW", self.__on_closing)

        self.create_widgets()

    def create_widgets(self):
        self.title = "STB Liga export"
        self.config(background='#006db8')

        main_label = ttk.Label(self, text='STB Liga', font=Fonts.LARGE_FONT,
                               foreground='#cccccc', background='#006db8')
        main_label.grid(column=2, row=1, sticky='n', padx=5, pady=5)
        sub_label = ttk.Label(self, text='Export und Verarbeitung', font=Fonts.SMALL_FONT,
                              foreground='#cccccc', background='#006db8')
        sub_label.grid(column=2, row=2, sticky="n", padx=5, pady=5)

        main_notebook = ttk.Notebook(self)
        export_tab = ExportTab(self)
        main_notebook.add(export_tab, text="Export", sticky="nsew", padding=3)
        visualisation_tab = VisualisationTab(self)
        main_notebook.add(visualisation_tab, text="Visualisierung", sticky="nsew", padding=3)
        main_notebook.grid(column=1, row=3, sticky="nwes", columnspan=3)

    def __on_closing(self):
        self.destroy()
        self.driver.quit()

    @staticmethod
    def ask_saveasfilename(var, *file_types):
        file_name = filedialog.asksaveasfilename(filetypes=[*file_types]) if file_types else filedialog.askopenfilename()
        if file_name:
            var.set(file_name)
        else:
            var.set('keine datei')


def setup_logging():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    log_streamhandler = logging.StreamHandler(sys.stdout)
    log_streamhandler.setLevel(logging.DEBUG)
    log_streamhandler.setFormatter(log_formatter)
    root_logger.addHandler(log_streamhandler)

    log_filehandler = logging.FileHandler(os.path.join(project_dir, 'log/ui.log'), encoding='utf-8')
    log_filehandler.setFormatter(log_formatter)
    root_logger.addHandler(log_filehandler)

def main():
    setup_logging()
    app = STBApp()
    app.mainloop()
