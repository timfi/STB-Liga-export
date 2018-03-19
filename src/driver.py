# -*- coding: utf-8 -*-
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from threading import RLock
from time import sleep

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as DriverOptions

from .data.helpers import Singleton

__all__ = [
    'Driver',
]


class Driver(metaclass=Singleton):
    def __init__(self, *, path=None, number_of_workers=8, home_address=None, headless=False):
        self.logger = logging.getLogger(self.__class__.__qualname__)
        options = DriverOptions()
        if headless:
            options.add_argument('--headless')
        if path:
            if os.name == 'nt' and not path.endswith('.exe'):
                path += '.exe'
            self._driver = webdriver.Firefox(firefox_options=options, executable_path=path)
        else:
            self._driver = webdriver.Firefox(firefox_options=options)
        self._lock = RLock()
        if home_address:
            self.get(home_address)

        self.logger.debug('Starting ThreadPoolExecutor...')
        self._worker_pool = ThreadPoolExecutor(max_workers=number_of_workers)

    def get(self, url):
        """A threadsafe wrapper method for the standard get method of the webdriver.

        :Args:
        url - the url to set the driver to
        """
        with self._lock:
            self._driver.get(url)

    def do(self, todo, callback, *args, **kwargs):
        """A method to submit a task request and callback to the drivers worker pool.

        :Args:
            - todo: the url to get the data from
            - callback: - the callback method to be added
            - *: any arguments needed for todo

        :Kwargs:
            - *: any keyword arguments needed for todo
        """
        fut = self._worker_pool.submit(todo, *args, **kwargs)
        fut.add_done_callback(callback)

    def extract_indexdb(self, url, callback, *, wait_timer=5, tables=()):
        """A method to submit a indexdb extraction request and callback to the drivers worker pool.

        :Args:
            - url: the url to get the indexdb from
            - callback: the callback method to be added

        :Kwargs:
            - wait_timer: how long the driver should wait for at maximum
        """
        self.do(self.__extract_indexdb, callback, url, wait_timer=wait_timer)  # , tables=())

    def __extract_indexdb(self, url, *, wait_timer=5, tables=('begegnung', 'person', 'mannschaft', 'tabelle', 'verein', 'halle', 'saison', 'cache')):
        """A method to extract the indexdb of a page, that waits for the js to load the data before extracting.

        :Args:
            - url: the url to get the data from

        :Kwargs:
            - wait_timer: how long the driver should wait for at maximum
        """
        # TODO fix js snippet for json style data extraction
        jssnippet = """
        var tbls = %s
        var ret={};

		tbls.forEach(function(tbl) {
            var trans = DB.db.transaction([tbl], "readonly");
            var store = trans.objectStore(tbl);
            var range = IDBKeyRange.lowerBound(0);
            var cursorRequest = store.openCursor(range);

    		var local = [];

    		cursorRequest.onsuccess = function(evt) {
    			if(evt.target.result) {
    				local.push(evt.target.result.value);
    				evt.target.result.continue();
    			}
    			else {
    				ret[tbl]=local
    			}
    		};
        });
        CONSOLE.log(ret);
        return JSON.stringify(ret)
        """ % str(list(tables))
        with self.__open_new_tab(url, wait_timer=wait_timer):
            self.logger.debug(f"Running jssnippet: {jssnippet}")
            JSON = self._driver.execute_script(jssnippet)
            input()
        return JSON

    def extract_soup(self, url, callback, *, wait_timer=5):
        """A method to submit a soup extraction request and callback to the drivers worker pool.

        :Args:
            - url: the url to get the data from
            - callback: the callback method to be added

        :Kwargs:
            - wait_timer: how long the driver should wait for at maximum
        """
        self.do(self.__extract_soup, callback, url, wait_timer=wait_timer)

    def __extract_soup(self, url, *, wait_timer=5):
        """A method to extract the html of a page, that waits for the js to load the data before extracting.

        :Args:
            - url: the url to get the data from

        :Kwargs:
            - wait_timer: how long the driver should wait for at maximum
        """
        jssnippet = "return document.getElementsByTagName('html')[0].innerHTML"
        with self.__open_new_tab(url, wait_timer=wait_timer):
            soup = BeautifulSoup(self._driver.execute_script(jssnippet), 'html.parser')
        return soup

    @contextmanager
    def __open_new_tab(self, url, *, wait_timer=5):
        """A contextmanager to open a url in a new tab and wait for a given time before yielding control back to caller.

        :Args:
            - url: the url to go to

        :Kwargs:
            - wait_timer - how long the driver should wait for at maximum
        """
        with self._lock:
            prev_window_handles = self._driver.window_handles
            self._driver.execute_script(f"window.open('{url}', '_blank')")
            current_window_handle = list(set(self._driver.window_handles) - set(prev_window_handles))[0]
        sleep(wait_timer)
        with self._lock:
            self._driver.switch_to.window(current_window_handle)
            yield
            self._driver.close()
            self._driver.switch_to.window(self._driver.window_handles[0])

    def quit(self):
        with self._lock:
            self._driver.quit()
