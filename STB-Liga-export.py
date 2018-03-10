# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from selenium import webdriver
from contextlib import contextmanager
from bs4 import BeautifulSoup
from time import sleep
import pandas as pd
import json
import codecs
import lxml

__all__ = []

@contextmanager
def excel_writer(path):
    path = path + '.xlsx' if not path.endswith('.xlsx') else path
    writer = pd.ExcelWriter(path)
    yield writer
    writer.save()

@contextmanager
def start_browser(*, maximize=False, hide=False):
    selbrowser = webdriver.Firefox()
    if maximize:
        selbrowser.maximize_window()
    elif hide:
        selbrowser.set_window_position(-30000, 0)
    yield selbrowser
    selbrowser.quit()

def extract_soup(url, *, sleep_timer=5, hide=True, maximize=False):
    with start_browser(hide=hide, maximize=maximize) as selbrowser:
        selbrowser.get(url)
        sleep(sleep_timer)
        return BeautifulSoup(selbrowser.execute_script("return document.getElementsByTagName('html')[0].innerHTML"), 'html.parser')

def write_html_to_file(path, *, url=None, soup=None):
    path = path + '.html' if not path.endswith('.html') else path
    with open(path, encoding='utf-8', mode='w+') as f:
        if soup and not url:
            f.write(soup.prettify())
        elif url and not soup:
            f.write(extract_soup(url, hide=True).prettify())
        else:
            raise RuntimeError('Either give a url or a preextracted soup, not both.')

urls = {
    'Tabellen': 'https://kutu.stb-liga.de/njs/#/?view=Tabellen',
    'Mannschaft': 'https://kutu.stb-liga.de/njs/#/?view=Mannschaft&filter=68',
    'Begegnung1': 'https://kutu.stb-liga.de/njs/#/?view=Begegnung&filter=1949',
}

if __name__ == '__main__':
    #soup = extract_soup(urls['Begegnung1'], hide=False)
    with codecs.open('test.html', 'r', 'utf-8') as f:
        soup = BeautifulSoup(f, 'lxml')
        # with excel_writer('test.xlsx') as ex_writer:
        dfs = [pd.read_html(t.prettify(), header=0)[0] for t in soup.find_all('table')]
        for df in dfs:
            print(df)
                # df.to_excel(ex_writer)
    #write_html_to_file('test.html', soup=soup)
    input("DONE >> ")
