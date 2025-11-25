import time

from selenium import webdriver
from account.models import SubscriberWebDriver, SubscriberSearchHistory
from utils.web_driver import WebDriver


# Initiate new webdriver
def new_webdriver(subscriber):

    driver = WebDriver().driver

    url = driver.command_executor._url
    session_id = driver.session_id

    webdriver_obj = SubscriberWebDriver.objects.create(
        subscriber=subscriber,
        url=url,
        session_id=session_id
    )

    return driver, webdriver_obj


class SessionRemote(webdriver.Remote):
    def start_session(self, desired_capabilities, browser_profile=None):
        # Skip the NEW_SESSION command issued by the original driver
        # and set only some required attributes
        self.w3c = True


# Reuse already open webdriver of user
def reuse_webdriver(subscriber):
    is_driver_reused = False
    webdriver_obj = SubscriberWebDriver.objects.filter(subscriber=subscriber, is_active=True).last()

    if webdriver_obj:
        url = webdriver_obj.url
        session_id = webdriver_obj.session_id
        try:
            driver = SessionRemote(command_executor=url, desired_capabilities={})
            driver.session_id = session_id
            print(driver.title)

            is_driver_reused = True
            webdriver_obj.reuse_count = webdriver_obj.reuse_count + 1
            webdriver_obj.save()

        except Exception as ex:
            print(ex)
            # TODO: Need to record these exceptions
            driver, webdriver_obj = new_webdriver(subscriber)

    else:
        driver, webdriver_obj = new_webdriver(subscriber)

    return driver, is_driver_reused, webdriver_obj


def update_current_screen(history_obj, current_screen):
    history_obj.current_screen = current_screen
    history_obj.save()


def change_driver_tab(driver, last_history_obj, url):

    if last_history_obj and last_history_obj.current_screen != SubscriberSearchHistory.SEARCH_SCREEN:

        driver.execute_script("window.open('');")
        windows = driver.window_handles
        driver.close()
        # # Switch to the new window
        driver.switch_to.window(windows[1])

    driver.get(url)


def close_webdriver(driver, webdriver_obj):
    driver.close()
    webdriver_obj.is_active = False
    webdriver_obj.save()

