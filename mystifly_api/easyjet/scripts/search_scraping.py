import requests
import random
from django.conf import settings
from utils.proxy import get_proxy
from easyjet import static_data

import json


class Scrape_flight_data:

    def search_scraping(data):
        message = ""
        proxy = get_proxy()
        proxies = {
            "http"  : "http://" + proxy[0],
        }
        cookies_dict = {}
        res = requests.get("https://www.easyjet.com/en",
                proxies=proxies
                )
        headers = {
            'ADRUM': 'isAjax:true',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Referer': 'https://www.easyjet.com/en/buy/flights?isOneWay=on&pid=www.easyjet.com',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'x-b2b-misc': '',
            }

        cookies_dict= res.cookies.get_dict()

        try:
            airport = static_data.data.filter(airport_code=data['origin'])
            for codes in airport:
                data['origin']=codes.mapping_airport_code
        except Exception as e:
            pass
        try:
            dep_airport = static_data.data.filter(airport_code=data['destination'])
            for codes in dep_airport:
                data['destination']=codes.mapping_airport_code
        except Exception as e:
            pass
        

        if data['air_trip']==1:            
            search_url = f"https://www.easyjet.com/ejavailability/api/v71/availability/query?AdditionalSeats=0&AdultSeats={data['adult']}&ArrivalIata={data['destination']}&ChildSeats={data['child']}&CurrencyCode=GBP&DepartureIata={data['origin']}&IncludeFlexiFares=false&IncludeLowestFareSeats=true&IncludePrices=true&Infants={data['infant']}&IsTransfer=false&LanguageCode=EN&MaxDepartureDate={data['depature_date']}&MinDepartureDate={data['depature_date']}"
        else:
            search_url = f"https://www.easyjet.com/ejavailability/api/v71/availability/query?AdditionalSeats=0&AdultSeats={data['adult']}&ArrivalIata={data['destination']}&ChildSeats={data['child']}&CurrencyCode=GBP&DepartureIata={data['origin']}&IncludeFlexiFares=false&IncludeLowestFareSeats=true&IncludePrices=true&Infants={data['infant']}&IsTransfer=false&LanguageCode=EN&MaxDepartureDate={data['depature_date']}&MaxReturnDate={data['return_date']}&MinDepartureDate={data['depature_date']}&MinReturnDate={data['return_date']}"
        for ip in proxy:
            proxies = {
                "http"  : "http://" + ip,
            }
            response = requests.get(
                url=search_url,
                headers=headers,
                cookies=cookies_dict,
                proxies=proxies
            )
            if response.status_code == 200:
                break
        logs = {
            "Search_api":{
                "url":search_url,
                "stauts":response.status_code,
                "text":response.text
            }
        }
        if response.status_code != 200 :
            message = "Failed to scrape data from Website."
            return response.text,cookies_dict,message,logs
        cookies = {}

        for cookie in response.cookies:
            cookies[cookie.name] = cookie.value
        response_data = json.loads(response.text)

        if not response_data:

            message = "No flights available on this date. Try another date"

            return response_data,cookies_dict,message,logs


        return response_data,cookies_dict,message,logs