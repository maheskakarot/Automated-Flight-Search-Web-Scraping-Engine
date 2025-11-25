import ast
import json
import redis
import requests
from rediscluster import RedisCluster
from django.conf import settings
from account.models import SubscriberSearchHistory, AdminCookies
from v6.ryanair.scripts.decrypt import get_card_details
from custom_logger.models import Email_model
from v6.ryanair.scripts.Azure_blob_manager import API_data, AzureBlob
from utils.proxy import get_proxy
class BookingAutomation():

    def __init__(self, request):
        self.basket_id = ''
        self.request = request
        self.is_return = request.data['AirTripType']
        self.blobs_list = []
        self.booking_email = ''

    def booking(self):
        azure_obj = AzureBlob()
        try:
            self.blobs_list.append(API_data(str(self.request.data), 'Book', 'FR1', 'request'))
            keys = self.get_keys()
            self.basket_id = self.create_basket()
            self.create_booking(keys)
            self.commit_booking()
            self.add_passengers()
            self.assign_seats()
            customer_id, session_token = self.login()
            payment_id = self.make_payment(customer_id, session_token)
            status, error = self.check_status(payment_id)
        except Exception as E:
            azure_obj.upload_data_to_blob_storage(self.request.data['MysAzureConfig'],
                                                  self.request.data['SearchIdentifier'],
                                                  self.blobs_list)

            return {'Message': 'Booking failed',
                    'BookStatus': 2}

        response_dict = self.book_response()

        if status == 'Declined':
            response_dict['Message'] = 'payment failed'
            response_dict['BookStatus'] = 2
            self.blobs_list.append(API_data(str(response_dict), 'Book', 'FR1', 'response'))
            azure_obj.upload_data_to_blob_storage(self.request.data['MysAzureConfig'],
                                                  self.request.data['SearchIdentifier'],
                                                  self.blobs_list)
            return {
                'Message':'payment failed',
                'BookStatus': 2
            }

        PNR = self.get_trip_overview(customer_id)

        response_dict['PNR'] = PNR
        response_dict['Message'] = 'SUCCESS'
        self.blobs_list.append(API_data(str(response_dict), 'Book', 'FR1', 'response'))
        self.save_booking(response_dict)
        azure_obj.upload_data_to_blob_storage(self.request.data['MysAzureConfig'],
                                              self.request.data['SearchIdentifier'],
                                              self.blobs_list)
        return response_dict

    def save_booking(self, response):
        endpoint = 'https://ryanbooking.default-626251809c40d7000131dba0.mystifly.facets.cloud/api/addBookDetails'
        payload = {
            "searchID": self.request.data['SearchIdentifier'],
            "createdBy":self.booking_email,
            "bookResponse": str(response),
            "metaData":"",
            "status":1,
            "supplierCode":"FR1"
        }
        requests.post(url=endpoint,
                      json=payload)

    def send_get_request(self, headers, endpoint, params):
        status = 0
        if settings.USE_PACKETSTREAM_PROXY:
            proxy = settings.PROXYDICT

            response = requests.get(url=endpoint,
                                    headers=headers,
                                    params=params,
                                    proxies=proxy
                                    )
            status = response.status_code

        if settings.USE_TTPROXY and status != 200:
            proxies = get_proxy()
            for ip in proxies:
                proxy = {
                    "http": "http://" + ip,
                }
                response = requests.get(url=endpoint,
                                        headers=headers,
                                        params=params,
                                        proxies=proxy
                                        )
                status = response.status_code
                if status == 200:
                    break

        return response

    def send_post_request(self, headers, endpoint, payload):
        status = 0
        if settings.USE_PACKETSTREAM_PROXY:
            proxy = settings.PROXYDICT

            response = requests.post(url=endpoint,
                                     headers=headers,
                                     json=payload,
                                     proxies=proxy
                                     )
            status = response.status_code

        if settings.USE_TTPROXY and status != 200:
            proxies = get_proxy()
            for ip in proxies:
                proxy = {
                    "http": "http://" + ip,
                }
                response = requests.post(url=endpoint,
                                         headers=headers,
                                         json=payload,
                                         proxies=proxy
                                         )
                status = response.status_code
                if status == 200:
                    break

        return response

    def get_flight_fare_key(self, flights_list, target_flight_number):
        for flight in flights_list:
            current_number = flight['flightNumber'].split(' ')[1]
            if current_number == target_flight_number:
                flight_key = flight['flightKey']
                fare_key = flight['regularFare']['fareKey']
                return flight_key, fare_key

    def search(self, endpoint):
        params = {}
        url = endpoint.split('?')[0]
        params_list = endpoint.split('?')[1].split('&')
        for item in params_list:
            item = item.split('=')
            params[item[0]] = item[1]

        headers = {
            'authority': 'www.ryanair.com',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-GB,en;q=0.9',
            'cache-control': 'no-cache',
            'cookie': 'fr-correlation-id=aa0e96df-9c1c-4d88-a80f-d382c28d4b21; rid=8e863587-ac14-4d1a-9b61-d56c1f8cc403; rid.sig=OCBtG/WF9HO7H4S44kdr0XfcXA+kJve6W2utpXOBDIT63EdBUn5+RpDqRuhaa6bY+Tu3bbBQkpI1C2hWSunLnycABTeYzQYeuk0EUiWmatdlnVCGxlIOEeKF2lkSSHwP5gvXIX5ElXnTnseyguZ1R9Z12ZIcgWyfhkVaG0FpyQoTtHC7FVeC++0KHFu/hWdwZVxr5SJqxN/fpO6TujlEHmj5vG/lZKkR3MSK1rQtnd1CnVxbQmoDXURKrTsz3070JIyrQNG66lIfChRh9AN3i57rWEh8u/wPhqD+rZy+S+kshVBid/XjRJB7g0oH+Q8hGr+8kn0gvdTXVlIRKM3h4c1jrOBb0inw3fMcSjS09ijsgzHRIcFf9A5dzvwBbvkFxSCbZLvHiqVLaY0qAcsLRTzqUOb7i1C2salwM+BIOX+1K4iTSDxO/AnGg++b3az3rScxKpMC2Atd5c1dXo2SFwn8CqjSXPbcMTpUamK0E3VoiYVW8VzuZiMsjII9ML9P; mkt=/gb/en/; _ga=GA1.2.414779126.1686225157; _gid=GA1.2.1247334694.1686225157; _gat_gtag_UA_153938230_2=1; myRyanairID=; STORAGE_PREFERENCES={"STRICTLY_NECESSARY":true,"PERFORMANCE":true,"FUNCTIONAL":true,"TARGETING":true,"SOCIAL_MEDIA":true,"PIXEL":true,"GANALYTICS":true,"__VERSION":2}; RY_COOKIE_CONSENT=true; bid_FRwdAp7a9G2cnLnTsgyBNeduseKcPcRy=12df2582-aadc-456d-99be-ea51f8c7a44c',
            'pragma': 'no-cache',
            # 'referer': 'https://www.ryanair.com/gb/en/trip/flights/select?adults=2&teens=0&children=0&infants=0&dateOut=2023-07-04&dateIn=2023-07-08&isConnectedFlight=false&isReturn=true&discount=0&promoCode=&originIata=STN&destinationIata=DUB&tpAdults=2&tpTeens=0&tpChildren=0&tpInfants=0&tpStartDate=2023-07-04&tpEndDate=2023-07-08&tpDiscount=0&tpPromoCode=&tpOriginIata=STN&tpDestinationIata=DUB',
            'sec-ch-ua': '"Chromium";v="113", "Not-A.Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
        }
        response = self.send_get_request(headers,url, params)

        self.blobs_list.append(API_data(str(params), 'Book/search', 'FR1', 'request'))
        self.blobs_list.append(API_data(response.text, 'Book/search', 'FR1', 'response'))

        response = json.loads(response.text)
        return response

    def get_keys(self):
        keys = {'departure_flight_key': '',
                'departure_fare_key': '',
                'return_flight_key': '',
                'return_fare_key': ''}

        subscriber = self.request.user.subscriber
        last_history_obj = SubscriberSearchHistory.objects.filter(subscriber=subscriber).last()
        search_url = last_history_obj.url

        search_response = self.search(search_url)

        departure_flight_number = self.request.data['ListFlightSegments'][0]['FlightNumber']
        departure_flights_list = search_response['trips'][0]['dates'][2]['flights']
        keys['departure_flight_key'], keys['departure_fare_key'] = self.get_flight_fare_key(departure_flights_list,
                                                                                            departure_flight_number)
        if self.is_return == 2:
            return_flight_number = self.request.data['ListFlightSegments'][1]['FlightNumber']
            return_flights_list = search_response['trips'][1]['dates'][2]['flights']
            keys['return_flight_key'], keys['return_fare_key'] = self.get_flight_fare_key(return_flights_list,
                                                                                          return_flight_number)

        return keys

    def create_basket(self):

        headers = {
            'authority': 'www.ryanair.com',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'cache-control': 'no-cache',
            'content-type': 'application/json',
            'cookie': 'rid=20736901-bf16-4fbb-8068-21900ff0c319; rid.sig=OCBtG/WF9HO7H4S44kdr0Q9YRbVRlLmXHl+JC3DAPukifYQYRB1Zw4pnTmQP/uv4ok+wW2OKV/dXM2dBUIRSymQcMGFzmspSbLdnXWidLlCuhX/QYdbuaI/s/5rX383WZ7ACymT4jGW+VrgDiomFwbyrvfMOMs8DOY5wtgFylphQewNdLLnZoUkIuE47aiWkXWIVwCeSpPaexSvaf9FrA7N9KIun91c4rgWNU9sGctaApLfI3c69thJinJcsCzuvcQh4HiL6OhXsLaIwtJycZ3prQHuKBnGEQfXmsYjIxoeOhIXscO18H5Xux5eDMdWLm8aBXosEdfUL/cPGJyGkZs3ufJAkHwxfpHtGpzZT8/SQ1SFj2cCVEywianoaJ7/Zodu6bg631JR1lBflyOJnqdk/1YItsCcC5y+yYTYedJ9pMB9ikhYlb3qA/ZVCVYLmqE6SEJQKDPDz6ZE5P23knQKKQFUWF/vfLw8NdZ8EA2m4LS2gF+zcFfF0f8hYheqDZ1RqrQTVy30BiNWhQkfl/A==; mkt=/gb/en/; fr-visit-id=25cf8c86-cec1-480c-8305-995c9f6a7d19; _ga=GA1.2.148026902.1675340460; STORAGE_PREFERENCES={"STRICTLY_NECESSARY":true,"PERFORMANCE":true,"FUNCTIONAL":true,"TARGETING":true,"SOCIAL_MEDIA":true,"PIXEL":true,"GANALYTICS":true,"__VERSION":2}; RY_COOKIE_CONSENT=true; bid_FRwdAp7a9G2cnLnTsgyBNeduseKcPcRy=658daf5c-797b-44d6-8935-d1c6de0568e8; RYANSESSION=Y9uqvwqhAm0AAFcgRUEAAAA7; _hjSessionUser_135144=eyJpZCI6IjMzMWE0Nzk1LTM5MzgtNWU5Ny1iYzY2LWM5ZGVhMzljN2JiZiIsImNyZWF0ZWQiOjE2NzUzNDA0NjEzMDcsImV4aXN0aW5nIjp0cnVlfQ==; agso=AQGewQwBAO9_ugEYBdtImQVi15IAl2k.; agsd=UaYSR_UKOM1tji40TZjzmKmN3POlgQFhaTSnz78WxEFTTO1u; agsn=h08Cz47eVZiWMjXAL8ctx8xh_RRzcxE1TpPcobm9pOc.; _cc=AYYTDLGQSwQwCkV22mxyzVLJ; _gcl_au=1.1.392399247.1677754258; fr-correlation-id=e8e522be-137e-48bb-966a-d0b7d1c8bdd4; fr-correlation-id.sig=ZMGcLW4B1zeAZ877ZsZBM0WrX9s; _gid=GA1.2.1511342970.1684926721; ADRUM=s=1684987541895&r=https%3A%2F%2Fcarhire.ryanair.com%2Fin-path%3Fhash%3D931663984; _cid_cc=AYYTDLGQSwQwCkV22mxyzVLJ; aws-waf-token=f47c0f2f-23f3-46d7-a15a-87799afc3ea9:BQoAZUMne48AAAAA:+GEAwRUbP86bRHWP5AWCJp8jN63IpeW9g46v5AdioRpU3eQnDv9Lnew+w2zLgEqBXXtVM4WOmHDUmdWpH/xgt00lrahgZ+i3nXAj6o+fUinmDJ9vwOgX0SrLrK9IgykSUZMmTqjAKWMJsZwWY6Idbh3Bz9L8NzfcVP8AowGcaJe8lfthoA==; myRyanairID=; agssn=AWKn6IwBANbBvQRxXttIQjhucQ..; .AspNetCore.Session=CfDJ8PZ1DANKhmxClKE0rZjt5S1lwrhFFXKu%2BncVo%2FBJVOS67h08hIa%2F4bVTT4JgJleJPzlBosMPqcOAHphwdg01h7aLu7ap7VrfJXS%2B%2FFMGA1EvOPz4%2BU2hDBjnaXApNblUDtAEMdpxcbFAxO%2FgyTRkeGVKATfOT5IPUI1CIrMsdb%2Fi; agsd=c9ViDjC8QdlyrrsWuec351P3yezVJvMdFEhNswfoMVOKwQ33',
            'origin': 'https://www.ryanair.com',
            'pragma': 'no-cache',
            # 'referer': 'https://www.ryanair.com/gb/en/trip/flights/select?adults=2&teens=0&children=0&infants=0&dateOut=2023-06-02&dateIn=2023-06-04&isConnectedFlight=false&isReturn=true&discount=0&promoCode=&originIata=STN&destinationIata=BUD&tpAdults=2&tpTeens=0&tpChildren=0&tpInfants=0&tpStartDate=2023-06-02&tpEndDate=2023-06-04&tpDiscount=0&tpPromoCode=&tpOriginIata=STN&tpDestinationIata=BUD',
            'sec-ch-ua': '"Chromium";v="113", "Not-A.Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
        }

        json_data = {
            'query': 'mutation CreateBasket {\n  createBasket {\n    ...BasketCommon\n    gettingAround {\n      ...GettingAroundPillar\n    }\n    thingsToDo {\n      ...ThingsToDoPillar\n    }\n  }\n}\n\n\nfragment TotalCommon on PriceType {\n  total\n}\n\nfragment PriceCommon on PriceType {\n  amountWithTaxes\n  total\n  discount\n  discountCode\n}\n\nfragment ComponentCommon on ComponentType {\n  id\n  parentId\n  code\n  type\n  quantity\n  removable\n  price {\n    ...PriceCommon\n  }\n}\n\nfragment VariantUnionAddOn on VariantUnionType {\n  ... on AddOn {\n    itemId\n    provider\n    paxNumber\n    pax\n    src\n    start\n    end\n  }\n}\n\nfragment VariantUnionFare on VariantUnionType {\n  ... on Fare {\n    fareOption\n    journeyNumber\n  }\n}\n\nfragment VariantUnionSsr on VariantUnionType {\n  ... on Ssr {\n    journeyNumber\n    paxNumber\n    segmentNumber\n  }\n}\n\nfragment VariantUnionSeat on VariantUnionType {\n  ... on Seat {\n    paxNumber\n    journeyNumber\n    segmentNumber\n    seatType\n    designator\n    childSeatsWithAdult\n    hasAdditionalSeatCost\n  }\n}\n\nfragment VariantUnionBundle on VariantUnionType {\n  ... on Bundle {\n    journeyNumber\n    segmentNumber\n  }\n}\n\nfragment VariantUnionVoucher on VariantUnionType {\n  ... on Voucher {\n    firstName\n    lastName\n    email\n  }\n}\n\nfragment VariantUnionPhysicalVoucher on VariantUnionType {\n  ... on PhysicalVoucher {\n    sequenceNumber\n    firstName\n    lastName\n    address1\n    address2\n    city\n    postalCode\n    country\n    countryName\n    scheduleDate\n    message\n  }\n}\n\nfragment VariantUnionDigitalVoucher on VariantUnionType {\n  ... on DigitalVoucher {\n    sequenceNumber\n    firstName\n    lastName\n    email\n    theme\n    scheduleDate\n    scheduleTime\n    message\n  }\n}\n\nfragment VariantGroundTransfer on VariantUnionType {\n  ... on GroundTransfer {\n    locationPickUp\n    locationDropOff\n    routeType\n    startDate\n    endDate\n    itemId\n    location\n  }\n}\n\nfragment GettingTherePillar on GettingThereType {\n  price {\n    ...TotalCommon\n  }\n  journeys {\n    ... on JourneyType {\n      arrival\n      departure\n      destination\n      duration\n      fareClass\n      fareKey\n      fareOption\n      flightKey\n      flightNumber\n      isConnecting\n      isDomestic\n      journeyNum\n      origin\n      segments {\n        ... on SegmentType {\n          aircraft\n          arrival\n          departure\n          destination\n          duration\n          hasGovernmentTax\n          flightNumber\n          segmentNum\n          origin\n          originCountry\n          destinationCountry\n        }\n      }\n    }\n  }\n  discounts {\n    ... on DiscountType {\n      amount\n      code\n      journeyNum\n      percentage\n      zone\n      description\n      qty\n    }\n  }\n  taxes {\n    ... on TaxType {\n      amount\n      code\n      journeyNum\n      percentage\n      zone\n    }\n  }\n  vouchers {\n    ... on VoucherType {\n      amount\n      code\n      status\n      accountNumber\n    }\n  }\n  components {\n    ... on ComponentType {\n      ...ComponentCommon\n      variant {\n        ...VariantUnionAddOn\n        ...VariantUnionFare\n        ...VariantUnionSsr\n        ...VariantUnionSeat\n        ...VariantGroundTransfer\n        ...VariantUnionBundle\n        ...VariantUnionVoucher\n        ...VariantUnionDigitalVoucher\n        ...VariantUnionPhysicalVoucher\n      }\n    }\n  }\n  messages {\n    ... on MessageType {\n      type\n      journeyNum\n      key\n      message\n    }\n  }\n}\n\nfragment StayingTherePillar on StayingThereType {\n  price {\n    ...TotalCommon\n  }\n  components {\n    ...ComponentCommon\n    price {\n      ...PriceCommon\n      fat\n      amount\n    }\n    payLater {\n      ...PriceCommon\n      fat\n      amount\n    }\n    variant {\n      ... on Hotel {\n        hotelName\n        reservationDescription\n        countryCode\n        city\n        startDate\n        endDate\n        provider\n        propertySurcharges {\n          ... on PropertySurcharges {\n            type\n            price\n          }\n        }\n        guestTotals {\n          adults\n          children\n        }\n        reservationInfo {\n          rooms {\n            ... on HotelRoomReservationInfo {\n              roomAllocation {\n                adultCount\n                childAges\n              }\n            }\n          }\n        }\n      }\n    }\n  }\n  payLater {\n    total\n  }\n}\n\nfragment PayLaterCommon on PriceType {\n  total\n}\n\nfragment BasketCommon on BasketType {\n  id\n  tripId\n  dotrezSessionId\n  currency\n  gettingThere {\n    ...GettingTherePillar\n  }\n  stayingThere {\n    ...StayingTherePillar\n  }\n  price {\n    ...TotalCommon\n  }\n  payLater {\n    ...PayLaterCommon\n  }\n  totalToPay\n}\n\nfragment VariantCar on VariantUnionType {\n  ... on Car {\n    rentPrice\n    carName\n    refId\n    engineLoadId\n    pickUpTime\n    pickUpLocation {\n      countryCode\n      code\n      name\n    }\n    dropOffTime\n    dropOffLocation {\n      countryCode\n      code\n      name\n    }\n    insurance\n    extras {\n      totalPrice\n      includedInRate\n      code\n      price\n      selected\n      type\n    }\n    residence\n    age\n  }\n}\n\nfragment VariantCarRental on VariantUnionType {\n  ... on CarRental {\n    rentPrice\n    carName\n    clientId\n    refId\n    pickUpTime\n    pickUpLocation {\n      countryCode\n      code\n      name\n    }\n    dropOffTime\n    dropOffLocation {\n      countryCode\n      code\n      name\n    }\n    insurance\n    extras {\n      totalPrice\n      includedInRate\n      code\n      price\n      selected\n      type\n      payNow\n    }\n    residence\n    age\n    searchId\n  }\n}\n\nfragment GettingAroundPillar on GettingAroundType {\n  price {\n    amount\n    discount\n    amountWithTaxes\n    total\n  }\n  payLater {\n    ...PayLaterCommon\n  }\n  taxes {\n    amount\n  }\n  components {\n    ...ComponentCommon\n    payLater {\n      amountWithTaxes\n      total\n    }\n    variant {\n      ...VariantCar\n      ...VariantCarRental\n      ...VariantGroundTransfer\n    }\n  }\n}\n\nfragment ThingsToDoPillar on ThingsToDoType {\n  price {\n    amount\n    discount\n    amountWithTaxes\n    total\n  }\n  taxes {\n    amount\n  }\n  components {\n    ...ComponentCommon\n    variant {\n      ... on Ticket {\n        name\n        reservationCode\n        activityTime\n        address\n      }\n    }\n  }\n}\n\n',
            'operationName': 'CreateBasket',
        }

        endpoint = 'https://www.ryanair.com/api/basketapi/en-gb/graphql'

        response = self.send_post_request(headers, endpoint, json_data)

        self.blobs_list.append(API_data(str(json_data), 'Book/create_basket', 'FR1', 'request'))
        self.blobs_list.append(API_data(response.text, 'Book/create_basket', 'FR1', 'response'))

        response = json.loads(response.text)
        basket_id = response['data']['createBasket']['id']

        return basket_id

    def create_booking(self, keys):

        headers = {
            'authority': 'www.ryanair.com',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'cache-control': 'no-cache',
            'content-type': 'application/json',
            'cookie': 'rid=20736901-bf16-4fbb-8068-21900ff0c319; rid.sig=OCBtG/WF9HO7H4S44kdr0Q9YRbVRlLmXHl+JC3DAPukifYQYRB1Zw4pnTmQP/uv4ok+wW2OKV/dXM2dBUIRSymQcMGFzmspSbLdnXWidLlCuhX/QYdbuaI/s/5rX383WZ7ACymT4jGW+VrgDiomFwbyrvfMOMs8DOY5wtgFylphQewNdLLnZoUkIuE47aiWkXWIVwCeSpPaexSvaf9FrA7N9KIun91c4rgWNU9sGctaApLfI3c69thJinJcsCzuvcQh4HiL6OhXsLaIwtJycZ3prQHuKBnGEQfXmsYjIxoeOhIXscO18H5Xux5eDMdWLm8aBXosEdfUL/cPGJyGkZs3ufJAkHwxfpHtGpzZT8/SQ1SFj2cCVEywianoaJ7/Zodu6bg631JR1lBflyOJnqdk/1YItsCcC5y+yYTYedJ9pMB9ikhYlb3qA/ZVCVYLmqE6SEJQKDPDz6ZE5P23knQKKQFUWF/vfLw8NdZ8EA2m4LS2gF+zcFfF0f8hYheqDZ1RqrQTVy30BiNWhQkfl/A==; mkt=/gb/en/; fr-visit-id=25cf8c86-cec1-480c-8305-995c9f6a7d19; _ga=GA1.2.148026902.1675340460; STORAGE_PREFERENCES={"STRICTLY_NECESSARY":true,"PERFORMANCE":true,"FUNCTIONAL":true,"TARGETING":true,"SOCIAL_MEDIA":true,"PIXEL":true,"GANALYTICS":true,"__VERSION":2}; RY_COOKIE_CONSENT=true; bid_FRwdAp7a9G2cnLnTsgyBNeduseKcPcRy=658daf5c-797b-44d6-8935-d1c6de0568e8; RYANSESSION=Y9uqvwqhAm0AAFcgRUEAAAA7; _hjSessionUser_135144=eyJpZCI6IjMzMWE0Nzk1LTM5MzgtNWU5Ny1iYzY2LWM5ZGVhMzljN2JiZiIsImNyZWF0ZWQiOjE2NzUzNDA0NjEzMDcsImV4aXN0aW5nIjp0cnVlfQ==; agso=AQGewQwBAO9_ugEYBdtImQVi15IAl2k.; agsd=UaYSR_UKOM1tji40TZjzmKmN3POlgQFhaTSnz78WxEFTTO1u; agsn=h08Cz47eVZiWMjXAL8ctx8xh_RRzcxE1TpPcobm9pOc.; _cc=AYYTDLGQSwQwCkV22mxyzVLJ; _gcl_au=1.1.392399247.1677754258; fr-correlation-id=e8e522be-137e-48bb-966a-d0b7d1c8bdd4; fr-correlation-id.sig=ZMGcLW4B1zeAZ877ZsZBM0WrX9s; _gid=GA1.2.1511342970.1684926721; ADRUM=s=1684987541895&r=https%3A%2F%2Fcarhire.ryanair.com%2Fin-path%3Fhash%3D931663984; _cid_cc=AYYTDLGQSwQwCkV22mxyzVLJ; aws-waf-token=f47c0f2f-23f3-46d7-a15a-87799afc3ea9:BQoAZUMne48AAAAA:+GEAwRUbP86bRHWP5AWCJp8jN63IpeW9g46v5AdioRpU3eQnDv9Lnew+w2zLgEqBXXtVM4WOmHDUmdWpH/xgt00lrahgZ+i3nXAj6o+fUinmDJ9vwOgX0SrLrK9IgykSUZMmTqjAKWMJsZwWY6Idbh3Bz9L8NzfcVP8AowGcaJe8lfthoA==; myRyanairID=; agssn=AWKn6IwBANbBvQRxXttIQjhucQ..; .AspNetCore.Session=CfDJ8PZ1DANKhmxClKE0rZjt5S1lwrhFFXKu%2BncVo%2FBJVOS67h08hIa%2F4bVTT4JgJleJPzlBosMPqcOAHphwdg01h7aLu7ap7VrfJXS%2B%2FFMGA1EvOPz4%2BU2hDBjnaXApNblUDtAEMdpxcbFAxO%2FgyTRkeGVKATfOT5IPUI1CIrMsdb%2Fi; agsd=c9ViDjC8QdlyrrsWuec351P3yezVJvMdFEhNswfoMVOKwQ33',
            'origin': 'https://www.ryanair.com',
            'pragma': 'no-cache',
            # 'referer': 'https://www.ryanair.com/gb/en/trip/flights/select?adults=2&teens=0&children=0&infants=0&dateOut=2023-06-02&dateIn=2023-06-04&isConnectedFlight=false&isReturn=true&discount=0&promoCode=&originIata=STN&destinationIata=BUD&tpAdults=2&tpTeens=0&tpChildren=0&tpInfants=0&tpStartDate=2023-06-02&tpEndDate=2023-06-04&tpDiscount=0&tpPromoCode=&tpOriginIata=STN&tpDestinationIata=BUD',
            'sec-ch-ua': '"Chromium";v="113", "Not-A.Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
        }

        json_data = {
            'query': 'mutation CreateBooking($basketId: String, $createBooking: CreateBookingInput!, $culture: String!) {\n  createBooking(basketId: $basketId, createBooking: $createBooking, culture: $culture) {\n    ...BasketCommon\n  }\n}\n\n\nfragment TotalCommon on PriceType {\n  total\n}\n\nfragment PriceCommon on PriceType {\n  amountWithTaxes\n  total\n  discount\n  discountCode\n}\n\nfragment ComponentCommon on ComponentType {\n  id\n  parentId\n  code\n  type\n  quantity\n  removable\n  price {\n    ...PriceCommon\n  }\n}\n\nfragment VariantUnionAddOn on VariantUnionType {\n  ... on AddOn {\n    itemId\n    provider\n    paxNumber\n    pax\n    src\n    start\n    end\n  }\n}\n\nfragment VariantUnionFare on VariantUnionType {\n  ... on Fare {\n    fareOption\n    journeyNumber\n  }\n}\n\nfragment VariantUnionSsr on VariantUnionType {\n  ... on Ssr {\n    journeyNumber\n    paxNumber\n    segmentNumber\n  }\n}\n\nfragment VariantUnionSeat on VariantUnionType {\n  ... on Seat {\n    paxNumber\n    journeyNumber\n    segmentNumber\n    seatType\n    designator\n    childSeatsWithAdult\n    hasAdditionalSeatCost\n  }\n}\n\nfragment VariantUnionBundle on VariantUnionType {\n  ... on Bundle {\n    journeyNumber\n    segmentNumber\n  }\n}\n\nfragment VariantUnionVoucher on VariantUnionType {\n  ... on Voucher {\n    firstName\n    lastName\n    email\n  }\n}\n\nfragment VariantUnionPhysicalVoucher on VariantUnionType {\n  ... on PhysicalVoucher {\n    sequenceNumber\n    firstName\n    lastName\n    address1\n    address2\n    city\n    postalCode\n    country\n    countryName\n    scheduleDate\n    message\n  }\n}\n\nfragment VariantUnionDigitalVoucher on VariantUnionType {\n  ... on DigitalVoucher {\n    sequenceNumber\n    firstName\n    lastName\n    email\n    theme\n    scheduleDate\n    scheduleTime\n    message\n  }\n}\n\nfragment VariantGroundTransfer on VariantUnionType {\n  ... on GroundTransfer {\n    locationPickUp\n    locationDropOff\n    routeType\n    startDate\n    endDate\n    itemId\n    location\n  }\n}\n\nfragment GettingTherePillar on GettingThereType {\n  price {\n    ...TotalCommon\n  }\n  journeys {\n    ... on JourneyType {\n      arrival\n      departure\n      destination\n      duration\n      fareClass\n      fareKey\n      fareOption\n      flightKey\n      flightNumber\n      isConnecting\n      isDomestic\n      journeyNum\n      origin\n      segments {\n        ... on SegmentType {\n          aircraft\n          arrival\n          departure\n          destination\n          duration\n          hasGovernmentTax\n          flightNumber\n          segmentNum\n          origin\n          originCountry\n          destinationCountry\n        }\n      }\n    }\n  }\n  discounts {\n    ... on DiscountType {\n      amount\n      code\n      journeyNum\n      percentage\n      zone\n      description\n      qty\n    }\n  }\n  taxes {\n    ... on TaxType {\n      amount\n      code\n      journeyNum\n      percentage\n      zone\n    }\n  }\n  vouchers {\n    ... on VoucherType {\n      amount\n      code\n      status\n      accountNumber\n    }\n  }\n  components {\n    ... on ComponentType {\n      ...ComponentCommon\n      variant {\n        ...VariantUnionAddOn\n        ...VariantUnionFare\n        ...VariantUnionSsr\n        ...VariantUnionSeat\n        ...VariantGroundTransfer\n        ...VariantUnionBundle\n        ...VariantUnionVoucher\n        ...VariantUnionDigitalVoucher\n        ...VariantUnionPhysicalVoucher\n      }\n    }\n  }\n  messages {\n    ... on MessageType {\n      type\n      journeyNum\n      key\n      message\n    }\n  }\n}\n\nfragment StayingTherePillar on StayingThereType {\n  price {\n    ...TotalCommon\n  }\n  components {\n    ...ComponentCommon\n    price {\n      ...PriceCommon\n      fat\n      amount\n    }\n    payLater {\n      ...PriceCommon\n      fat\n      amount\n    }\n    variant {\n      ... on Hotel {\n        hotelName\n        reservationDescription\n        countryCode\n        city\n        startDate\n        endDate\n        provider\n        propertySurcharges {\n          ... on PropertySurcharges {\n            type\n            price\n          }\n        }\n        guestTotals {\n          adults\n          children\n        }\n        reservationInfo {\n          rooms {\n            ... on HotelRoomReservationInfo {\n              roomAllocation {\n                adultCount\n                childAges\n              }\n            }\n          }\n        }\n      }\n    }\n  }\n  payLater {\n    total\n  }\n}\n\nfragment PayLaterCommon on PriceType {\n  total\n}\n\nfragment BasketCommon on BasketType {\n  id\n  tripId\n  dotrezSessionId\n  currency\n  gettingThere {\n    ...GettingTherePillar\n  }\n  stayingThere {\n    ...StayingTherePillar\n  }\n  price {\n    ...TotalCommon\n  }\n  payLater {\n    ...PayLaterCommon\n  }\n  totalToPay\n}\n\n',
            'variables': {
                'basketId': self.basket_id,
                'createBooking': {
                    'adults': len(self.request.data['ListPassengers']),
                    'children': 0,
                    'infants': 0,
                    'teens': 0,
                    'flights': [
                        {
                            'fareKey': keys['departure_fare_key'],
                            'flightKey': keys['departure_flight_key'],
                            'fareOption': None,
                        }
                    ],
                    'discount': 0,
                    'promoCode': '',
                },
                'culture': 'en-gb',
            },
            'operationName': 'CreateBooking',
        }

        if self.is_return == 2:
            return_data = {
                            'fareKey': keys['return_fare_key'],
                            'flightKey': keys['return_flight_key'],
                            'fareOption': None,
                        }
            json_data['variables']['createBooking']['flights'].append(return_data)

        endpoint = 'https://www.ryanair.com/api/basketapi/en-gb/graphql'
        response = self.send_post_request(headers, endpoint, json_data)

        self.blobs_list.append(API_data(str(json_data), 'Book/create_booking', 'FR1', 'request'))
        self.blobs_list.append(API_data(response.text, 'Book/create_booking', 'FR1', 'response'))

    def commit_booking(self):
        headers = {
            'authority': 'www.ryanair.com',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'cache-control': 'no-cache',
            'content-type': 'application/json',
            'cookie': 'rid=20736901-bf16-4fbb-8068-21900ff0c319; rid.sig=OCBtG/WF9HO7H4S44kdr0Q9YRbVRlLmXHl+JC3DAPukifYQYRB1Zw4pnTmQP/uv4ok+wW2OKV/dXM2dBUIRSymQcMGFzmspSbLdnXWidLlCuhX/QYdbuaI/s/5rX383WZ7ACymT4jGW+VrgDiomFwbyrvfMOMs8DOY5wtgFylphQewNdLLnZoUkIuE47aiWkXWIVwCeSpPaexSvaf9FrA7N9KIun91c4rgWNU9sGctaApLfI3c69thJinJcsCzuvcQh4HiL6OhXsLaIwtJycZ3prQHuKBnGEQfXmsYjIxoeOhIXscO18H5Xux5eDMdWLm8aBXosEdfUL/cPGJyGkZs3ufJAkHwxfpHtGpzZT8/SQ1SFj2cCVEywianoaJ7/Zodu6bg631JR1lBflyOJnqdk/1YItsCcC5y+yYTYedJ9pMB9ikhYlb3qA/ZVCVYLmqE6SEJQKDPDz6ZE5P23knQKKQFUWF/vfLw8NdZ8EA2m4LS2gF+zcFfF0f8hYheqDZ1RqrQTVy30BiNWhQkfl/A==; mkt=/gb/en/; fr-visit-id=25cf8c86-cec1-480c-8305-995c9f6a7d19; _ga=GA1.2.148026902.1675340460; STORAGE_PREFERENCES={"STRICTLY_NECESSARY":true,"PERFORMANCE":true,"FUNCTIONAL":true,"TARGETING":true,"SOCIAL_MEDIA":true,"PIXEL":true,"GANALYTICS":true,"__VERSION":2}; RY_COOKIE_CONSENT=true; bid_FRwdAp7a9G2cnLnTsgyBNeduseKcPcRy=658daf5c-797b-44d6-8935-d1c6de0568e8; RYANSESSION=Y9uqvwqhAm0AAFcgRUEAAAA7; _hjSessionUser_135144=eyJpZCI6IjMzMWE0Nzk1LTM5MzgtNWU5Ny1iYzY2LWM5ZGVhMzljN2JiZiIsImNyZWF0ZWQiOjE2NzUzNDA0NjEzMDcsImV4aXN0aW5nIjp0cnVlfQ==; agso=AQGewQwBAO9_ugEYBdtImQVi15IAl2k.; agsd=UaYSR_UKOM1tji40TZjzmKmN3POlgQFhaTSnz78WxEFTTO1u; agsn=h08Cz47eVZiWMjXAL8ctx8xh_RRzcxE1TpPcobm9pOc.; _cc=AYYTDLGQSwQwCkV22mxyzVLJ; _gcl_au=1.1.392399247.1677754258; fr-correlation-id=e8e522be-137e-48bb-966a-d0b7d1c8bdd4; fr-correlation-id.sig=ZMGcLW4B1zeAZ877ZsZBM0WrX9s; _gid=GA1.2.1511342970.1684926721; ADRUM=s=1684987541895&r=https%3A%2F%2Fcarhire.ryanair.com%2Fin-path%3Fhash%3D931663984; _cid_cc=AYYTDLGQSwQwCkV22mxyzVLJ; aws-waf-token=f47c0f2f-23f3-46d7-a15a-87799afc3ea9:BQoAZUMne48AAAAA:+GEAwRUbP86bRHWP5AWCJp8jN63IpeW9g46v5AdioRpU3eQnDv9Lnew+w2zLgEqBXXtVM4WOmHDUmdWpH/xgt00lrahgZ+i3nXAj6o+fUinmDJ9vwOgX0SrLrK9IgykSUZMmTqjAKWMJsZwWY6Idbh3Bz9L8NzfcVP8AowGcaJe8lfthoA==; myRyanairID=; .AspNetCore.Session=CfDJ8PZ1DANKhmxClKE0rZjt5S1lwrhFFXKu%2BncVo%2FBJVOS67h08hIa%2F4bVTT4JgJleJPzlBosMPqcOAHphwdg01h7aLu7ap7VrfJXS%2B%2FFMGA1EvOPz4%2BU2hDBjnaXApNblUDtAEMdpxcbFAxO%2FgyTRkeGVKATfOT5IPUI1CIrMsdb%2Fi; agssn=AY3OZBgBAKuLrkF6XttIb-qjdQ..; _gat_gtag_UA_153938230_2=1; agsd=c9ViDjC8QdlyrrsWuec351P3yezVJvMdFEhNswfoMVOKwQ33',
            'origin': 'https://www.ryanair.com',
            'pragma': 'no-cache',
            # 'referer': 'https://www.ryanair.com/gb/en/trip/flights/select?adults=2&teens=0&children=0&infants=0&dateOut=2023-06-02&dateIn=2023-06-04&isConnectedFlight=false&isReturn=true&discount=0&promoCode=&originIata=STN&destinationIata=BUD&tpAdults=2&tpTeens=0&tpChildren=0&tpInfants=0&tpStartDate=2023-06-02&tpEndDate=2023-06-04&tpDiscount=0&tpPromoCode=&tpOriginIata=STN&tpDestinationIata=BUD',
            'sec-ch-ua': '"Chromium";v="113", "Not-A.Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
        }
        json_data = {
            'query': 'mutation CommitBooking($basketId: String!) {\n  commitBooking(basketId: $basketId) {\n    ...BasketCommon\n  }\n}\n\n\nfragment TotalCommon on PriceType {\n  total\n}\n\nfragment PriceCommon on PriceType {\n  amountWithTaxes\n  total\n  discount\n  discountCode\n}\n\nfragment ComponentCommon on ComponentType {\n  id\n  parentId\n  code\n  type\n  quantity\n  removable\n  price {\n    ...PriceCommon\n  }\n}\n\nfragment VariantUnionAddOn on VariantUnionType {\n  ... on AddOn {\n    itemId\n    provider\n    paxNumber\n    pax\n    src\n    start\n    end\n  }\n}\n\nfragment VariantUnionFare on VariantUnionType {\n  ... on Fare {\n    fareOption\n    journeyNumber\n  }\n}\n\nfragment VariantUnionSsr on VariantUnionType {\n  ... on Ssr {\n    journeyNumber\n    paxNumber\n    segmentNumber\n  }\n}\n\nfragment VariantUnionSeat on VariantUnionType {\n  ... on Seat {\n    paxNumber\n    journeyNumber\n    segmentNumber\n    seatType\n    designator\n    childSeatsWithAdult\n    hasAdditionalSeatCost\n  }\n}\n\nfragment VariantUnionBundle on VariantUnionType {\n  ... on Bundle {\n    journeyNumber\n    segmentNumber\n  }\n}\n\nfragment VariantUnionVoucher on VariantUnionType {\n  ... on Voucher {\n    firstName\n    lastName\n    email\n  }\n}\n\nfragment VariantUnionPhysicalVoucher on VariantUnionType {\n  ... on PhysicalVoucher {\n    sequenceNumber\n    firstName\n    lastName\n    address1\n    address2\n    city\n    postalCode\n    country\n    countryName\n    scheduleDate\n    message\n  }\n}\n\nfragment VariantUnionDigitalVoucher on VariantUnionType {\n  ... on DigitalVoucher {\n    sequenceNumber\n    firstName\n    lastName\n    email\n    theme\n    scheduleDate\n    scheduleTime\n    message\n  }\n}\n\nfragment VariantGroundTransfer on VariantUnionType {\n  ... on GroundTransfer {\n    locationPickUp\n    locationDropOff\n    routeType\n    startDate\n    endDate\n    itemId\n    location\n  }\n}\n\nfragment GettingTherePillar on GettingThereType {\n  price {\n    ...TotalCommon\n  }\n  journeys {\n    ... on JourneyType {\n      arrival\n      departure\n      destination\n      duration\n      fareClass\n      fareKey\n      fareOption\n      flightKey\n      flightNumber\n      isConnecting\n      isDomestic\n      journeyNum\n      origin\n      segments {\n        ... on SegmentType {\n          aircraft\n          arrival\n          departure\n          destination\n          duration\n          hasGovernmentTax\n          flightNumber\n          segmentNum\n          origin\n          originCountry\n          destinationCountry\n        }\n      }\n    }\n  }\n  discounts {\n    ... on DiscountType {\n      amount\n      code\n      journeyNum\n      percentage\n      zone\n      description\n      qty\n    }\n  }\n  taxes {\n    ... on TaxType {\n      amount\n      code\n      journeyNum\n      percentage\n      zone\n    }\n  }\n  vouchers {\n    ... on VoucherType {\n      amount\n      code\n      status\n      accountNumber\n    }\n  }\n  components {\n    ... on ComponentType {\n      ...ComponentCommon\n      variant {\n        ...VariantUnionAddOn\n        ...VariantUnionFare\n        ...VariantUnionSsr\n        ...VariantUnionSeat\n        ...VariantGroundTransfer\n        ...VariantUnionBundle\n        ...VariantUnionVoucher\n        ...VariantUnionDigitalVoucher\n        ...VariantUnionPhysicalVoucher\n      }\n    }\n  }\n  messages {\n    ... on MessageType {\n      type\n      journeyNum\n      key\n      message\n    }\n  }\n}\n\nfragment StayingTherePillar on StayingThereType {\n  price {\n    ...TotalCommon\n  }\n  components {\n    ...ComponentCommon\n    price {\n      ...PriceCommon\n      fat\n      amount\n    }\n    payLater {\n      ...PriceCommon\n      fat\n      amount\n    }\n    variant {\n      ... on Hotel {\n        hotelName\n        reservationDescription\n        countryCode\n        city\n        startDate\n        endDate\n        provider\n        propertySurcharges {\n          ... on PropertySurcharges {\n            type\n            price\n          }\n        }\n        guestTotals {\n          adults\n          children\n        }\n        reservationInfo {\n          rooms {\n            ... on HotelRoomReservationInfo {\n              roomAllocation {\n                adultCount\n                childAges\n              }\n            }\n          }\n        }\n      }\n    }\n  }\n  payLater {\n    total\n  }\n}\n\nfragment PayLaterCommon on PriceType {\n  total\n}\n\nfragment BasketCommon on BasketType {\n  id\n  tripId\n  dotrezSessionId\n  currency\n  gettingThere {\n    ...GettingTherePillar\n  }\n  stayingThere {\n    ...StayingTherePillar\n  }\n  price {\n    ...TotalCommon\n  }\n  payLater {\n    ...PayLaterCommon\n  }\n  totalToPay\n}\n\n',
            'variables': {
                'basketId': self.basket_id,
            },
            'operationName': 'CommitBooking',
        }

        endpoint = 'https://www.ryanair.com/api/basketapi/en-gb/graphql'

        response = self.send_post_request(headers, endpoint, json_data)

        self.blobs_list.append(API_data(str(json_data), 'Book/commit_booking', 'FR1', 'request'))
        self.blobs_list.append(API_data(response.text, 'Book/commit_booking', 'FR1', 'response'))


    def add_passengers(self):

        headers = {
            'authority': 'www.ryanair.com',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'cache-control': 'no-cache',
            'content-type': 'application/json',
            # 'cookie': 'rid=20736901-bf16-4fbb-8068-21900ff0c319; rid.sig=OCBtG/WF9HO7H4S44kdr0Q9YRbVRlLmXHl+JC3DAPukifYQYRB1Zw4pnTmQP/uv4ok+wW2OKV/dXM2dBUIRSymQcMGFzmspSbLdnXWidLlCuhX/QYdbuaI/s/5rX383WZ7ACymT4jGW+VrgDiomFwbyrvfMOMs8DOY5wtgFylphQewNdLLnZoUkIuE47aiWkXWIVwCeSpPaexSvaf9FrA7N9KIun91c4rgWNU9sGctaApLfI3c69thJinJcsCzuvcQh4HiL6OhXsLaIwtJycZ3prQHuKBnGEQfXmsYjIxoeOhIXscO18H5Xux5eDMdWLm8aBXosEdfUL/cPGJyGkZs3ufJAkHwxfpHtGpzZT8/SQ1SFj2cCVEywianoaJ7/Zodu6bg631JR1lBflyOJnqdk/1YItsCcC5y+yYTYedJ9pMB9ikhYlb3qA/ZVCVYLmqE6SEJQKDPDz6ZE5P23knQKKQFUWF/vfLw8NdZ8EA2m4LS2gF+zcFfF0f8hYheqDZ1RqrQTVy30BiNWhQkfl/A==; mkt=/gb/en/; fr-visit-id=25cf8c86-cec1-480c-8305-995c9f6a7d19; _ga=GA1.2.148026902.1675340460; STORAGE_PREFERENCES={"STRICTLY_NECESSARY":true,"PERFORMANCE":true,"FUNCTIONAL":true,"TARGETING":true,"SOCIAL_MEDIA":true,"PIXEL":true,"GANALYTICS":true,"__VERSION":2}; RY_COOKIE_CONSENT=true; bid_FRwdAp7a9G2cnLnTsgyBNeduseKcPcRy=658daf5c-797b-44d6-8935-d1c6de0568e8; RYANSESSION=Y9uqvwqhAm0AAFcgRUEAAAA7; _hjSessionUser_135144=eyJpZCI6IjMzMWE0Nzk1LTM5MzgtNWU5Ny1iYzY2LWM5ZGVhMzljN2JiZiIsImNyZWF0ZWQiOjE2NzUzNDA0NjEzMDcsImV4aXN0aW5nIjp0cnVlfQ==; agso=AQGewQwBAO9_ugEYBdtImQVi15IAl2k.; agsd=UaYSR_UKOM1tji40TZjzmKmN3POlgQFhaTSnz78WxEFTTO1u; agsn=h08Cz47eVZiWMjXAL8ctx8xh_RRzcxE1TpPcobm9pOc.; _cc=AYYTDLGQSwQwCkV22mxyzVLJ; _gcl_au=1.1.392399247.1677754258; fr-correlation-id=e8e522be-137e-48bb-966a-d0b7d1c8bdd4; fr-correlation-id.sig=ZMGcLW4B1zeAZ877ZsZBM0WrX9s; _gid=GA1.2.1511342970.1684926721; ADRUM=s=1684987541895&r=https%3A%2F%2Fcarhire.ryanair.com%2Fin-path%3Fhash%3D931663984; _cid_cc=AYYTDLGQSwQwCkV22mxyzVLJ; aws-waf-token=f47c0f2f-23f3-46d7-a15a-87799afc3ea9:BQoAZUMne48AAAAA:+GEAwRUbP86bRHWP5AWCJp8jN63IpeW9g46v5AdioRpU3eQnDv9Lnew+w2zLgEqBXXtVM4WOmHDUmdWpH/xgt00lrahgZ+i3nXAj6o+fUinmDJ9vwOgX0SrLrK9IgykSUZMmTqjAKWMJsZwWY6Idbh3Bz9L8NzfcVP8AowGcaJe8lfthoA==; myRyanairID=; .AspNetCore.Session=CfDJ8PZ1DANKhmxClKE0rZjt5S1lwrhFFXKu%2BncVo%2FBJVOS67h08hIa%2F4bVTT4JgJleJPzlBosMPqcOAHphwdg01h7aLu7ap7VrfJXS%2B%2FFMGA1EvOPz4%2BU2hDBjnaXApNblUDtAEMdpxcbFAxO%2FgyTRkeGVKATfOT5IPUI1CIrMsdb%2Fi; agssn=AY3OZBgBAKuLrkF6XttIb-qjdQ..; agsd=c9ViDjC8QdlyrrsWuec351P3yezVJvMdFEhNswfoMVOKwQ33; .AspNetCore.Session=CfDJ8JyS2spazCRLi9BjvHl3ZOtE7ZFM7ZIb%2BZEQ3Qt81YxYkJ5u5i9bsVJnCulb17i%2Bn%2BpHZU8TOTumSYxPV%2BnYSDCR3SDBkJgYjvukRdraOvySzMNwTYAFuMgorKLHtqeHD9Sq%2FqHThcUfFTqw%2FGbH3AI04%2FBwgb7DlvG358YFonWn',
            'origin': 'https://www.ryanair.com',
            'pragma': 'no-cache',
            'referer': 'https://www.ryanair.com/gb/en/trip/flights/select?adults=2&teens=0&children=0&infants=0&dateOut=2023-06-02&dateIn=2023-06-04&isConnectedFlight=false&isReturn=true&discount=0&promoCode=&originIata=STN&destinationIata=BUD&tpAdults=2&tpTeens=0&tpChildren=0&tpInfants=0&tpStartDate=2023-06-02&tpEndDate=2023-06-04&tpDiscount=0&tpPromoCode=&tpOriginIata=STN&tpDestinationIata=BUD',
            'sec-ch-ua': '"Chromium";v="113", "Not-A.Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
        }

        json_data = {
            'query': 'mutation AddPassengers($passengers: [InputPassenger] = null, $basketId: String!) {\n  addPassengers(passengers: $passengers, basketId: $basketId) {\n    ...PassengersResponse\n  }\n}\n\nfragment PassengersResponse on PassengersResponse {\n  passengers {\n    ...PassengersPassenger\n  }\n}\n\nfragment PassengersPassenger on Passenger {\n  paxNum\n  type\n  title\n  firstName\n  firstSurname\n  secondSurname\n  first\n  last\n  middle\n  dob\n  inf {\n    ...PassengersInfant\n  }\n  specialAssistance {\n    ...PassengersPassengerPrmSsrType\n  }\n}\n\nfragment PassengersInfant on Infant {\n  firstName\n  firstSurname\n  secondSurname\n  first\n  last\n  middle\n  dob\n}\n\nfragment PassengersPassengerPrmSsrType on PassengerPrmSsrType {\n  codes\n  journeyNum\n  segmentNum\n}\n',
            'variables': {
                'passengers': [],
                'basketId': self.basket_id,
            },
        }

        passengers = self.request.data['ListPassengers']

        for i, passenger in enumerate(passengers):
            data = {
                        'type': 'ADT',
                        'dob': None,
                        'first': passenger['FirstName'],
                        'last': passenger['LastName'],
                        'middle': None,
                        'title': passenger['Title'].upper(),
                        'paxNum': i,
                        'specialAssistance': [],
                    }
            json_data['variables']['passengers'].append(data)

        endpoint = 'https://www.ryanair.com/api/personapi/en-gb/graphql'

        response = self.send_post_request(headers, endpoint, json_data)

        self.blobs_list.append(API_data(str(json_data), 'Book/add_passengers', 'FR1', 'request'))
        self.blobs_list.append(API_data(response.text, 'Book/add_passengers', 'FR1', 'response'))


    def assign_seats(self):
        headers = {
            'authority': 'www.ryanair.com',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'cache-control': 'no-cache',
            'content-type': 'application/json',
            'cookie': 'rid=20736901-bf16-4fbb-8068-21900ff0c319; rid.sig=OCBtG/WF9HO7H4S44kdr0Q9YRbVRlLmXHl+JC3DAPukifYQYRB1Zw4pnTmQP/uv4ok+wW2OKV/dXM2dBUIRSymQcMGFzmspSbLdnXWidLlCuhX/QYdbuaI/s/5rX383WZ7ACymT4jGW+VrgDiomFwbyrvfMOMs8DOY5wtgFylphQewNdLLnZoUkIuE47aiWkXWIVwCeSpPaexSvaf9FrA7N9KIun91c4rgWNU9sGctaApLfI3c69thJinJcsCzuvcQh4HiL6OhXsLaIwtJycZ3prQHuKBnGEQfXmsYjIxoeOhIXscO18H5Xux5eDMdWLm8aBXosEdfUL/cPGJyGkZs3ufJAkHwxfpHtGpzZT8/SQ1SFj2cCVEywianoaJ7/Zodu6bg631JR1lBflyOJnqdk/1YItsCcC5y+yYTYedJ9pMB9ikhYlb3qA/ZVCVYLmqE6SEJQKDPDz6ZE5P23knQKKQFUWF/vfLw8NdZ8EA2m4LS2gF+zcFfF0f8hYheqDZ1RqrQTVy30BiNWhQkfl/A==; mkt=/gb/en/; fr-visit-id=25cf8c86-cec1-480c-8305-995c9f6a7d19; _ga=GA1.2.148026902.1675340460; STORAGE_PREFERENCES={"STRICTLY_NECESSARY":true,"PERFORMANCE":true,"FUNCTIONAL":true,"TARGETING":true,"SOCIAL_MEDIA":true,"PIXEL":true,"GANALYTICS":true,"__VERSION":2}; RY_COOKIE_CONSENT=true; bid_FRwdAp7a9G2cnLnTsgyBNeduseKcPcRy=658daf5c-797b-44d6-8935-d1c6de0568e8; RYANSESSION=Y9uqvwqhAm0AAFcgRUEAAAA7; _hjSessionUser_135144=eyJpZCI6IjMzMWE0Nzk1LTM5MzgtNWU5Ny1iYzY2LWM5ZGVhMzljN2JiZiIsImNyZWF0ZWQiOjE2NzUzNDA0NjEzMDcsImV4aXN0aW5nIjp0cnVlfQ==; agso=AQGewQwBAO9_ugEYBdtImQVi15IAl2k.; agsd=UaYSR_UKOM1tji40TZjzmKmN3POlgQFhaTSnz78WxEFTTO1u; agsn=h08Cz47eVZiWMjXAL8ctx8xh_RRzcxE1TpPcobm9pOc.; _cc=AYYTDLGQSwQwCkV22mxyzVLJ; fr-correlation-id=e8e522be-137e-48bb-966a-d0b7d1c8bdd4; fr-correlation-id.sig=ZMGcLW4B1zeAZ877ZsZBM0WrX9s; _cid_cc=AYYTDLGQSwQwCkV22mxyzVLJ; _gcl_au=1.1.513928296.1685632940; ADRUM=s=1685700773021&r=https%3A%2F%2Fcarhire.ryanair.com%2Fin-path%3Fhash%3D-378896025; myRyanairID=; _gid=GA1.2.1870883775.1685942079; .AspNetCore.Session=CfDJ8H9Fg%2FLvAtlJvXQK0IhJmJH34%2B15PeUEteQ5BaEW7m4r9XBXHglC2COD5Qcl6NyLSJ2rKwXBgTo1i8pwH%2FOzKMJoFtiHePy5rVW%2FomHmYWeN2XcjIkgLx6A4yIpZ%2FnwOTYHIRV6GC%2BvZA03zhtt4RK2Qajyou33YnK0SqM%2FgXoDx; agssn=AW7GMJsBAL_5ROwsZ9tIATVy2A..; _gat_gtag_UA_153938230_2=1; agsd=c9ViDjC8QdlyrrsWuec351P3yezVJvMdFEhNswfoMVOKwQ33',
            'newrelic': 'eyJ2IjpbMCwxXSwiZCI6eyJ0eSI6IkJyb3dzZXIiLCJhYyI6IjY0NjgzMiIsImFwIjoiMzI5ODE1Nzc0IiwiaWQiOiI3YThkOGYzMDk3ODBhMWY3IiwidHIiOiI5Yjk0ODY5Y2I2NGM3MWY5M2EwYmQwMzc5NDEzYjUwMCIsInRpIjoxNjg2MTI1MjUzNDM1fX0=',
            'origin': 'https://www.ryanair.com',
            'pragma': 'no-cache',
            # 'referer': 'https://www.ryanair.com/gb/en/trip/flights/seats?tpAdults=2&tpTeens=0&tpChildren=0&tpInfants=0&tpStartDate=2023-07-05&tpEndDate=2023-07-08&tpDiscount=0&tpPromoCode=&tpOriginIata=STN&tpDestinationIata=BER',
            'sec-ch-ua': '"Chromium";v="113", "Not-A.Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'traceparent': '00-9b94869cb64c71f93a0bd0379413b500-7a8d8f309780a1f7-01',
            'tracestate': '646832@nr=0-1-646832-329815774-7a8d8f309780a1f7----1686125253435',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
            'x-newrelic-id': 'undefined',
        }
        json_data = {
            'query': 'mutation AssignSeat($basketId: String!, $seats: [SeatInputType]!) {\n  assignSeat(basketId: $basketId, seats: $seats) {\n    ...BasketCommon\n  }\n}\n\n\nfragment TotalCommon on PriceType {\n  total\n}\n\nfragment PriceCommon on PriceType {\n  amountWithTaxes\n  total\n  discount\n  discountCode\n}\n\nfragment ComponentCommon on ComponentType {\n  id\n  parentId\n  code\n  type\n  quantity\n  removable\n  price {\n    ...PriceCommon\n  }\n}\n\nfragment VariantUnionAddOn on VariantUnionType {\n  ... on AddOn {\n    itemId\n    provider\n    paxNumber\n    pax\n    src\n    start\n    end\n  }\n}\n\nfragment VariantUnionFare on VariantUnionType {\n  ... on Fare {\n    fareOption\n    journeyNumber\n  }\n}\n\nfragment VariantUnionSsr on VariantUnionType {\n  ... on Ssr {\n    journeyNumber\n    paxNumber\n    segmentNumber\n  }\n}\n\nfragment VariantUnionSeat on VariantUnionType {\n  ... on Seat {\n    paxNumber\n    journeyNumber\n    segmentNumber\n    seatType\n    designator\n    childSeatsWithAdult\n    hasAdditionalSeatCost\n  }\n}\n\nfragment VariantUnionBundle on VariantUnionType {\n  ... on Bundle {\n    journeyNumber\n    segmentNumber\n  }\n}\n\nfragment VariantUnionVoucher on VariantUnionType {\n  ... on Voucher {\n    firstName\n    lastName\n    email\n  }\n}\n\nfragment VariantUnionPhysicalVoucher on VariantUnionType {\n  ... on PhysicalVoucher {\n    sequenceNumber\n    firstName\n    lastName\n    address1\n    address2\n    city\n    postalCode\n    country\n    countryName\n    scheduleDate\n    message\n  }\n}\n\nfragment VariantUnionDigitalVoucher on VariantUnionType {\n  ... on DigitalVoucher {\n    sequenceNumber\n    firstName\n    lastName\n    email\n    theme\n    scheduleDate\n    scheduleTime\n    message\n  }\n}\n\nfragment VariantGroundTransfer on VariantUnionType {\n  ... on GroundTransfer {\n    locationPickUp\n    locationDropOff\n    routeType\n    startDate\n    endDate\n    itemId\n    location\n  }\n}\n\nfragment GettingTherePillar on GettingThereType {\n  price {\n    ...TotalCommon\n  }\n  journeys {\n    ... on JourneyType {\n      arrival\n      departure\n      destination\n      duration\n      fareClass\n      fareKey\n      fareOption\n      flightKey\n      flightNumber\n      isConnecting\n      isDomestic\n      journeyNum\n      origin\n      segments {\n        ... on SegmentType {\n          aircraft\n          arrival\n          departure\n          destination\n          duration\n          hasGovernmentTax\n          flightNumber\n          segmentNum\n          origin\n          originCountry\n          destinationCountry\n        }\n      }\n    }\n  }\n  discounts {\n    ... on DiscountType {\n      amount\n      code\n      journeyNum\n      percentage\n      zone\n      description\n      qty\n    }\n  }\n  taxes {\n    ... on TaxType {\n      amount\n      code\n      journeyNum\n      percentage\n      zone\n    }\n  }\n  vouchers {\n    ... on VoucherType {\n      amount\n      code\n      status\n      accountNumber\n    }\n  }\n  components {\n    ... on ComponentType {\n      ...ComponentCommon\n      variant {\n        ...VariantUnionAddOn\n        ...VariantUnionFare\n        ...VariantUnionSsr\n        ...VariantUnionSeat\n        ...VariantGroundTransfer\n        ...VariantUnionBundle\n        ...VariantUnionVoucher\n        ...VariantUnionDigitalVoucher\n        ...VariantUnionPhysicalVoucher\n      }\n    }\n  }\n  messages {\n    ... on MessageType {\n      type\n      journeyNum\n      key\n      message\n    }\n  }\n}\n\nfragment StayingTherePillar on StayingThereType {\n  price {\n    ...TotalCommon\n  }\n  components {\n    ...ComponentCommon\n    price {\n      ...PriceCommon\n      fat\n      amount\n    }\n    payLater {\n      ...PriceCommon\n      fat\n      amount\n    }\n    variant {\n      ... on Hotel {\n        hotelName\n        reservationDescription\n        countryCode\n        city\n        startDate\n        endDate\n        provider\n        propertySurcharges {\n          ... on PropertySurcharges {\n            type\n            price\n          }\n        }\n        guestTotals {\n          adults\n          children\n        }\n        reservationInfo {\n          rooms {\n            ... on HotelRoomReservationInfo {\n              roomAllocation {\n                adultCount\n                childAges\n              }\n            }\n          }\n        }\n      }\n    }\n  }\n  payLater {\n    total\n  }\n}\n\nfragment PayLaterCommon on PriceType {\n  total\n}\n\nfragment BasketCommon on BasketType {\n  id\n  tripId\n  dotrezSessionId\n  currency\n  gettingThere {\n    ...GettingTherePillar\n  }\n  stayingThere {\n    ...StayingTherePillar\n  }\n  price {\n    ...TotalCommon\n  }\n  payLater {\n    ...PayLaterCommon\n  }\n  totalToPay\n}\n\n',
            'variables': {
                'basketId': self.basket_id,
                'seats': [],
            },
            'operationName': 'AssignSeat',
        }
        endpoint = 'https://www.ryanair.com/api/basketapi/en-gb/graphql'
        response = self.send_post_request(headers, endpoint, json_data)

        self.blobs_list.append(API_data(str(json_data), 'Book/assign_seats', 'FR1', 'request'))
        self.blobs_list.append(API_data(response.text, 'Book/assign_seats', 'FR1', 'response'))


    def get_email_password(self):
        # r = redis.Redis(host="10.10.0.4",port=6379,db=0)
        startup_nodes = settings.REDIS_CLUSTER_NODES
        r = RedisCluster(startup_nodes=startup_nodes, decode_responses=True)
        key = 'RYANAIR-PRODUCTION-EMAILS'

        is_available = r.exists(key)

        if not is_available:
            print('email not available in redis')
            objects = Email_model.objects.all().filter(Airline_code='FR1')
            for object in objects:
                d = {}
                d['email'] = object.email
                d['password'] = object.password
                d['cookies'] = object.cookies
                r.lpush(key, json.dumps(d))

        current_email = json.loads(r.rpop(key))
        r.lpush(key, json.dumps(current_email))
        return current_email


    def login(self):
        email_dict = self.get_email_password()
        self.booking_email = email_dict['email']

        login_headers = {
            'authority': 'api.ryanair.com',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'cache-control': 'no-cache',
            'content-type': 'application/json',
            'cookie': email_dict['cookies'],
            'origin': 'https://www.ryanair.com',
            'pragma': 'no-cache',
            'sec-ch-ua': '"Chromium";v="113", "Not-A.Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
        }

        json_data = {
            'email': email_dict['email'],
            'password': email_dict['password'],
            'policyAgreed': True,
        }
        login_endpoint = 'https://api.ryanair.com/usrprof/v2/accountLogin?market=en-gb'

        login_response = self.send_post_request(login_headers, login_endpoint, json_data)

        self.blobs_list.append(API_data(str(json_data), 'Book/login', 'FR1', 'request'))
        self.blobs_list.append(API_data(login_response.text, 'Book/login', 'FR1', 'response'))

        login_response = json.loads(login_response.text)
        customer_id = str(login_response['customerId'])
        session_token = str(login_response['token'])

        return customer_id, session_token

    def get_expiration_date(self, data):
        year = data['expiryYear']
        month = data['expiryMonth']
        date = '01'
        if len(year) == 2:
            year = '20' + year

        if len(month) == 1:
            month = '0' + month

        response = year + '-' + month + '-' + date
        return response

    def get_payment_method(self, card_type):
        if card_type == 'VISA':
            return 'VI'
        elif card_type == 'MASTERCARD':
            return 'MC'
        elif card_type == 'DISCOVER':
            return 'DS'
        elif card_type == 'AMEX':
            return 'AX'
        elif card_type == 'UATP':
            return 'TP'



    def make_payment(self, customer_id, ryanair_token):
        headers = {
            'authority': 'www.ryanair.com',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'cache-control': 'no-cache',
            'client': 'desktop',
            'client-version': '3.65.0',
            'content-type': 'application/json',
            'cookie': 'rid=20736901-bf16-4fbb-8068-21900ff0c319; rid.sig=OCBtG/WF9HO7H4S44kdr0Q9YRbVRlLmXHl+JC3DAPukifYQYRB1Zw4pnTmQP/uv4ok+wW2OKV/dXM2dBUIRSymQcMGFzmspSbLdnXWidLlCuhX/QYdbuaI/s/5rX383WZ7ACymT4jGW+VrgDiomFwbyrvfMOMs8DOY5wtgFylphQewNdLLnZoUkIuE47aiWkXWIVwCeSpPaexSvaf9FrA7N9KIun91c4rgWNU9sGctaApLfI3c69thJinJcsCzuvcQh4HiL6OhXsLaIwtJycZ3prQHuKBnGEQfXmsYjIxoeOhIXscO18H5Xux5eDMdWLm8aBXosEdfUL/cPGJyGkZs3ufJAkHwxfpHtGpzZT8/SQ1SFj2cCVEywianoaJ7/Zodu6bg631JR1lBflyOJnqdk/1YItsCcC5y+yYTYedJ9pMB9ikhYlb3qA/ZVCVYLmqE6SEJQKDPDz6ZE5P23knQKKQFUWF/vfLw8NdZ8EA2m4LS2gF+zcFfF0f8hYheqDZ1RqrQTVy30BiNWhQkfl/A==; mkt=/gb/en/; fr-visit-id=25cf8c86-cec1-480c-8305-995c9f6a7d19; _ga=GA1.2.148026902.1675340460; STORAGE_PREFERENCES={"STRICTLY_NECESSARY":true,"PERFORMANCE":true,"FUNCTIONAL":true,"TARGETING":true,"SOCIAL_MEDIA":true,"PIXEL":true,"GANALYTICS":true,"__VERSION":2}; RY_COOKIE_CONSENT=true; bid_FRwdAp7a9G2cnLnTsgyBNeduseKcPcRy=658daf5c-797b-44d6-8935-d1c6de0568e8; RYANSESSION=Y9uqvwqhAm0AAFcgRUEAAAA7; _hjSessionUser_135144=eyJpZCI6IjMzMWE0Nzk1LTM5MzgtNWU5Ny1iYzY2LWM5ZGVhMzljN2JiZiIsImNyZWF0ZWQiOjE2NzUzNDA0NjEzMDcsImV4aXN0aW5nIjp0cnVlfQ==; agso=AQGewQwBAO9_ugEYBdtImQVi15IAl2k.; agsd=UaYSR_UKOM1tji40TZjzmKmN3POlgQFhaTSnz78WxEFTTO1u; agsn=h08Cz47eVZiWMjXAL8ctx8xh_RRzcxE1TpPcobm9pOc.; _cc=AYYTDLGQSwQwCkV22mxyzVLJ; _gcl_au=1.1.392399247.1677754258; fr-correlation-id=e8e522be-137e-48bb-966a-d0b7d1c8bdd4; fr-correlation-id.sig=ZMGcLW4B1zeAZ877ZsZBM0WrX9s; _cid_cc=AYYTDLGQSwQwCkV22mxyzVLJ; _gid=GA1.2.1688928057.1685255862; .AspNetCore.Session=CfDJ8FC4fSlP6dxPggIvnxx9l71UrKjq8qpULVZVQWhxZMQU5OUPRngBjTinRPYG9oGV%2Bt1S6n2fXQ0DkOH9K0cVkeW%2BKX5TKCyF%2FPxY2VQ4W4B0qOt4zDTX5kRlmioDhzuJqDrJIhHqcvbRhuL6FdrS2Uos8aerdqRCzq0UXRfh60v6; agssn=AbzndTcBAGuBgpsQYdtI2B5A4g..; myRyanairID=1org8g71997l1; ADRUM=s=1685455703567&r=https%3A%2F%2Fcarhire.ryanair.com%2Fin-path%3Fhash%3D1064852707; aws-waf-token=90d17ad1-8ed5-4989-90cb-8526369aad5b:BQoAmiFiyt4AAAAA:uoMPcp0KI0O6jXi1YIhTWksL9XAMkemfDYQCNv86DVXw81Z+9SUOwjfT+dfnht8Oxol8XixnKlCiSRsTXXgnILYkLQi7xZFsCvqsVF3iVAbHL2n0qznoUJBdQoEoSfh8ORR1ts90n/r5ow/Cmvdr/QC06qwXsmgtl1CxdRU2y3JiKcBWeg==; agsd=c9ViDjC8QdlyrrsWuec351P3yezVJvMdFEhNswfoMVOKwQ33; .AspNetCore.Session=CfDJ8MDrobS2KpxGoo43M9dUsUPs96MUnA9Sr0288izB%2BDeoKokTC01tqg50Fjwp7y8vqw3fA%2BQ3FhtNmusoInGyqDzGSpL6bgTGCt2Z7itI7MendRd056aAgVrIuCkA4NK%2Fc0XbOGuOrrsx8Lw8suPxMrgKOH1v8IM3gxojLFnEdVCT',
            'dotrez-session': 'etaptiai05cqhbbn5yaqqk2t',
            'fr-correlation-id': 'e8e522be-137e-48bb-966a-d0b7d1c8bdd4',
            'fr-payment-caller': 'BOOKING',
            'fr-token-sig': 'b4lHDOZBesb0mJaFPQJMlVlZo9dYJFGjSoH5gzaEY0Sj73k891aXwRcVAf/rTB11q/1Y5ViYme3rlAzSuXevyw==',
            'newrelic': 'eyJ2IjpbMCwxXSwiZCI6eyJ0eSI6IkJyb3dzZXIiLCJhYyI6IjY0NjgzMiIsImFwIjoiMzkwMDg1MzUzIiwiaWQiOiI4MzAyZjZhY2I3NjlhMjk0IiwidHIiOiI5MGExZDhlZDViMjNjNDk3MzMwODY2ZWYzZjQ1ZWYwMCIsInRpIjoxNjg1NDU1OTE2MDYwfX0=',
            'origin': 'https://www.ryanair.com',
            'pragma': 'no-cache',
            'referer': 'https://www.ryanair.com/gb/en/payment?tpAdults=1&tpTeens=0&tpChildren=0&tpInfants=0&tpStartDate=2023-06-14&tpEndDate=2023-06-18&tpDiscount=0&tpPromoCode=&tpOriginIata=STN&tpDestinationIata=DUB',
            'referrer': '/gb/en/payment',
            'sec-ch-ua': '"Chromium";v="113", "Not-A.Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'traceparent': '00-90a1d8ed5b23c497330866ef3f45ef00-8302f6acb769a294-01',
            'tracestate': '646832@nr=0-1-646832-390085353-8302f6acb769a294----1685455916060',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
            'x-auth-token': ryanair_token,
            'x-newrelic-id': 'undefined',
        }
        card_config_payload = {
            "amount": self.request.data['TotalFare'],
            "bookingRef": self.request.data['BookRef'],
            "clientId": '0',
            "currency": self.request.data['BaseCurrency'],
            "externalIdentifiers": {
                "externalIdentifiers1": self.request.data['BookRef'],
                "externalIdentifiers2": self.request.data['ListPassengers'][0]['FirstName'],
                "externalIdentifiers3": self.request.data['ListFlightSegments'][0]['DepartureDateTime'],
                "externalIdentifiers4": self.request.data['SupplierCode'],
                "externalIdentifiers5": self.request.data['ListFlightSegments'][0]['DepartureAirport'] + "-" +
                                        self.request.data['ListFlightSegments'][0]['ArrivalAirport']
            },
            "firstName": self.request.data['ListPassengers'][0]['FirstName'],
            "lastName": self.request.data['ListPassengers'][0]['LastName'],
            "searchId": self.request.data['SearchIdentifier'],
            "virtualAccountId": self.request.data['AccountId']
        }
        self.blobs_list.append(API_data(str(card_config_payload), 'CardBook', 'FR1', 'request'))
        card_details = get_card_details(self.request.data['MysCardConfig'], card_config_payload, api="Book")
        self.blobs_list.append(API_data(str(card_details), 'CardBook', 'FR1', 'response'))
        #sample response of get_card_details
        # card_details = {
        #     "message": "POST Request successful.",
        #     "isError": False,
        #     "result": {
        #         "data": {
        #             "isCardGenerated": False,
        #             "nameOnCard": "Aer_EUR",
        #             "cardNo": "154114608002000",
        #             "cvv": "000",
        #             "expiryYear": "2024",
        #             "expiryMonth": "8",
        #             "startYear": "2022",
        #             "startMonth": "8",
        #             "cardType": "UATP",
        #             "cardAccountType": "Credit",
        #             "accountNo": "",
        #             "referenceNumber": "6770471",
        #             "vendorId": 1106,
        #             "vpaID": 106,
        #             "cardStatus": "Static"
        #         }
        #     }
        # }

        isd_code = self.request.data['ListPassengers'][0]['ISDCode']
        if '+' in isd_code:
            isd_code = isd_code.replace('+', '')

        json_data = {
            'basketId': self.basket_id,
            'myRyanairToken': ryanair_token,
            'myRyanairCustomerId': customer_id,
            'agreeNewsletters': True,
            'payment': {
                'contact': {
                    'email': self.request.data['ListPassengers'][0]['EmailId'],
                    'phoneNumber': self.request.data['ListPassengers'][0]['Phonenumber'],
                    'phoneCode': int(isd_code),
                    'countryCode': self.request.data['ListPassengers'][0]['Nationality'],
                },
                'threeDsIFrameSize': 5,
                'accountNumber': card_details['result']['data']['cardNo'],
                'accountName': self.request.data['ListPassengers'][0]['FirstName'],
                'verificationCode': card_details['result']['data']['cvv'],
                'expiration': self.get_expiration_date(card_details['result']['data']),
                'paymentMethodCode': self.get_payment_method(card_details['result']['data']['cardType']),
                'address': {
                    'city': 'Alaska',
                    'line1': '321, Stanley layout',
                    'line2': '',
                    'country': 'US',
                    'postal': '32545',
                    'state': 'AK',
                },
                'currencyConversion': {
                    'foreignCurrencyCode': self.request.data['BaseCurrency'],
                },
                'isDepositPayment': False,
            },
            'BrowserInfo': {
                'browserColorDepth': 24,
                'browserJavaEnabled': False,
                'browserScreenHeight': 263,
                'browserScreenWidth': 1468,
                'browserTimeZone': -330,
            },
        }

        endpoint = 'https://www.ryanair.com/api/payment/en-gb/payment'
        response = self.send_post_request(headers=headers,
                                          endpoint=endpoint,
                                          payload=json_data)

        self.blobs_list.append(API_data(str(json_data), 'Book/payment', 'FR1', 'request'))
        self.blobs_list.append(API_data(response.text, 'Book/payment', 'FR1', 'response'))

        response = json.loads(response.text)
        payment_id = response['paymentId']
        return payment_id

    def check_status(self, payment_id):
        headers = {
            'authority': 'www.ryanair.com',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'cache-control': 'no-cache',
            'cookie': 'rid=20736901-bf16-4fbb-8068-21900ff0c319; rid.sig=OCBtG/WF9HO7H4S44kdr0Q9YRbVRlLmXHl+JC3DAPukifYQYRB1Zw4pnTmQP/uv4ok+wW2OKV/dXM2dBUIRSymQcMGFzmspSbLdnXWidLlCuhX/QYdbuaI/s/5rX383WZ7ACymT4jGW+VrgDiomFwbyrvfMOMs8DOY5wtgFylphQewNdLLnZoUkIuE47aiWkXWIVwCeSpPaexSvaf9FrA7N9KIun91c4rgWNU9sGctaApLfI3c69thJinJcsCzuvcQh4HiL6OhXsLaIwtJycZ3prQHuKBnGEQfXmsYjIxoeOhIXscO18H5Xux5eDMdWLm8aBXosEdfUL/cPGJyGkZs3ufJAkHwxfpHtGpzZT8/SQ1SFj2cCVEywianoaJ7/Zodu6bg631JR1lBflyOJnqdk/1YItsCcC5y+yYTYedJ9pMB9ikhYlb3qA/ZVCVYLmqE6SEJQKDPDz6ZE5P23knQKKQFUWF/vfLw8NdZ8EA2m4LS2gF+zcFfF0f8hYheqDZ1RqrQTVy30BiNWhQkfl/A==; mkt=/gb/en/; fr-visit-id=25cf8c86-cec1-480c-8305-995c9f6a7d19; _ga=GA1.2.148026902.1675340460; STORAGE_PREFERENCES={"STRICTLY_NECESSARY":true,"PERFORMANCE":true,"FUNCTIONAL":true,"TARGETING":true,"SOCIAL_MEDIA":true,"PIXEL":true,"GANALYTICS":true,"__VERSION":2}; RY_COOKIE_CONSENT=true; bid_FRwdAp7a9G2cnLnTsgyBNeduseKcPcRy=658daf5c-797b-44d6-8935-d1c6de0568e8; RYANSESSION=Y9uqvwqhAm0AAFcgRUEAAAA7; _hjSessionUser_135144=eyJpZCI6IjMzMWE0Nzk1LTM5MzgtNWU5Ny1iYzY2LWM5ZGVhMzljN2JiZiIsImNyZWF0ZWQiOjE2NzUzNDA0NjEzMDcsImV4aXN0aW5nIjp0cnVlfQ==; agso=AQGewQwBAO9_ugEYBdtImQVi15IAl2k.; agsd=UaYSR_UKOM1tji40TZjzmKmN3POlgQFhaTSnz78WxEFTTO1u; agsn=h08Cz47eVZiWMjXAL8ctx8xh_RRzcxE1TpPcobm9pOc.; _cc=AYYTDLGQSwQwCkV22mxyzVLJ; _gcl_au=1.1.392399247.1677754258; fr-correlation-id=e8e522be-137e-48bb-966a-d0b7d1c8bdd4; fr-correlation-id.sig=ZMGcLW4B1zeAZ877ZsZBM0WrX9s; _cid_cc=AYYTDLGQSwQwCkV22mxyzVLJ; _gid=GA1.2.1688928057.1685255862; .AspNetCore.Session=CfDJ8FC4fSlP6dxPggIvnxx9l71UrKjq8qpULVZVQWhxZMQU5OUPRngBjTinRPYG9oGV%2Bt1S6n2fXQ0DkOH9K0cVkeW%2BKX5TKCyF%2FPxY2VQ4W4B0qOt4zDTX5kRlmioDhzuJqDrJIhHqcvbRhuL6FdrS2Uos8aerdqRCzq0UXRfh60v6; agssn=AbzndTcBAGuBgpsQYdtI2B5A4g..; myRyanairID=1org8g71997l1; ADRUM=s=1685455703567&r=https%3A%2F%2Fcarhire.ryanair.com%2Fin-path%3Fhash%3D1064852707; aws-waf-token=90d17ad1-8ed5-4989-90cb-8526369aad5b:BQoAmiFiyt4AAAAA:uoMPcp0KI0O6jXi1YIhTWksL9XAMkemfDYQCNv86DVXw81Z+9SUOwjfT+dfnht8Oxol8XixnKlCiSRsTXXgnILYkLQi7xZFsCvqsVF3iVAbHL2n0qznoUJBdQoEoSfh8ORR1ts90n/r5ow/Cmvdr/QC06qwXsmgtl1CxdRU2y3JiKcBWeg==; agsd=c9ViDjC8QdlyrrsWuec351P3yezVJvMdFEhNswfoMVOKwQ33',
            'newrelic': 'eyJ2IjpbMCwxXSwiZCI6eyJ0eSI6IkJyb3dzZXIiLCJhYyI6IjY0NjgzMiIsImFwIjoiMzkwMDg1MzUzIiwiaWQiOiJkYzNjZDE4YTM1MDZiNDU2IiwidHIiOiI5M2RhZmQzNjZiZTk4ZGY3NjMwMmJhYzFhYjFlNjkwMCIsInRpIjoxNjg1NDU1OTE4MDcxfX0=',
            'pragma': 'no-cache',
            'referer': 'https://www.ryanair.com/gb/en/payment?tpAdults=1&tpTeens=0&tpChildren=0&tpInfants=0&tpStartDate=2023-06-14&tpEndDate=2023-06-18&tpDiscount=0&tpPromoCode=&tpOriginIata=STN&tpDestinationIata=DUB',
            'sec-ch-ua': '"Chromium";v="113", "Not-A.Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'traceparent': '00-93dafd366be98df76302bac1ab1e6900-dc3cd18a3506b456-01',
            'tracestate': '646832@nr=0-1-646832-390085353-dc3cd18a3506b456----1685455918071',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
            'x-newrelic-id': 'undefined',
        }
        params = {
            'paymentId': payment_id,
            'waitTimeSeconds': '50',
        }
        endpoint = 'https://www.ryanair.com/api/payment/en-gb/payment/status'
        response = self.send_get_request(headers=headers,
                                          endpoint=endpoint,
                                          params=params)

        self.blobs_list.append(API_data(str(params), 'Book/payment_status', 'FR1', 'request'))
        self.blobs_list.append(API_data(response.text, 'Book/payment_status', 'FR1', 'response'))
        response = json.loads(response.text)
        status = response['status']
        error = {}
        if status == 'Declined':
            error['errorCode'] = response['errorCode']
            error['errorMessage'] = response['errorMessage']

        return status, error


    def get_trip_overview(self, customer_id):
        headers = {
            'authority': 'www.ryanair.com',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-GB,en;q=0.9',
            'cache-control': 'no-cache',
            'content-type': 'application/json',
            'cookie': 'fr-correlation-id=1334742f-2f1d-4cf9-b7f5-7a93d236599d; rid=e053a503-1996-4513-b26c-1de7c0dcb167; mkt=/gb/en/; _ga=GA1.2.708858424.1687351341; _gid=GA1.2.574785759.1687351341; STORAGE_PREFERENCES={"STRICTLY_NECESSARY":true,"PERFORMANCE":true,"FUNCTIONAL":true,"TARGETING":true,"SOCIAL_MEDIA":true,"PIXEL":true,"GANALYTICS":true,"__VERSION":2}; RY_COOKIE_CONSENT=true; bid_FRwdAp7a9G2cnLnTsgyBNeduseKcPcRy=c788442e-47b1-40ff-8b26-6faba7dc9b00; .AspNetCore.Session=CfDJ8PHHHJHb%2BxJDghnHHhHaza%2FKhjelZdTmFbqV8cC4WrFK35m%2B6iL0HPifmEvSAAGUcH2c8M3lbMCSM9Vd%2FkGeuSOBpZdtvhxGE%2Fvv3sVDmDpgS1uh%2B1rW20Z8EYabQ0UgiO8lxlyL0Hrc6DoRGZ8fj4%2Bu22Y9MEoJcupL2zRaGM5w; agso=AVUnNigBAJ__rCNVcttIz3hy7HQK4Rk.; agsd=6xFQ-UhYlyMMMmoibZzAsbONcWklS40A_V2zm9lu8vMCGCcD; agsn=yLkhNMcMcR6f1fkxFlFraDouEyjkAYmAxneKHBV1tMc.; agssn=ASj_hEQBAJ__rCNVcttIuCPmLg..; _cc=ASltk1opnJpvROa3cw84lxE7; _cid_cc=ASltk1opnJpvROa3cw84lxE7; myRyanairID=1xxfyyn3ohx8e; aws-waf-token=cf57a1e9-d916-44b6-ad17-fcd45f5d1c1b:HgoAsaZZYEgAAAAA:8PaVeCw0iQ+QDUPsQ5opXo2QhUo2u70TB3oHql3sj6nswoYNAXkn9X5+4oFylq5ILwo8CwxPpCecA/ff1eCOGr43mrq9AslBV40q5J1H1lYg05hxIL6LZQguhfRJ/PjW2Xsg/hNoCmLphnBmwLWPKM7V6QXFtODwdk2gQckji7Be9kTWo3E3VxENYKglnyH0; rid.sig=jyna6R42wntYgoTpqvxHMK7H+KyM6xLed+9I3KsvYZaVt7P36AL6zp9dGFPu5uVxaIiFpNXrszr+LfNCdY3IT3oCSYLeNv/ujtjsDqOzkY5JmUFsCdAEz3kpPbhCUwiArp5oaa75tpJtO3kFwYQ8l0DbH67AtcN/PMbniLsiM5qn+2AjrrtoNJicE3ZQwFHVipe4lWPSRfq2OIyUrlFhwEDt20+wCX7l1mCubNXtG6ly1DzBqZYVDrO1g5GvXPZOA42fzbLan/n0LVhBklBpY6U/DWH9GWzD7j+/+9w23sqU9uVs2TW0AC6JX4YnBG0JUYQEBR4bMXYlq9mpvZdBBc3yMCaEXwHho6z5hf2BQbIaz9GN1IMsbSL57KWbHyz76fC628bk5FkdHbFlJBb3NsU2uXZ6B3cZJZb3AcD2BnjRvUYVCuKxAfi9cklMlgWPfu79GtoOL3uLi0ZNXABydXpcZ9F+fPe8sXyJsES55kFvXV9f0et/yAMn4PYmfHVgHWNZIUjdS1iH3tSbaA2A4SezgTdrOBpSxPwnKC1+gDD/vt86vxbZ/s5rMXBYOjJBi3XaVHndbY8ZkPysqussfi8fHSYUP0EkdwgKXlcEtb1fqM+WfWmwJlVP/fQH35Vo3l3f5nGNwRthEE+EFbfxwueZaPO8whfE3zxWu+DeQLaTfIhnD4x8o2nb6FxB9JOSyMnAsKAF+UNvGiPOozf2IzxkpzZr1i4sajU/ubevSRVV+GgoGhKTIznNhzDL8ZD3fp1Ce1KbsFBHGNeSIPyF0w==; agsd=c9ViDjC8QdlyrrsWuec351P3yezVJvMdFEhNswfoMVOKwQ33; .AspNetCore.Session=CfDJ8JyS2spazCRLi9BjvHl3ZOtE7ZFM7ZIb%2BZEQ3Qt81YxYkJ5u5i9bsVJnCulb17i%2Bn%2BpHZU8TOTumSYxPV%2BnYSDCR3SDBkJgYjvukRdraOvySzMNwTYAFuMgorKLHtqeHD9Sq%2FqHThcUfFTqw%2FGbH3AI04%2FBwgb7DlvG358YFonWn',
            'newrelic': 'eyJ2IjpbMCwxXSwiZCI6eyJ0eSI6IkJyb3dzZXIiLCJhYyI6IjY0NjgzMiIsImFwIjoiMzY3MzY3NDc1IiwiaWQiOiI2NDZlNzNlNzU2MWE5YWMzIiwidHIiOiIwMjE5ZTI3NjI1ZTcxNzNkOGQyOGFlYjQ1MzBjZTUwMCIsInRpIjoxNjg3MzUxNzQ5MTM2fX0=',
            'origin': 'https://www.ryanair.com',
            'pragma': 'no-cache',
            'referer': 'https://www.ryanair.com/gb/en/trip?tpAdults=1&tpTeens=0&tpChildren=0&tpInfants=0&tpStartDate=2023-08-13&tpEndDate=&tpDiscount=0&tpPromoCode=&tpOriginIata=STN&tpDestinationIata=AAL&tripId=bcf1bc76-24d1-41a5-8810-485d2b8d02ed',
            'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'traceparent': '00-0219e27625e7173d8d28aeb4530ce500-646e73e7561a9ac3-01',
            'tracestate': '646832@nr=0-1-646832-367367475-646e73e7561a9ac3----1687351749136',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'x-auth-token': 'dWaMrbZ2_wXoMOe60Nf6mhPhFu9vpmugnWC7mNZeZQyAZf3Y30pH6riNjznqgZR5-VjjNQv_HwcFi-rq3caNDEElgtQhew-4pBl9HNqEvyfjaGxNXy0MHYeKTn_6khUGOeDbcZKkM888rukuhGGqoDIi6gZ_VRkX5_5Q-ntlSgM=',
            'x-newrelic-id': 'undefined',
        }

        departure_date = self.request.data['ListFlightSegments'][0]['DepartureDateTime'].split(' ')[0]
        if self.is_return == 2:
            arrival_date = self.request.data['ListFlightSegments'][1]['DepartureDateTime'].split(' ')[0]
        else:
            arrival_date = ''
        adults_count = len(self.request.data['ListPassengers'])
        origin = self.request.data['ListFlightSegments'][0]['DepartureAirport']
        destination = self.request.data['ListFlightSegments'][0]['ArrivalAirport']
        json_data = {
            'basketId': None,
            'market': 'en-gb',
            'isDesktop': True,
            'flightFlowLastStep': 'trip-overview',
            'tpAdults': adults_count,
            'tpTeens': '0',
            'tpChildren': '0',
            'tpInfants': '0',
            'tpStartDate': departure_date,
            'tpEndDate': arrival_date,
            'tpDiscount': '0',
            'tpPromoCode': '',
            'tpOriginIata': origin,
            'tpDestinationIata': destination,
            'tripId': self.basket_id,
            'customerId': customer_id,
        }

        endpoint = 'https://www.ryanair.com/api/tpsearch/v1/tripOverview'
        response = self.send_post_request(headers, endpoint, json_data)

        self.blobs_list.append(API_data(str(json_data), 'Book/trip_overview', 'FR1', 'request'))
        self.blobs_list.append(API_data(response.text, 'Book/trip_overview', 'FR1', 'response'))
        response = json.loads(response.text)
        if response['gettingThere'] is not None:
            PNR = response['gettingthere']['flights'][0]['pnr']
        elif response['stayingThere'] is not None:
            PNR = response['stayingThere']['flights'][0]['pnr']
        elif response['gettingAround'] is not None:
            PNR = response['gettingAround']['flights'][0]['pnr']

        return PNR

    def book_response(self):
        response = {
            'IsCashFlow': False,
            'SupplierRefNo': "",
            'ListPassengers': self.request.data['ListPassengers'],
            'PNR': '',
            'ListFlightSegments': self.request.data['ListFlightSegments'],
            'BookStatus': 1,
            'Message': '',
            'OptionalData':{}
        }

        return response




