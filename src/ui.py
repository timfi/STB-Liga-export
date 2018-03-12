# -*- coding: utf-8 -*-
import tkinter as tk
import tkinter.ttk as ttk
import driver
from data import acquisition
import logging
import sys
import os

logger = logging.Logger(__name__)

LARGE_FONT = (
    'Verdana',
    12
)

class StartPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = ttk.Label(self, text='Hello World', font=LARGE_FONT)
        label.pack(pady=10, padx=10)
        button1 = ttk.Button(self, text='Print team_data to console', command=lambda: print(acquisition.get_team_data(driver=controller.driver)))
        button1.pack()
        button2 = ttk.Button(self, text='Print ranking_data to console', command=lambda: print(acquisition.get_ranking_data(driver=controller.driver)))
        button2.pack()
        button3 = ttk.Button(self, text='Print encounter_data to console', command=lambda: print(acquisition.get_encounter_data(driver=controller.driver)))
        button3.pack()

class STB_App(tk.Tk):
    FRAMES = (
        StartPage,
    )
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.driver = driver.create_webdriver()
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

def setup_logging():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    log_streamhandler = logging.StreamHandler(sys.stdout)
    log_streamhandler.setLevel(logging.DEBUG)
    log_streamhandler.setFormatter(log_formatter)
    root_logger.addHandler(log_streamhandler)

    log_filehandler = logging.FileHandler(os.path.join(os.path.dirname(os.getcwd()), 'log/ui.log'), encoding='utf-8')
    log_filehandler.setFormatter(log_formatter)
    root_logger.addHandler(log_filehandler)

def main():
    app = STB_App()
    app.mainloop()

if __name__ == '__main__':
    setup_logging()
    main()
