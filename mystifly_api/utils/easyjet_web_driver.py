import random
# from selenium import webdriver
from django.conf import settings
from selenium.webdriver.common.proxy import ProxyType, Proxy
from seleniumwire import webdriver
from utils.constants import SMART_PROXY_ENDPOINTS
from v4.ryanair.helpers.proxy import proxyDict
from utils.proxy import get_proxy
from utils.proxy_scheduler import get_proxy_automation


class WebDriver:
    def __init__(self):
        self.CHROME_DRIVER_LOCATION = settings.CHROME_DRIVER_LOCATION
        self.CHROME_BINARY_LOCATION = settings.CHROME_BINARY_LOCATION
        self.IS_HEADLESS_DRIVER = settings.IS_HEADLESS_DRIVER
        self.driver = self.__chrome_driver()

    def __chrome_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--incognito")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-bundled-ppapi-flash")
        options.add_argument("--disable-plugins-discovery")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--disable-infobars")
        options.add_argument("--ignore-certifcate-errors")
        options.add_argument("--ignore-certifcate-errors-spki-list")
        options.binary_location = self.CHROME_BINARY_LOCATION
        options.add_experimental_option("detach", True)
        if self.IS_HEADLESS_DRIVER:
            options.add_argument("--headless=new")

        proxy_value = get_proxy_automation()
        proxy = get_proxy()

        if proxy_value == "PS":
                proxies = {
                'proxy': settings.PROXYDICT
            }
        elif proxy_value == "TT":
            proxies = {"http": f"http://{proxy[0]}"}
        else:
            proxies = {
            'proxy': settings.PROXYDICT
        }
        proxies_options = {
            'proxy': proxies
        }

        web_driver = webdriver.Chrome(executable_path=self.CHROME_DRIVER_LOCATION,
                                      chrome_options=options,
                                      desired_capabilities={}, 
                                      options=proxies_options
                                      )
        web_driver.maximize_window()
        web_driver.implicitly_wait(10)
        return web_driver
    @staticmethod
    def smartproxy():
        prox = Proxy()
        random_proxy = random.choice(SMART_PROXY_ENDPOINTS)
        prox.proxy_type = ProxyType.MANUAL

        prox.http_proxy = '{hostname}:{port}'.format(hostname=random_proxy['hostname'], port=random_proxy['port_no'])
        prox.ssl_proxy = '{hostname}:{port}'.format(hostname=random_proxy['hostname'], port=random_proxy['port_no'])

        capabilities = webdriver.DesiredCapabilities.CHROME
        prox.add_to_capabilities(capabilities)

        return capabilities
