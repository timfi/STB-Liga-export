# -*- coding: utf-8 -*-
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
import pandas as pd
import driver
from data import acquisition, export
import logging
import sys
import os
import asyncio
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
from threading import RLock
from collections import namedtuple
import inspect
from inspect import signature

Font = namedtuple('Font', ['tpye', 'size'])

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
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        for x in range(3):
            self.grid_rowconfigure(x, weight=1)
            self.grid_columnconfigure(x, weight=1)
        self.create_widgets(parent, controller)

def make_tab(f):
    """Function decorator to create tab-subclass defnitions from widget function."""
    cleaned_sourcecode = "\n".join(map(lambda x: " " * 8 + x, inspect.getsource(f).split('\n')[2:]))
    code = f'class {f.__name__}(Tab): \n' + \
            '    def create_widgets(self, parent, controller): \n' + \
            cleaned_sourcecode
    temp_locals = {}
    exec(code, globals(), temp_locals)
    return temp_locals[f.__name__]

@make_tab
def AcquisitionTab():
    entry_string = tk.StringVar()
    id_entry_field = tk.Entry(self, textvariable=entry_string)
    id_entry_field.grid(row=1, column=2, sticky='nsew')

    team_data_button = ttk.Button(self, text='Teamdaten laden',
                         command=lambda: controller.get_data(acquisition.MAPPINGS.TEAM, entry_string.get()))
    team_data_button.grid(row=2, column=1, sticky='nsew')
    ranking_data_button = ttk.Button(self, text='Ranglisten laden',
                         command=lambda: controller.get_data(acquisition.MAPPINGS.RANKING))
    ranking_data_button.grid(row=2, column=2, sticky='nsew')
    encounter_data_button = ttk.Button(self, text='Begegnung laden',
                         command=lambda: controller.get_data(acquisition.MAPPINGS.ENCOUNTER, entry_string.get()))
    encounter_data_button.grid(row=2, column=3, sticky='nsew')

@make_tab
def ExportTab():
    file_path = tk.StringVar()
    selected_file_label = tk.Entry(self, textvariable=file_path, state="readonly")
    selected_file_label.grid(row=1, column=1)

    file_picker_button = ttk.Button(self, text='Datei wählen',
                         command=lambda: STB_App.ask_saveasfilename(file_path, ('Excel Datei', "*.xlsx")))
    file_picker_button.grid(row=1, column=2)
    export_button = ttk.Button(self, text='Daten als excel datei speichern',
                         command=lambda: controller.export_excel(file_path.get()))
    export_button.grid(row=2, column=1)

@make_tab
def VisualisationTab():
    data_choice = tk.StringVar()
    data_option = ttk.OptionMenu(self, variable=data_choice)
    data_option.grid(row=1, column=1)

    def update_data_choices(e):
        controller.logger.debug('Updating visualisation choices')
        data_choice.set('')
        data_option['menu'].delete(0, 'end')
        with controller.data_lock:
            new_data_keys = list(controller.aquired_data.keys())
        for choice in new_data_keys:
            data_option['menu'].add_command(label=choice, command=tk._setit(data_choice, choice))

    controller.bind("<<DATA UPDATED>>", update_data_choices)

class StartPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.logger = logging.getLogger('StartPage')
        self.config(background='#006db8')

        main_label = ttk.Label(self, text='STB Liga', font=LARGE_FONT,
                               foreground='#cccccc', background='#006db8')
        main_label.grid(column=2, row=1, sticky='n', padx=5, pady=5)
        sub_label = ttk.Label(self, text='Export und Verarbeitung', font=SMALL_FONT,
                              foreground='#cccccc', background='#006db8')
        sub_label.grid(column=2, row=2, sticky="n", padx=5, pady=5)

        main_notebook = ttk.Notebook(self)
        acquisition_tab = AcquisitionTab(self, controller)
        main_notebook.add(acquisition_tab, text="Acquise", sticky="nsew", padding=3)
        export_tab = ExportTab(self, controller)
        main_notebook.add(export_tab, text="Export", sticky="nsew", padding=3)
        visualisation_tab = VisualisationTab(self, controller)
        main_notebook.add(visualisation_tab, text="Visualisierung", sticky="nsew", padding=3)
        main_notebook.grid(column=1, row=3, sticky="nwes", columnspan=3)

class STB_App(tk.Tk):
    FRAMES = (
        StartPage,
    )
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.resizable(False, False)

        self.logger = logging.getLogger('STB_App')
        self.logger.debug('Starting driver...')
        self.driver = driver.create_webdriver()
        self.driver.get('https://kutu.stb-liga.de/')

        self.logger.debug('Starting ThreadPoolExecutor...')
        self.worker_pool = ThreadPoolExecutor(max_workers=8)

        self.data_lock = RLock()
        self.aquired_data = {}

        self.protocol("WM_DELETE_WINDOW", self.__on_closing)
        self.title = "STB Liga export"

        self.container = tk.Frame(self)
        self.container.pack(side='top', fill='both', expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in STB_App.FRAMES:
            frame = F(self.container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky='nsew')
        self.show_frame(STB_App.FRAMES[0])

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

    def __on_closing(self):
        self.driver.quit()
        self.destroy()

    def export_excel(self, path):
        self.logger.debug(f'Exporting dfs to {path}')
        self.worker_pool.submit(STB_App.__export_excel, self.aquired_data, self, path)

    @staticmethod
    def __export_excel(data, controller, path):
        with controller.data_lock, export.excel_writer(path) as writer:
            for key, df in data.items():
                df.to_excel(writer, sheet_name=key)

    def get_data(self, data_type, uid=None):
        if data_type.requires_id:
            self.logger.debug(f'Getting {str(data_type.name)}_{uid}')
        else:
            self.logger.debug(f'Getting {str(data_type.name)}')
        self.worker_pool.submit(STB_App._get_data, data_type, self, uid)

    @staticmethod
    def _get_data(data_type, controller, uid=None):
        if data_type.requires_id:
            data = data_type.func(uid, driver=controller.driver)
        else:
            data = data_type.func(driver=controller.driver)

        with controller.data_lock:
            controller.aquired_data[data_type.name + f'_{uid}'] = data
        controller.event_generate("<<DATA UPDATED>>")

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

    log_streamhandler = logging.StreamHandler(sys.stderr)
    log_streamhandler.setLevel(logging.DEBUG)
    log_streamhandler.setFormatter(log_formatter)
    root_logger.addHandler(log_streamhandler)

    log_filehandler = logging.FileHandler(os.path.join(os.path.dirname(os.getcwd()), 'log/ui.log'), encoding='utf-8')
    log_filehandler.setFormatter(log_formatter)
    root_logger.addHandler(log_filehandler)

def main():
    setup_logging()
    app = STB_App()
    app.mainloop()

if __name__ == '__main__':
    main()
