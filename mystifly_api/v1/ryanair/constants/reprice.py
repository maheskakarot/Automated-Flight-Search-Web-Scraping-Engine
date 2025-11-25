REQUIRED_FIELDS_TO_BOOK = [
    "PassengersInfo",
    "Address",
    "City",
    "Country",
    "PostCode/ZipCode",
    "CountryCode",
    "ContactNumber",
]

# Boiler plates for reprice validation API response
ONE_WAY_REPRICE_RESPONSE_STRUCTURE = {
    "total_amount_to_pay_info": {},
    "required_fields_to_book": REQUIRED_FIELDS_TO_BOOK
}

RETURN_TRIP_REPRICE_RESPONSE_STRUCTURE = {
    "departure_flight_info": {},
    "arrival_flight_info": {},
    "total_amount_to_pay_info": {},
    "required_fields_to_book": REQUIRED_FIELDS_TO_BOOK
}

SEATS_INFO_STRUCTURE = {
    "seat_count": 0,
    "items_included": [],
    "items_description": [],
    "fare_info": {}
}

PRICE_INFO_STRUCTURE = {
    "currency": "",
    "value": ""
}

DISCOUNT_OR_TAX_RESPONSE_STRUCTURE = {
    "name": "",
    "price_info": {}
}

PAID_ITEM = {
    "item": "",
    "price_info": {}
}
