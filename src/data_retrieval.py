# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException
from contextlib import contextmanager
from bs4 import BeautifulSoup
from time import sleep
import pandas as pd
import lxml
import inspect
import os
import platform

__all__ = [
    'write_html_to_file',
    'get_ranking_data',
    'get_team_data',
    'create_webdriver'
]

urls = {
    'Tabellen': 'https://kutu.stb-liga.de/njs/#/?view=Tabellen',
    'Mannschaft': 'https://kutu.stb-liga.de/njs/#/?view=Mannschaft&filter=',
    'Mannschaft_SVB': 'https://kutu.stb-liga.de/njs/#/?view=Mannschaft&filter=68',
    'Begegnung': 'https://kutu.stb-liga.de/njs/#/?view=Begegnung&filter=',
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

    <kwargs>
    hide - boolean the hide the webdriver
    maximize - boolean the maximize the webdriver
    [hide and maximize are exclusive to one another]
    '''
    driver = create_webdriver(maximize=maximize, hide=hide)
    yield driver
    driver.quit()

def create_webdriver(*, maximize=False, hide=False):
    '''A method to create a selenium webdriver

    <kwargs>
    hide - boolean the hide the webdriver
    maximize - boolean the maximize the webdriver
    [hide and maximize are exclusive to one another]
    '''
    driver = webdriver.Firefox()
    if maximize:
        driver.maximize_window()
    elif hide:
        driver.set_window_position(-30000, 0)
    return driver


def extract_soup(url, *, wait_timer=5, hide=True, maximize=False, driver=None):
    '''A method to extract the html of a page, that waits for the js to load the data before extracting.

    <args>
    url - the url to get the data from

    <kwargs>
    wait_timer - how long the driver should wait for at maximum
    hide - boolean the hide the browser
    maximize - boolean the maximize the browser
    [hide and maximize are exclusive to one another]
    driver - webdriver to use
    '''
    if not driver:
        print("using local driver")
        with start_webdriver(hide=hide, maximize=maximize) as local_driver:
            if local_driver.current_url != url:
                local_driver.get(url)
                # try:
                #     WebDriverWait(seldriver, wait_timer).until(page_has_loaded())
                # except:
                #     raise Exception('Couldn\'t load page')
                sleep(wait_timer)
            return retrieve_soup(local_driver)
    else:
        print("using foreign driver")
        if driver.current_url != url:
            driver.get(url)
            sleep(wait_timer)
        return retrieve_soup(driver)

def write_html_to_file(path, *, url=None, soup=None):
    '''A method to write the html of a soup or an url to a given file path

    <args>
    path - the path to write to

    <kwargs>
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

def retrieve_soup(driver):
    '''A method to retrieve the soup from a running webdriver.

    <args>
    driver - driver to extract html from
    '''
    return BeautifulSoup(driver.execute_script("return document.getElementsByTagName('html')[0].innerHTML"), 'html.parser')

def get_dfs_from_soup(soup):
    '''A method to transform all the tables in a given soup into pandas dataframes.

    <args>
    soup - soup to transform
    '''
    return [pd.read_html(table.prettify(), flavor='html5lib')[0] for table in soup.find_all('table')]

def get_soup_from_args(key, path, *, uid=None, driver=None, **kwargs):
    '''A method to get the soup from a given html file / predefined url.

    <args>
    key - key for url in urls dict
    path - path to html file
    [key and path are exclusive to one another]

    <kwargs>
    uid - url identifier (only use when specifically needed)
    driver - webdriver to use
    '''
    if not path:
        if uid:
            soup = extract_soup(urls[key] + str(uid), driver=driver, **kwargs)
        else:
            soup = extract_soup(urls[key], driver=driver, **kwargs)
    else:
        with open(path, encoding='utf-8', mode='r') as f:
            soup = BeautifulSoup(f, 'html.parser', **kwargs)
    return soup

def cleanup_team_data(team_encounter_data, team_ranking_data):
    '''A method to clean up the given team data.

    <args>
    team_encounter_data - encounter data to clean
    team_ranking_data - ranking data to clean
    '''
    team_encounter_data = team_encounter_data.iloc[:,:9]
    team_encounter_data.columns = ['Liga', 'Begin', 'Heim', 'Gast', 'Mannschaften', 'Punkte', 'TP', 'GP', 'Bemerkung']
    team_ranking_data = team_ranking_data.applymap(lambda x: x.split(':')[-1])
    team_ranking_data.columns = ['Platz', 'Mannschaft', 'Tabellenpunkte', 'Gerätepunkte', 'Wettkämpfe']
    return team_encounter_data, team_ranking_data

def get_team_data(team_id=68, *, path=None, cleanup_func=cleanup_team_data, driver=None):
    '''A method to get the given team data.

    <args>
    team_id - id of the team (defaults to 68)

    <kwargs>
    path - html file path to query from [if not given the default url is queried]
    cleanup_func - function to clean up data
    driver - webdriver to use
    '''
    soup = get_soup_from_args('Mannschaft', path, uid=team_id, driver=driver)
    dfs = get_dfs_from_soup(soup)
    return cleanup_func(*dfs)

def cleanup_ranking_data(*ranking_data):
    '''A method to clean up the given ranking data.

    <args>
    ranking_data - data to clean
    '''
    # TODO cleanup_func for ranking data
    return ranking_data

def get_ranking_data(*, path=None, cleanup_func=cleanup_ranking_data, driver=None):
    '''A method to get the given ranking data.

    <kwargs>
    path - html file path to query from [if not given the default url is queried]
    cleanup_func - function to clean up data
    driver - webdriver to use
    '''
    soup = get_soup_from_args('Tabellen', path, driver=driver)
    dfs = get_dfs_from_soup(soup)
    return cleanup_func(*dfs)

def cleanup_encounter_data(encounter_data):
    '''A method to clean up the given ranking data.

    <args>
    encounter_data - data to clean
    '''
    # Split table
    encounter_lteam_data = encounter_data.iloc[:,:5]
    encounter_rteam_data = encounter_data.iloc[:,6:]
    # reverse rteam table
    encounter_rteam_data = encounter_rteam_data[encounter_rteam_data.columns[::-1]]
    # Relable rTeams columns
    encounter_rteam_data.columns = [0,1,2,3,4]
    return encounter_lteam_data, encounter_rteam_data

def get_encounter_data(encounter_id=1949, *, path=None, cleanup_func=cleanup_encounter_data, driver=None):
    '''A method to get the given encounter data.

    <args>
    encounter_id - id of encounter (defaults to 1949)

    <kwargs>
    path - html file path to query from [if not given the default url is queried]
    cleanup_func - function to clean up data
    driver - webdriver to use
    '''
    # requires special treatment due to the way the html is structured
    soup = get_soup_from_args('Begegnung', path, uid=encounter_id, driver=driver)
    table = soup.find('table')
    rows = table.find_all('tr', attrs=['even desktop', 'odd desktop'])  #Find all desktop table rows
    str_table= r'<table>'+ str(rows) + r'</table>'   #Make string which pandas can read
    df = pd.read_html(str_table)[0]
    return cleanup_func(df)
