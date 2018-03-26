# -*- coding: utf-8 -*-
import os
from contextlib import contextmanager
from threading import RLock
from time import sleep

from selenium import webdriver
from selenium.webdriver.firefox.options import Options as DriverOptions

from ..concurrent import ConcurrentProcessor
from .task import _get
from ..helpers import Singleton

__all__ = [
    'Driver'
]


class Driver(ConcurrentProcessor, metaclass=Singleton):
    """A basic wrapper class for a selenium driver"""
    def __init__(self, *args, path=None, home_address=None, headless=False, **kwargs):
        super(Driver, self).__init__(*args, **kwargs)
        options = DriverOptions()
        if headless:
            options.add_argument('--headless')
        self._logger.info('Starting Geckodriver...')
        if path:
            if os.name == 'nt' and not path.endswith('.exe'):
                path += '.exe'
            self._resource = webdriver.Firefox(firefox_options=options, executable_path=path)
        else:
            self._resource = webdriver.Firefox(firefox_options=options)
        if home_address:
            self.get(home_address)

    def quit(self):
        super(Driver, self).quit()
        with self._lock:
            try:
                self._logger.info('Closing driver...')
                self._driver.quit()
            except Exception:
                pass

    def get(self, url: str):
        """A threadsafe wrapper method for the standard get method of the webdriver.

        :param url: url: the url to set the driver to
        """
        self.do(_get(url))

    @contextmanager
    def open_new_tab(self, url: str, *, wait_timer: int = 5):
        """A contextmanager to open a url in a new tab and wait for a given time before yielding control back to caller.

        :param url: the url to go to
        :param wait_timer: how long the driver should wait for the page to load
        """
        with self._lock:
            prev_window_handles = self._resource.window_handles
            self._resource.execute_script(f"window.open('{url}', '_blank')")
            current_window_handle = list(set(self._resource.window_handles) - set(prev_window_handles))[0]
        sleep(wait_timer)
        with self._lock:
            self._resource.switch_to.window(current_window_handle)
            yield
            self._resource.close()
            self._resource.switch_to.window(self._driver.window_handles[0])
