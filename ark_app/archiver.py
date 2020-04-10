#from ark_app import webapp
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from screenshoter import ScreenShoter

#pip install Pillow
#pip install selenium

import time, csv, sys, math, os

supported_browsers = {"chrome", "firefox"}
default_browser = "chrome"
default_path = "."
default_image_format = ".png"

#This should be the s3 trigger function
def archive_webpages_handler():
    archive_webpages()

def archive_webpages():
    #Process s3 trigger event
    #Take_screen_shots(...)
    #Send screenshots to s3


def get_default_driver():
    if default_browser == "chrome":
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
    elif default_browser == "firefox":
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")
        driver = webdriver.Firefox(options=options)
    else:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)

    return driver   

def take_screenshots(image_names_and_page_urls):
    screenshoter = ScreenShoter(get_default_driver())

    for name_and_url in image_names_and_page_urls:
        take_screenshot(name_and_url)

def take_screenshot(name_and_url):
    name = name_and_url[0].strip()
    url = name_and_url[1].strip()

    screenshoter.open_url(url)
    screenshoter.force_render()
    image_path = os.path.join(default_path, name+".png")
    screenshoter.take_and_save_screenshot(image_path)    


names_and_urls = [["google","http://www.google.com"]]
take_screenshots(names_and_urls)
