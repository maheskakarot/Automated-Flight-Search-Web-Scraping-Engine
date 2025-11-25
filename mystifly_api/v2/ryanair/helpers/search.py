import requests
import threading
import random
import time
from datetime import datetime
from utils.web_driver import WebDriver
from v2.ryanair.scripts.common import CommonActions
from utils.google_sheet import SheetClient
from utils.delete_file import delete_file_from_os
from utils.aws_s3 import UploadFiles

# # Initiating driver globally
# driver = WebDriver().driver
#
# # Initial search request
# first_request = "https://www.ryanair.com/gb/en/trip/flights/select?adults=1&teens=0&children=0&infants=0&dateOut=2022-11-27&dateIn=&isConnectedFlight=false&isReturn=false&discount=0&promoCode=&originMac=LON&destinationIata=DUB&tpAdults=1&tpTeens=0&tpChildren=0&tpInfants=0&tpStartDate=2022-11-27&tpEndDate=&tpDiscount=0&tpPromoCode=&tpOriginMac=LON&tpDestinationIata=DUB"
# driver.get(first_request)
#
# # Closing cookies popup
# common_actions_obj = CommonActions(driver)
# common_actions_obj.accept_cookies()

total_api_calls = 0
failed_api_calls = 0


def ryanair_search_api(url, sheet_obj):
    username = 'sahil1021'
    password = 'Sahil1234'

    # proxy = f'http://{username}:{password}@gate.smartproxy.com:7000'

    http_proxy = "http://sahil1021:Z7IYgNuG7VnGi3Z6@proxy.packetstream.io:31112"
    https_proxy = "http://sahil1021:Z7IYgNuG7VnGi3Z6@proxy.packetstream.io:31112"

    proxyDict = {
        "http": http_proxy,
        "https": https_proxy,
    }

    is_success = False
    data = None
    exception = None

    try:
        USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36"
        HEADERS = {
            'user-agent': USER_AGENT
        }

        request = requests.get(url, headers=HEADERS, proxies=proxyDict)

        request_status = request.status_code
        if request_status == 200:
            is_success = True
            response = request.json()
            data = str(response['trips'])

            global total_api_calls
            total_api_calls += 1

        else:
            print(request_status)
    except Exception as ex:
        exception = str(ex)
        print(ex)
        global failed_api_calls
        failed_api_calls += 1
        # random_no = random.randint(1, 100)
        #
        # if random_no % 15 == 0:
        #     row_data = [str(datetime.now()), random.randint(5, 20), url, "Failed", exception]
        #     sheet_obj.insert_row(row_data, 2)
    return is_success, data, exception


def handle_api_calls_per_second(url, sheet_obj):
    random_no = random.randint(2, 15)
    print("Random Number - ", random_no)
    for i in range(random_no):
        threading.Thread(target=ryanair_search_api, args=(url, sheet_obj)).start()

    return random_no


def t2():
    seconds = 20000
    sheet_obj = SheetClient().get_sheet_instance("APi Test", "Sheet1")

    for i in range(seconds):
        print("Seconds - ", i)
        search_url = generate_search_url(select_random_search_request_data())
        if i % 58 == 0:
            is_success, data, exception = ryanair_search_api(search_url, sheet_obj)

            if is_success:
                row_data = [str(datetime.now()), total_api_calls, failed_api_calls, random.randint(2, 15), search_url, data]

            else:
                row_data = [str(datetime.now()), total_api_calls, failed_api_calls, random.randint(2, 15), search_url, "Failed", exception]

            sheet_obj.insert_row(row_data, 2)
        else:
            random_no = handle_api_calls_per_second(search_url, sheet_obj)

        time.sleep(0.9)


def select_random_search_request_data():
    random_index = random.randint(0, 5)
    search_flights_data = [
        {'ADT': 1, 'CHD': 0, 'INF': 0, 'DATE_IN': '', 'DATE_OUT': '2022-11-20', 'DST_CODE': 'BAR', 'OGN_CODE': 'STN',
         'OGN_IS_MAC': 'false', 'DST_IS_MAC': 'true', 'RETURN_TRIP': 'false'},
        {'ADT': 1, 'CHD': 0, 'INF': 0, 'DATE_IN': '2022-11-27', 'DATE_OUT': '2022-11-20', 'DST_CODE': 'BAR',
         'OGN_CODE': 'STN', 'OGN_IS_MAC': 'false', 'DST_IS_MAC': 'true', 'RETURN_TRIP': 'true'},
        {'ADT': 1, 'CHD': 1, 'INF': 0, 'DATE_IN': '', 'DATE_OUT': '2022-11-25', 'DST_CODE': 'AGP', 'OGN_CODE': 'GLW',
         'OGN_IS_MAC': 'true', 'DST_IS_MAC': 'false', 'RETURN_TRIP': 'false'},
        {'ADT': 1, 'CHD': 1, 'INF': 0, 'DATE_IN': '2022-11-29', 'DATE_OUT': '2022-11-25', 'DST_CODE': 'AGP',
         'OGN_CODE': 'GLW', 'OGN_IS_MAC': 'true', 'DST_IS_MAC': 'false', 'RETURN_TRIP': 'true'},
        {'ADT': 1, 'CHD': 1, 'INF': 1, 'DATE_IN': '', 'DATE_OUT': '2022-11-27', 'DST_CODE': 'ALC', 'OGN_CODE': 'STN',
         'OGN_IS_MAC': 'false', 'DST_IS_MAC': 'false', 'RETURN_TRIP': 'false'},
        {'ADT': 1, 'CHD': 1, 'INF': 1, 'DATE_IN': '2022-11-30', 'DATE_OUT': '2022-11-27', 'DST_CODE': 'ALC',
         'OGN_CODE': 'STN', 'OGN_IS_MAC': 'false', 'DST_IS_MAC': 'false', 'RETURN_TRIP': 'true'},
    ]
    return search_flights_data[random_index]


def generate_search_url(request_data):
    URL = f"https://www.ryanair.com/api/booking/v4/en-gb/availability?ADT={request_data['ADT']}&CHD={request_data['CHD']}&" \
          f"DateIn={request_data['DATE_IN']}&DateOut={request_data['DATE_OUT']}&Destination={request_data['DST_CODE']}&Disc=0&INF={request_data['INF']}&Origin={request_data['OGN_CODE']}&" \
          f"TEEN=0&promoCode=&IncludeConnectingFlights=false&FlexDaysBeforeOut=2&" \
          f"FlexDaysOut=2&FlexDaysBeforeIn=2&FlexDaysIn=2&OriginIsMac={request_data['OGN_IS_MAC']}&" \
          f"DestinationIsMac={request_data['DST_IS_MAC']}&RoundTrip={request_data['RETURN_TRIP']}&ToUs=AGREED"

    return URL


"""
from v2.ryanair.helpers.search import *
t2()
"""
