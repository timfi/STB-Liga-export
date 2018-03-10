# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException
from contextlib import contextmanager
from bs4 import BeautifulSoup
from time import sleep
import pandas as pd
import lxml

__all__ = [
    'write_html_to_file',
    'get_ranking_data',
    'get_team_data',
]

urls = {
    'Tabellen': 'https://kutu.stb-liga.de/njs/#/?view=Tabellen',
    'Mannschaft': 'https://kutu.stb-liga.de/njs/#/?view=Mannschaft&filter=',
    'Mannschaft_SVB': 'https://kutu.stb-liga.de/njs/#/?view=Mannschaft&filter=68',
    'Begegnung1': 'https://kutu.stb-liga.de/njs/#/?view=Begegnung&filter=1949',
}

class page_has_loaded(object):
    '''An expectation for checking if the js on the page has already loaded the data.'''
    def __init__(self):
        super(page_has_loaded, self).__init__()

    def __call__(self, driver):
        element = driver.find_element_by_tag_name('section')
        children = element.find_elements_by_css_selector("*")
        try:
            if children[0].get_attribute('class') == "tooltip":
                return False
        except StaleElementReferenceException as e:
            pass
        except:
            return False
        return len(children) > 0


@contextmanager
def start_webdriver(*, maximize=False, hide=False):
    '''A contextmanager for the selenium webdriver

    hide - boolean the hide the webdriver
    maximize - boolean the maximize the webdriver
    '''
    selbrowser = webdriver.Firefox()
    if maximize:
        selbrowser.maximize_window()
    elif hide:
        selbrowser.set_window_position(-30000, 0)
    yield selbrowser
    selbrowser.quit()

def extract_soup(url, *, wait_timer=60, hide=True, maximize=False):
    '''A method to extract the html of a page, that waits for the js to load the data before extracting.

    url - the url to get the data from
    wait_timer - how long the driver should wait for at maximum
    hide - boolean the hide the browser
    maximize - boolean the maximize the browser
    '''
    with start_webdriver(hide=hide, maximize=maximize) as seldriver:
        seldriver.get(url)
        try:
            WebDriverWait(seldriver, wait_timer).until(page_has_loaded())
        except:
            raise Exception('Couldn\'t load page')
        return retrieve_html(seldriver)

def write_html_to_file(path, *, url=None, soup=None):
    '''A method to write the html of a soup or an url to a given file path

    path - the path to write to
    url - source url
    soup - source soup
    [url and soup are exclusive to one another]
    '''
    path = path + '.html' if not path.endswith('.html') else path
    with open(path, encoding='utf-8', mode='w+') as f:
        if soup and not url:
            f.write(soup.prettify())
        elif url and not soup:
            f.write(extract_soup(url, hide=True).prettify())
        else:
            raise RuntimeError('Either give a url or a preextracted soup, not both or nothing.')

def retrieve_html(driver):
    '''A method to retrieve the html from a running webdriver.

    driver - driver to extract html from
    '''
    return BeautifulSoup(driver.execute_script("return document.getElementsByTagName('html')[0].innerHTML"), 'html.parser')

def get_dfs_from_soup(soup):
    '''A method to transform all the tables in a given soup into pandas dataframes.

    soup - soup to transform
    '''
    return [pd.read_html(table.prettify(), flavor='html5lib')[0] for table in soup.find_all('table')]

def get_soup_from_args(key, path, *, uid=None):
    '''A method to get the soup from a given html file / predefined url.

    key - key for url in urls dict
    path - path to html file
    [key and path are exclusive to one another]
    uid - url identifier (only use when specifically needed)
    '''
    if not path:
        if uid:
            soup = extract_soup(urls[key] + str(uid))
        else:
            soup = extract_soup(urls[key])
    else:
        with open(path, encoding='utf-8', mode='r') as f:
            soup = BeautifulSoup(f, 'html.parser')
    return soup

def cleanup_team_data(team_data):
    '''A method to clean up the given team data.

    team_data - data to clean
    '''
    team_data[0] = team_data[0].iloc[:,:9]
    team_data[0].columns = ['Liga', 'Begin', 'Heim', 'Gast', 'Mannschaften', 'Punkte', 'TP', 'GP', 'Bemerkung']
    team_data[1] = team_data[1].applymap(lambda x: x.split(':')[-1])
    team_data[1].columns = ['Platz', 'Mannschaft', 'Tabellenpunkte', 'Gerätepunkte', 'Wettkämpfe']
    return team_data

def get_team_data(team_id=68, *, path=None, cleanup_func=cleanup_team_data):
    '''A method to get the given team data.

    team_id - id of the team
    path - html file path to query from [if not given the default url is queried]
    cleanup_func - function to clean up data
    '''
    soup = get_soup_from_args('Mannschaft', path, uid=team_id)
    dfs = get_dfs_from_soup(soup)
    return cleanup_func(dfs)

def cleanup_ranking_data(ranking_data):
    '''A method to clean up the given ranking data.

    ranking_data - data to clean
    '''
    # TODO cleanup_func for ranking data
    return ranking_data

def get_ranking_data(*, path=None, cleanup_func=cleanup_ranking_data):
    '''A method to get the given ranking data.

    path - html file path to query from [if not given the default url is queried]
    cleanup_func - function to clean up data
    '''
    soup = get_soup_from_args('Tabellen', path)
    dfs = get_dfs_from_soup(soup)
    return cleanup_func(dfs)


if __name__ == '__main__':
    for i, df in enumerate(get_ranking_data()):
        print(f'Table #{i} ------------------------')
        print(df)
