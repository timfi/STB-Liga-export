import logging
import os
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from functools import partial, wraps
from threading import RLock
from time import sleep

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import SessionNotCreatedException, WebDriverException
from selenium.webdriver.firefox.options import Options as DriverOptions

from .helpers import Singleton, snake_to_camel

__all__ = [
    'Driver',
    'extract_soup'
]


class Driver(metaclass=Singleton):
    """A basic wrapper class for a selenium driver"""
    def __init__(self, *, path=None, number_of_workers=8, home_address=None, headless=False):
        self.logger = logging.getLogger(self.__class__.__qualname__)
        options = DriverOptions()
        if headless:
            options.add_argument('--headless')
        self.logger.info('Starting Geckodriver...')
        if path:
            if os.name == 'nt' and not path.endswith('.exe'):
                path += '.exe'
            self._driver = webdriver.Firefox(firefox_options=options, executable_path=path)
        else:
            self._driver = webdriver.Firefox(firefox_options=options)
        self._lock = RLock()
        if home_address:
            self.get(home_address)

        self.logger.info('Starting ThreadPoolExecutor...')
        self._worker_pool = ThreadPoolExecutor(max_workers=number_of_workers)

    def __getattr__(self, item):
        if item in self.__dict__:
            return self.__dict__[item]
        else:
            return getattr(self._driver, item)

    def get(self, url: str):
        """A threadsafe wrapper method for the standard get method of the webdriver.

        :Args:
            - url: the url to set the driver to
        """
        with self._lock:
            self.logger.info(f'Pointing driver to {url}')
            self._driver.get(url)

    @contextmanager
    def open_new_tab(self, url: str, *, wait_timer: int = 5):
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
            try:
                self._driver.quit()
            except WebDriverException as e:
                if "Failed to decode response from marionette" in e.msg:
                    pass
            except SessionNotCreatedException:
                pass

    def do(self, task: type, callback, *args, **kwargs):
        """A method to submit a task request and callback to the drivers worker pool.

        :Args:
            - task: task to do
            - callback: - the callback method to be added (Signature: future ==> void)
            - *: any arguments needed for task

        :Kwargs:
            - *: any keyword arguments needed for task
        """
        assert issubclass(task.__class__, Driver._Task), 'Task definition must be made with, make_task decorator'
        fut = self._worker_pool.submit(task, self)
        fut.add_done_callback(callback)

    class _Task:
        def __init__(self, *args, **kwargs):
            self._args = args
            self._kwargs = kwargs

        def __call__(self, driver):
            pass

    @staticmethod
    def make_task(func):
        """Decorator to create proper task class definition from method."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            task_name = snake_to_camel(func.__name__ + '_task')
            class Task(Driver._Task):
                def __init__(self, *args, **kwargs):
                    super(Task, self).__init__(*args, **kwargs)
                    self.logger = logging.getLogger(task_name)

                def __call__(self, driver):
                    return func(driver, *self._args, **self._kwargs)
            Task.__name__ = task_name
            return Task(*args, **kwargs)
        return wrapper


@Driver.make_task
def extract_soup(driver, url, *, wait_timer=5):
    """A method to extract the html of a page, that waits for the js to load the data before extracting.

    :Args:
        - url: the url to get the data from

    :Kwargs:
        - wait_timer: how long the driver should wait for at maximum
    """
    jssnippet = "return document.getElementsByTagName('html')[0].innerHTML"
    with driver.open_new_tab(url, wait_timer=wait_timer):
        soup = BeautifulSoup(driver.execute_script(jssnippet), 'html.parser')
    return soup
