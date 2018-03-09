# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from selenium import webdriver
from contextlib import contextmanager
from bs4 import BeautifulSoup
from time import sleep
import pandas as pd
import json
import html5lib

table_url = 'https://kutu.stb-liga.de/njs/#/?view=Tabellen'
listen_url = 'https://kutu.stb-liga.de/njs/#/?view=Mannschaft&filter=68'

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

# write_html_to_file(table_url, 'test')

soup = extract_soup(listen_url)
for table in soup.find_all('table'):
    df = pd.read_html(table.prettify(), header=0)
    print(json.dumps(df[0].to_json(orient='index')))
    #print(table)
