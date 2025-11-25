import random
# from selenium import webdriver
from django.conf import settings
from selenium.webdriver.common.proxy import ProxyType, Proxy
from seleniumwire import webdriver
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import random
import undetected_chromedriver as uc


class WebDriver:
    def __init__(self):
        self.CHROME_DRIVER_LOCATION = settings.CHROME_DRIVER_LOCATION
        self.CHROME_BINARY_LOCATION = settings.CHROME_BINARY_LOCATION
        self.IS_HEADLESS_DRIVER = settings.IS_HEADLESS
        self.driver = self.__chrome_driver()

    def __chrome_driver(self):
      
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--incognito")
        options.add_argument("--disable-popup-blocking")
        return uc.Chrome(options=options)
       
