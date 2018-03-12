# -*- coding: utf-8 -*-
from driver import *
from bs4 import BeautifulSoup
import pandas as pd
import lxml
from enum import Enum, unique
from .processing import *

__all__ = [
    'get_ranking_data',
    'get_team_data',
    'get_encounter_data',
    'MAPPINGS',
    'URLS',
]

@unique
class URLS(str, Enum):
    TABELLEN = 'https://kutu.stb-liga.de/njs/#/?view=Tabellen'
    MANNSCHAFT = 'https://kutu.stb-liga.de/njs/#/?view=Mannschaft&filter='
    BEGEGNUNG =  'https://kutu.stb-liga.de/njs/#/?view=Begegnung&filter='

def get_dfs_from_soup(soup):
    '''A method to transform all the tables in a given soup into pandas dataframes.

    <args>
    soup - soup to transform
    '''
    return [pd.read_html(table.prettify(), flavor='html5lib')[0] for table in soup.find_all('table')]

def get_soup_from_args(url, path, *, uid=None, driver=None, additional_parameters={}):
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
            soup = extract_soup(url + str(uid), driver=driver)
        else:
            soup = extract_soup(url, driver=driver)
    else:
        with open(path, encoding='utf-8', mode='r') as f:
            soup = BeautifulSoup(f, 'html.parser', **additional_parameters)
    return soup

def get_team_data(team_id=68, *, path=None, cleanup_func=cleanup_team_data, driver=None):
    '''A method to get the given team data.

    <args>
    team_id - id of the team (defaults to 68)

    <kwargs>
    path - html file path to query from [if not given the default url is queried]
    cleanup_func - function to clean up data
    driver - webdriver to use
    '''
    soup = get_soup_from_args(URLS.MANNSCHAFT, path, uid=team_id, driver=driver)
    dfs = get_dfs_from_soup(soup)
    return cleanup_func(dfs)

def get_ranking_data(*, path=None, cleanup_func=cleanup_ranking_data, driver=None):
    '''A method to get the given ranking data.

    <kwargs>
    path - html file path to query from [if not given the default url is queried]
    cleanup_func - function to clean up data
    driver - webdriver to use
    '''
    soup = get_soup_from_args(URLS.TABELLEN, path, driver=driver)
    dfs = get_dfs_from_soup(soup)
    return cleanup_func(dfs)

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
    soup = get_soup_from_args(URLS.BEGEGNUNG, path, uid=encounter_id, driver=driver)
    table = soup.find('table')
    rows = table.find_all('tr', attrs=['even desktop', 'odd desktop'])  #Find all desktop table rows
    str_table= r'<table>'+ str(rows) + r'</table>'   #Make string which pandas can read
    df = pd.read_html(str_table)[0]
    return cleanup_func(df)

class MAPPINGS(Enum):
    TEAM = get_team_data
    RANKING = get_ranking_data
    ENCOUNTER = get_encounter_data
