import time

from selenium.webdriver.common.by import By

from v1.ryanair.constants.myip_contants import IP_CLASS_NAMES


class IpAddressInfo:
    def __init__(self, driver):
        self.driver = driver

    def scrap_ip_address(self):
        ip_info_div = self.driver.find_element(By.CLASS_NAME, IP_CLASS_NAMES['IP_INFO'])
        ip_info = ip_info_div.find_elements(By.CLASS_NAME, IP_CLASS_NAMES['CARD_ROW'])

        ip_info_details = {}

        for each in ip_info:

            param = each.find_element(By.CLASS_NAME, IP_CLASS_NAMES['COL_PARAM']).text
            value = each.find_element(By.CLASS_NAME, IP_CLASS_NAMES['COL_VALUE']).text

            ip_info_details[param.lower()[:-1]] = value

        return ip_info_details

    def scrap_time_info(self):
        time_info_div = self.driver.find_element(By.CLASS_NAME, IP_CLASS_NAMES['TIME_INFO'])
        time_info = time_info_div.find_elements(By.CLASS_NAME, IP_CLASS_NAMES['CARD_ROW'])

        time_info_details = {}

        for each in time_info:
            param = each.find_element(By.CLASS_NAME, IP_CLASS_NAMES['COL_PARAM']).text
            value = each.find_element(By.CLASS_NAME, IP_CLASS_NAMES['COL_VALUE']).text

            time_info_details[param.lower()[:-1]] = value

        return time_info_details

    def scrap_details(self):
        details = {}
        self.driver.get('https://myip.link/')
        time.sleep(1)
        details['ip_info'] = self.scrap_ip_address()
        details['time_info'] = self.scrap_time_info()

        return details
