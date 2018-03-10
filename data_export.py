import pandas as pd
from contextlib import contextmanager

@contextmanager
def excel_writer(path):
    '''A contextmanager for the pandas excel writer.'''
    path = path + '.xlsx' if not path.endswith('.xlsx') else path
    writer = pd.ExcelWriter(path)
    yield writer
    writer.save()
