# -*- coding: utf-8 -*-
import pandas as pd
from contextlib import contextmanager
import os

__all__ = [
    'excel_writer',
    'write_data_to_csv',
    'write_html_to_file',
]


@contextmanager
def excel_writer(path):
    '''A contextmanager for the pandas excel writer.'''
    path = path + '.xlsx' if not path.endswith('.xlsx') else path
    writer = pd.ExcelWriter(path)
    yield writer
    writer.save()


def write_data_to_csv(dfs=[], path='test'):
    '''A method to write a list of pandas dataframes to a csv files'''
    for i, df in enumerate(dfs):
        with open(os.path.join(path, 'export_' + str(i) + '.csv'), encoding='utf-8', mode='w') as f:
            df.to_csv(f)


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
            f.write(extract_soup(url).prettify())
        else:
            raise RuntimeError('Either give a url or a preextracted soup, not both or nothing.')
