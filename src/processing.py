# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np

__all__ = [
    'cleanup_indexdb_dump',
    'STB_DB_CLEANUP_MAP',
]


def cleanup_indexdb_dump(fut, *, cleanup_functions={}):
    data = fut.result()
    assert data.keys() == cleanup_functions.keys(), "Cleanup functions didn't mach the extracted data set."
    ret = {key: cleanup_functions[key](item) for key, item in data.items()}
    print(ret)


def _cleanup_begegnung(df):
    return df


def _cleanup_person(df):
    return df


def _cleanup_mannschaft(df):
    return df


def _cleanup_tabelle(df):
    return df


def _cleanup_verein(df):
    return df


def _cleanup_halle(df):
    return df


def _cleanup_saison(df):
    return df


def _cleanup_cache(df):
    return df


STB_DB_CLEANUP_MAP = {
    'begegnung': _cleanup_begegnung,
    'person': _cleanup_person,
    'mannschaft': _cleanup_mannschaft,
    'tabelle': _cleanup_tabelle,
    'verein': _cleanup_verein,
    'halle': _cleanup_halle,
    'saison': _cleanup_saison,
    'cache': _cleanup_cache,
}
