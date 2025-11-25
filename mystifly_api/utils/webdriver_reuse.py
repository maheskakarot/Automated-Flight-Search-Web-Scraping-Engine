import time
from selenium import webdriver
from easyjet.models import SearchIDWebdriver
from seleniumwire import webdriver


# Initiate new webdriver
def new_webdriver(SearchIdentifier):

    driver = WebDriver().driver
    a=driver.execute_script("return navigator.userAgent")

    url = driver.command_executor._url
    session_id = driver.session_id

    webdriver_obj = SearchIDWebdriver.objects.create(
        search_identifier=SearchIdentifier,
        url=url,
        session_id=session_id
    )
    webdriver_obj.save()

    return driver, webdriver_obj


class SessionRemote(webdriver.Remote):
    def start_session(self, desired_capabilities, browser_profile=None):
        # Skip the NEW_SESSION command issued by the original driver
        # and set only some required attributes
        self.w3c = True


# Reuse already open webdriver of user
def reuse_webdriver(SearchIdentifier):
    is_driver_reused = False
    webdriver_obj = SearchIDWebdriver.objects.filter(search_identifier=SearchIdentifier, is_active=True).last()
    if webdriver_obj:
        url = webdriver_obj.url
        session_id = webdriver_obj.session_id
        try:
            driver = SessionRemote(command_executor=url)
            print("remote>>>")
            driver.session_id = session_id
            print("<TITLE>",driver.title)

            is_driver_reused = True
            # webdriver_obj.reuse_count = webdriver_obj.reuse_count + 1
            # webdriver_obj.save()

        except Exception as ex:
            print("Using new webdriver")
            print(ex)
            # TODO: Need to record these exceptions
            driver, webdriver_obj = new_webdriver(SearchIdentifier)

    else:
        driver, webdriver_obj = new_webdriver(SearchIdentifier)

    return driver, is_driver_reused, webdriver_obj


def update_current_screen(history_obj, current_screen):
    history_obj.current_screen = current_screen
    history_obj.save()



def close_webdriver(driver, webdriver_obj):
    driver.close()
    webdriver_obj.is_active = False
    webdriver_obj.save()

