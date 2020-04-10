from PIL import Image
        # Optimize image
        # foo = Image.open(image_path)
        # foo.save(image_path, optimize=True,quality=95)
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions


_SUPPORTED_BROWERS = {"chrome", "firefox"}
_DEFAULT_BROWSER = "chrome"
class ScreenShoter:
    def __init__(self):
        def get_default_driver():
            if _DEFAULT_BROWSER == "chrome":
                options = webdriver.ChromeOptions()
                options.add_argument("--headless")
                driver = webdriver.Chrome(options=options)
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
        #time.sleep(10)
    

    def get_screenshot_as_png(self):
        self._driver.set_window_size(1000, self._height)
        return self._driver.get_screenshot_as_png()


def take_url_webpage_screenshot_as_png(url, screenshoter=ScreenShoter()):
    '''
    Return screenshot image in png format
    '''
    url = url.strip()

    screenshoter.open_url(url)
    screenshoter.force_render()
    return screenshoter.get_screenshot_as_png()  