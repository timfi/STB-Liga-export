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
from functools import partial

LARGE_FONT = (
    'Verdana',
    12
)

SMALL_FONT = (
    'Verdana',
    9
)

class AcquisitionTab(ttk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.logger = logging.getLogger('AcquisitionTab')

        entry_string = tk.StringVar()
        entry_field = tk.Entry(self, textvariable=entry_string)
        entry_field.pack()

        button1 = ttk.Button(self, text='Teamdaten laden',
                             command=lambda: controller.get_data(acquisition.MAPPINGS.TEAM, entry_string.get()))
        button1.pack()
        button2 = ttk.Button(self, text='Ranglisten laden',
                             command=lambda: controller.get_data(acquisition.MAPPINGS.RANKING))
        button2.pack()
        button3 = ttk.Button(self, text='Begegnung laden',
                             command=lambda: controller.get_data(acquisition.MAPPINGS.ENCOUNTER, entry_string.get()))
        button3.pack()

class ExportTab(ttk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        file_path = tk.StringVar()
        dir_box = tk.Entry(self, textvariable=file_path, state="readonly")
        dir_box.pack()

        button0 = ttk.Button(self, text='Datei wählen',
                             command=lambda: STB_App.ask_saveasfilename(file_path, ('Excel Datei', "*.xlsx")))
        button0.pack()
        button1 = ttk.Button(self, text='Daten als excel datei speichern',
                             command=lambda: controller.export_excel(file_path.get()))
        button1.pack()


class StartPage(ttk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.logger = logging.getLogger('StartPage')

        main_label = ttk.Label(self, text='STB Liga', font=LARGE_FONT)
        main_label.pack(pady=10, padx=10)
        sub_label = ttk.Label(self, text='Export und Verarbeitung', font=SMALL_FONT)
        sub_label.pack(pady=5, padx=5)

        main_notebook = ttk.Notebook(self)
        acquisition_tab = AcquisitionTab(self, controller)
        main_notebook.add(acquisition_tab, text="Daten laden", sticky="nsew", padding=3)
        export_tab = ExportTab(self, controller)
        main_notebook.add(export_tab, text="Daten exportieren", sticky="nsew", padding=3)
        main_notebook.pack()

class STB_App(tk.Tk):
    FRAMES = (
        StartPage,
    )
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.logger = logging.getLogger('STB_App')
        self.logger.debug('Starting driver...')
        self.driver = driver.create_webdriver()
        self.driver.get('https://kutu.stb-liga.de/')

        self.logger.debug('Starting ThreadPoolExecutor...')
        self.worker_pool = ThreadPoolExecutor(max_workers=8)

        self.data_lock = RLock()
        self.aquired_data = {}
        self.bind("<<DUMP DATA>>", lambda e: print(self.aquired_data))

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
        controller.event_generate("<<DUMP DATA>>")

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
