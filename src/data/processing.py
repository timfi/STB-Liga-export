# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np

__all__ = [
    'cleanup_indexdb_dump',
]


def cleanup_indexdb_dump(fut):
    print(fut.result())
