import requests
import threading
import random
import time
from datetime import datetime
from utils.google_sheet import SheetClient
from v5.ryanair.helpers.proxy import proxyDict, HEADERS, MAX_TRY

total_api_calls = 0
failed_api_calls = 0


def ryanair_search_api(url, sheet_obj):

    is_success = False
    data = None
    exception = None

    try:
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
    return is_success, data, exception


def handle_api_calls_per_second(url, sheet_obj):
    random_no = random.randint(2, 15)
    for i in range(random_no):
        threading.Thread(target=ryanair_search_api, args=(url, sheet_obj)).start()

    return random_no


def t2():
    seconds = 20000
    sheet_obj = SheetClient().get_sheet_instance("APi Test", "Sheet1")

    for i in range(seconds):
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


def search_api_response(search_url):
    departure_flight_data = {}
    arrival_flight_data = {}
    currency = None
    error = None
    request_hit = 0

    while request_hit < MAX_TRY:
        try:
            response = requests.get(search_url, headers=HEADERS, proxies=proxyDict)

            if response.status_code == 200:
                response = response.json()

                currency = response['currency']
                trips = response['trips']

                if len(trips):
                    departure_flight_data = trips[0]

                    if len(trips) > 1:
                        arrival_flight_data = trips[1]

                else:
                    error = "Trips data is not present"

                break
        except Exception as ex:
            print(ex)

        request_hit += 1

    return currency, departure_flight_data, arrival_flight_data, error


def get_fare_values():

    response = None
    url = "https://www.ryanair.com/apps/ryanair/i18n.frontend.auth.flightselect.legalfooter.networkerrors.deposit" \
          "-payment.chatbot.breadcrumbs.en-gb.json"
    request_hit = 0

    while request_hit < MAX_TRY:
        try:
            response = requests.get(url, headers=HEADERS, proxies=proxyDict)

            if response.status_code == 200:
                response = response.json()
                break

        except Exception as ex:
            print(ex)

        request_hit += 1

    return response

