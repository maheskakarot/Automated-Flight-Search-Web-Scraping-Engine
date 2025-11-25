import requests
# import grequests
from .proxy import proxyDict, HEADERS, MAX_TRY


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


def get_fare_values_v4():

    response = {
        'fare_type': 'Value',
        'fare_desc': 'Travel light',
        'ancillaries': {
            'ancillary_name': '1 Small Bag only',
            'ancillary_desc': 'Must fit under the seat\n(40cm x 20cm x 25cm)',
        },
    }

    return response

