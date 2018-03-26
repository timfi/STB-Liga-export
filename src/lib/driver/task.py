# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup

from ..concurrent import make_task_factory


__all__ = [
    'extract_soup',
]


@make_task_factory
def extract_soup(driver, url, *, wait_timer=5):
    """A Task to extract the html of a page, that waits for the js to load the data before extracting.

    :param driver: driver to operate on
    :param url: the url to get the data from
    :param wait_timer: how long the driver should wait for at maximum
    :return: the extracted soup
    """
    js_snippet = "return document.getElementsByTagName('html')[0].innerHTML"
    with driver.open_new_tab(url, wait_timer=wait_timer):
        soup = BeautifulSoup(driver.execute_script(js_snippet), 'html.parser')
    return soup


@make_task_factory
def _get(driver, url):
    with driver._lock:
        driver._logger.info(f'Pointing driver to {url}')
        driver.get(url)
    return True


