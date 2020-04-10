from PIL import Image
        # Optimize image
        # foo = Image.open(image_path)
        # foo.save(image_path, optimize=True,quality=95)
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

import os
import pathlib

import platform




_SUPPORTED_BROWERS = {"chrome", "firefox"}
_DEFAULT_BROWSER = "chrome"
class Snapshoter:
    def __init__(self):
        def get_default_driver():
            if _DEFAULT_BROWSER == "chrome":
                options = webdriver.ChromeOptions()
                options.add_argument("--headless")
                
                chromedrivers_path = os.path.join(str(pathlib.Path(__file__).parent.absolute()), 'chromedrivers')
                
                operating_system = platform.system()
                if operating_system == 'Windows':
                    chromedriver_path = os.path.join(chromedrivers_path, 'chromedriver.exe')
                elif operating_system == 'Darwin':
                    chromedriver_path = os.path.join(chromedrivers_path, 'chromedriver')

                driver = webdriver.Chrome(executable_path=chromedriver_path, options=options)
            elif _DEFAULT_BROWSER == "firefox":
                options = webdriver.FirefoxOptions()
                options.add_argument("--headless")
                driver = webdriver.Firefox(options=options)
            else:
                options = webdriver.ChromeOptions()
                options.add_argument("--headless")
                driver = webdriver.Chrome(options=options)

            return driver

        self._driver = get_default_driver()
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
        return self._driver.get_screenshot_as_png()


    def get_webpage_inner_html(self):
        #document_html = self._driver.execute_script("return document.documentElement.innerHTML;")
        #body_html = self._driver.execute_script("return document.body.innerHTML;")
        return self._driver.page_source


def take_url_webpage_snapshot(url, snapshoter=Snapshoter()):
    '''
    (png, text)
    '''
    snapshoter.open_url(url)
    snapshoter.force_render()

    image = snapshoter.get_screenshot_as_png()
    text = snapshoter.get_webpage_inner_html() 

    return image, text