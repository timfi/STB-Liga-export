# -*- coding: utf-8 -*-
import json
from time import sleep

import pandas as pd
from selenium.common.exceptions import NoSuchElementException

from .lib.concurrent import make_task_factory
from .lib.driver import Driver

__all__ = [
    'STBDriver',
    'extract_index_db',
]


class STBDriver(Driver):
    def __init__(self, *args, **kwargs):
        kwargs['home_address'] = 'https://kutu.stb-liga.de'
        super(STBDriver, self).__init__(*args, **kwargs)


@make_task_factory
def extract_index_db(driver, url, tables, *, wait_timer=5):
    """A method to extract the indexdb of a page, that waits for the js to load the data before extracting.

    :param driver: driver to operate on
    :param url: the url to get the data from
    :param tables: the tables to extract
    :param wait_timer: how long the driver should wait for at maximum
    :return: dict with extracted values
    """
    js_snippet = """
    var tbl = "{}";
    var templist = document.createElement('templist-' + tbl);
    document.body.appendChild(templist);
    CONSOLE.log("------------------------------");
    CONSOLE.log("> Started extraction of " + tbl);
    var trans = DB.db.transaction([tbl], "readonly");
    var store = trans.objectStore(tbl);
    var range = IDBKeyRange.lowerBound(0);
    var cursorRequest = store.openCursor(range);
    
    cursorRequest.onsuccess = function(evt) {{
        if(evt.target.result) {{
            var s = document.createTextNode(JSON.stringify(evt.target.result.value)+'<->');
            templist.appendChild(s);
            evt.target.result.continue();
        }}
        else {{
            var s = document.createTextNode('[DONE]');
            templist.appendChild(s);
        }}
    }};
    
    CONSOLE.log("> Done with " + tbl);
    """
    ret = {}
    with driver.open_new_tab(url, wait_timer=wait_timer):
        for table in tables:
            # start js snippet
            driver.execute_script(js_snippet.format(table))
            templist_name = 'templist-' + table

            # wait for the db cursor to reach the end
            done = False
            while not done:
                try:
                    sleep(1)
                    if '[DONE]' in driver.find_element_by_tag_name(templist_name).text:
                        driver.logger.debug(f'Found templist <{templist_name}>')
                        done = True
                except NoSuchElementException:
                    pass

            # grad clear text data from the pages html
            res = driver.find_element_by_tag_name(templist_name).text
            ret[table] = pd.DataFrame([json.loads(x) for x in res.split('<->')[:-1]])
            driver.logger.debug(f"{table} ==> {ret[table]}")
    return ret
