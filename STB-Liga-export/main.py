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
from collections import namedtuple

Team = namedtuple('Team', ['id', 'name'])
Liga = namedtuple('Liga', ['name', 'teams'])
Begegnung = namedtuple('Begegnung', ['id', 'host', 'guest'])

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

def write_html_to_file(url, path):
    if not path.endswith('.html'):
        path += '.html'
    with open(path, encoding='utf-8', mode='w+') as f:
        f.write(extract_soup(url, hide=True).prettify())


table_url = 'https://kutu.stb-liga.de/njs/#/?view=Tabellen'
listen_url = 'https://kutu.stb-liga.de/njs/#/?view=Mannschaft&filter=68'

if __name__ == '__main__':
    # soup = extract_soup(listen_url)
    with codecs.open('test.html', 'r', 'utf-8') as f:
        soup = BeautifulSoup(f)
        excel_writer = pd.ExcelWriter('test.xlsx')
        for i, table in enumerate(soup.find_all('table')):
            df = pd.read_html(table.prettify(), header=0)[0]
            print(df)
            df.to_excel(excel_writer, 'Sheet ' + str(i))
        else:
            print("done")
            excel_writer.save()
