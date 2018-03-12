# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options as DriverOptions
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.keys import Keys
from contextlib import contextmanager
from time import sleep
from bs4 import BeautifulSoup
import os
from threading import RLock

__all__ = [
    'start_webdriver',
    'create_webdriver',
    'extract_soup',
]

DRIVER_LOCK = RLock()

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

@contextmanager
def start_webdriver():
    '''A contextmanager for the selenium webdriver.'''
    driver = create_webdriver()
    yield driver
    driver.quit()

def create_webdriver(*, headless=True):
    '''A method to create a selenium webdriver.'''
    options = DriverOptions()
    if headless:
        options.add_argument('--headless')
    if os.name == 'nt':
        subpath = 'drivers/geckodriver.exe'
    else:
        subpath = 'drivers/geckodriver'
    path = os.path.join(os.path.dirname(os.getcwd()), subpath)
    driver = webdriver.Firefox(firefox_options=options, executable_path=path)
    return driver

def extract_soup(url, *, wait_timer=5, driver=None):
    '''A method to extract the html of a page, that waits for the js to load the data before extracting.

    <args>
    url - the url to get the data from

    <kwargs>
    wait_timer - how long the driver should wait for at maximum
    driver - webdriver to use
    '''
    if not driver:
        with start_webdriver() as local_driver:
            if local_driver.current_url != url:
                local_driver.get(url)
                # try:
                #     WebDriverWait(seldriver, wait_timer).until(page_has_loaded())
                # except:
                #     raise Exception('Couldn\'t load page')
                sleep(wait_timer)
            return retrieve_soup(local_driver)
    else:
        with DRIVER_LOCK:
            prev_window_handles = driver.window_handles
            driver.execute_script(f"window.open('{url}', '_blank')")
            current_window_handle = list(set(driver.window_handles) - set(prev_window_handles))[0]
        sleep(wait_timer)
        with DRIVER_LOCK:
            driver.switch_to_window(current_window_handle)
            soup = retrieve_soup(driver)
            driver.close()
            driver.switch_to_window(driver.window_handles[0])
        return soup

def retrieve_soup(driver):
    '''A method to retrieve the soup from a running webdriver.

    <args>
    driver - driver to extract html from
    '''
    return BeautifulSoup(driver.execute_script("return document.getElementsByTagName('html')[0].innerHTML"), 'html.parser')
