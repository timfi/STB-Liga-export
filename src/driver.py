# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options as DriverOptions
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.keys import Keys
from time import sleep
from bs4 import BeautifulSoup
import os
from threading import RLock
from concurrent.futures import ThreadPoolExecutor
import logging
from contextlib import contextmanager
import json

__all__ = [
    'start_webdriver',
    'create_webdriver',
    'extract_soup',
]

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


class Driver:
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
            self.open_url(home_address)

        self.logger.debug('Starting ThreadPoolExecutor...')
        self._worker_pool = ThreadPoolExecutor(max_workers=8)

    def get(self, url):
        '''A threadsafe wrapper method for the standard get method of the webdriver.

        <args>
        url - the url to set the driver to
        '''
        with self._lock:
            self._driver.get(url)

    def do(self, todo, callback, *args, **kwargs):
        '''A method to submit a task request and callback to the drivers worker pool.

        <args>
        todo - the url to get the data from
        callback - the callback method to be added
        * - any arguments needed for todo

        <kwargs>
        * - any keyword arguments needed for todo
        '''
        fut = self._worker_pool.submit(todo, *args, **kwargs)
        fut.add_done_callback(callback)

    def extract_indexdb(self, url, callback, *, wait_timer=5, tables=[]):
        '''A method to submit a indexdb extraction request and callback to the drivers worker pool.

        <args>
        url - the url to get the indexdb from
        callback - the callback method to be added

        <kwargs>
        wait_timer - how long the driver should wait for at maximum
        '''
        self.do(self.__extract_indexdb, callback, url, wait_timer=wait_timer)#, tables=[])

    def __extract_indexdb(self, url, *, wait_timer=5, tables=['begegnung', 'person', 'mannschaft', 'tabelle', 'verein', 'halle', 'saison', 'cache']):
        '''A method to extract the indexdb of a page, that waits for the js to load the data before extracting.

        <args>
        url - the url to get the data from

        <kwargs>
        wait_timer - how long the driver should wait for at maximum
        '''
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
        CONSOLE.log(JSON.stringify(ret));
        return JSON.stringify(ret)
        """ % str(tables)
        with self.__open_new_tab(url, wait_timer=wait_timer):
            self.logger.debug(f"Running jssnippet: {jssnippet}")
            JSON = self._driver.execute_script(jssnippet)
            input()
        return JSON

    def extract_soup(self, url, callback, *, wait_timer=5):
        '''A method to submit a soup extraction request and callback to the drivers worker pool.

        <args>
        url - the url to get the data from
        callback - the callback method to be added

        <kwargs>
        wait_timer - how long the driver should wait for at maximum
        '''
        self.do(self.__extract_soup, callback, url, wait_timer=wait_timer)

    def __extract_soup(self, url, *, wait_timer=5):
        '''A method to extract the html of a page, that waits for the js to load the data before extracting.

        <args>
        url - the url to get the data from

        <kwargs>
        wait_timer - how long the driver should wait for at maximum
        '''
        jssnippet = "return document.getElementsByTagName('html')[0].innerHTML"
        with self.__open_new_tab(url, wait_timer=wait_timer):
            soup = BeautifulSoup(self._driver.execute_script(jssnippet), 'html.parser')
        return soup

    @contextmanager
    def __open_new_tab(self, url, *, wait_timer=5):
        '''A method to open a url in a new tab and wait for a given time before yielding control back to caller.

        <args>
        url - the url to go to

        <kwargs>
        wait_timer - how long the driver should wait for at maximum
        '''
        with self._lock:
            prev_window_handles = self._driver.window_handles
            self._driver.execute_script(f"window.open('{url}', '_blank')")
            current_window_handle = list(set(self._driver.window_handles) - set(prev_window_handles))[0]
        sleep(wait_timer)
        with self._lock:
            self._driver.switch_to_window(current_window_handle)
            yield
            self._driver.close()
            self._driver.switch_to_window(self._driver.window_handles[0])

    def quit(self):
        with self._lock:
            self._driver.quit()
