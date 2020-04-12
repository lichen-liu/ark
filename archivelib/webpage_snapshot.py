from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions

import os
import pathlib

import platform


def get_chrome_executable_path(running_locally):
    '''
    (chromedriver_path, chrome_path/None)
    '''
    if running_locally:
        chromedrivers_path = os.path.join(str(pathlib.Path(__file__).parent.parent.absolute()), 'bin')
        operating_system = platform.system()
        if operating_system == 'Windows':
            chromedriver_path = os.path.join(chromedrivers_path, 'chromedriver.exe')
        elif operating_system == 'Darwin':
            chromedriver_path = os.path.join(chromedrivers_path, 'chromedriver')
        return (chromedriver_path, None)
    else:
        return ('/tmp/bin/chromedriver', '/tmp/bin/headless-chromium')


class Snapshoter:
    def __init__(self, running_locally):
        chromedriver_path, chrome_path = get_chrome_executable_path(running_locally)
        print('chrome executable at', chrome_path if chrome_path else 'default location')
        print('chromedriver executable at', chromedriver_path)

        if running_locally:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--headless")
        else:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-data-dir=/tmp/user-data')
            chrome_options.add_argument('--hide-scrollbars')
            chrome_options.add_argument('--enable-logging')
            chrome_options.add_argument('--log-level=0')
            chrome_options.add_argument('--v=99')
            chrome_options.add_argument('--single-process')
            chrome_options.add_argument('--data-path=/tmp/data-path')
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--homedir=/tmp')
            chrome_options.add_argument('--disk-cache-dir=/tmp/cache-dir')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36')
            chrome_options.binary_location = chrome_path
        
        self._driver = webdriver.Chrome(executable_path=chromedriver_path, options=chrome_options)
        self._driver.maximize_window()
        self._height = 0


    def open_url(self, url):
        self._driver.get(url)
    

    def force_render(self):
        self._height = self._driver.execute_script("return document.body.scrollHeight")
        #Scroll the page to make sure everything is loaded
        #driver.set_window_size(1000, height - 700)
        #driver.execute_script("window.scrollTo(0, 700)")
        #driver.execute_script("window.scrollTo(0, 0)")
        # import time
        # time.sleep(10)
    

    def get_screenshot_as_png(self):
        self._driver.set_window_size(1000, self._height)
        try:
            png = self._driver.get_screenshot_as_png()
        except Exception as e:
            print('Unexpected exception: ' + str(e))
            return b''
        return png


    def get_webpage_inner_html(self):
        #document_html = self._driver.execute_script("return document.documentElement.innerHTML;")
        #body_html = self._driver.execute_script("return document.body.innerHTML;")
        return self._driver.page_source


def take_url_webpage_snapshot(url, running_locally, snapshoter=None):
    '''
    (png, text)
    '''
    if snapshoter is None:
        snapshoter = Snapshoter(running_locally=running_locally)
    snapshoter.open_url(url)
    snapshoter.force_render()

    image = snapshoter.get_screenshot_as_png()
    text = snapshoter.get_webpage_inner_html() 

    return image, text