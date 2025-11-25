
subscriber_payload = '''{
    "country_code": "91",
    "mobile": "%s"
}'''

search_payload = '''{
  "OriginDestinationInformations": [
    {
      "DepartureDateTime": "%s",
      "OriginLocationCode": "LON",
      "DestinationLocationCode": "DUB"
    },
    {
      "DepartureDateTime": "%s",
      "OriginLocationCode": "DUB",
      "DestinationLocationCode": "LON"
    }
  ],
  "TravelPreferences": {
    "MaxStopsQuantity": "Direct",
    "AirTripType": "Return"
  },
  "PassengerTypeQuantities": [
    {
      "Code": "ADT",
      "Quantity": 1
    },
    {
      "Code": "CHD",
      "Quantity": 0
    },
    {
      "Code": "INF",
      "Quantity": 0
    }
  ],
  "OriginNearByAirports": false,
  "DestinationNearByAirports": false,
  "isPaginated": true,
  "page": 1,
  "pageSize": 50
}'''

revalidation_payload = '''{
    "ResultId": "%s",
    "FareDetails": {
        "currency": "%s",
        "value": %s
    }
}'''

initiate_booking_payload = '''{
    "ResultId": "%s",
    "PassengersDetails": [
        {
            "Title": "Mr",
            "FirstName": "Mahes",
            "LastName": "Waran",
            "Code": "ADT"
        }
    ],
    "FareDetails": {
        "currency": "EUR",
        "value": 10.99
    },
    "Address": "Test",
    "City": "Kaithal",
    "Country": "India",
    "PostCode": "136027",
    "CountryCode": "+91",
    "ContactNumber": "8950101357"
}'''

seat_selection_payload = '''{
    "ResultId": "%s",
    "ContinueWithoutSeatsSelection": true,
    "SeatSelectionFor": "Departure Flight",
    "PassengersSeatsInfo": [
        {
            "SeatNumber": "06B",
            "SeatType": "Standard",
            "PassengerName": "Mahes Waran",
            "Code": "ADT"
        }
    ]
}'''

baggage_selection_payload = '''{
    "ResultId": "%s",
    "SelectIncludedBags": true
}'''

fastrack_payload = '''{
    "ResultId": "%s",
    "FastTrackInfo": {
        "DepartureFlight": {},
        "ArrivalFlight": {}
    }
}'''

login_payload = '''{
    "UserEmail": "japanmailbox61@gmail.com",
    "UserPassword": "Japan@123"
}'''

payment_payload = '''{
    "ResultId": "%s",
    "CountryCode": "+91",
    "ContactNumber": "8825458179",
    "CreditCardInfo": {
        "CardNumber": "1315811855108007",
        "ExpiryDate": "0125",
        "CVV": "609",
        "HolderName": "SMAHES"
    },
    "AddressInfo": {
        "AddressLineFirst": "CostcoTravel",
        "AddressLineSecond": "California",
        "City": "California",
        "Country": "US",
        "PostCode": "560032",
        "State": "California"
    },
    "FareDetails": {
        "Currency": "EUR",
        "Value": 10.99
    }
}'''

