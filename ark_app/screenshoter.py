from PIL import Image
        # Optimize image
        # foo = Image.open(image_path)
        # foo.save(image_path, optimize=True,quality=95)
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

class ScreenShoter:
    def __init__(self, driver):
        self._driver = driver
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
        #time.sleep(10)
    
    def take_and_save_screenshot(self, path):
        self._driver.set_window_size(1000, self._height)
        self._driver.save_screenshot(path)
       
    