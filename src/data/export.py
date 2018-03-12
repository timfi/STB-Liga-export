# -*- coding: utf-8 -*-
import pandas as pd
from contextlib import contextmanager

__all__ = [
    'excel_writer',
    'write_data_to_csv',
]

@contextmanager
def excel_writer(path):
    '''A contextmanager for the pandas excel writer.'''
    path = path + '.xlsx' if not path.endswith('.xlsx') else path
    writer = pd.ExcelWriter(path)
    yield writer
    writer.save()

def write_data_to_csv(dfs=[], path='test.csv'):
    '''A method to write a list of pandas dataframes to a csv file'''
    with open(path, encoding='utf-8', mode='w') as f:
        for df in dfs:
            df.to_csv(f)
