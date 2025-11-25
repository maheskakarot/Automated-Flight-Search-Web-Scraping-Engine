from v1.ryanair.models import Airport
from django.core.cache import cache
from v1.ryanair import views


PASSENGER_TYPE = {
    "adult": "ADT",
    "children": "CHD",
    "infant": "INF"
}

MANAGE_BOOKING_URL = 'https://www.ryanair.com/gb/en/trip/manage'

RYANAIR_HOME_URL = 'https://www.ryanair.com/gb/en'
RYANAIR_SEARCH_API_ENDPOINT = 'https://www.ryanair.com/api/booking/v4/en-gb/availability'


# This function will return search url and other required info
def search_url_and_other_req_info(validated_data):
    OriginDestinationInformations = validated_data.get('OriginDestinationInformations')
    TravelPreferences = validated_data.get('TravelPreferences')
    PassengerTypeQuantities = validated_data.get('PassengerTypeQuantities')
    OriginNearByAirports = validated_data.get('OriginNearByAirports')
    DestinationNearByAirports = validated_data.get('DestinationNearByAirports')

    isReturn = False
    ArrivalDate = ""
    adults = teens = children = infants = 0

    DepartureLocationInfo = OriginDestinationInformations[0]
    OriginLocationCode = DepartureLocationInfo["OriginLocationCode"]
    DestinationLocationCode = DepartureLocationInfo["DestinationLocationCode"]
    DepartureDateTime = DepartureLocationInfo["DepartureDateTime"]
    DepartureDate = DepartureDateTime.split("T")[0]
    DepartureTime = DepartureDateTime.split("T")[1]

    data = cache.get('cached_data')
    if data is None:
        data = views.load_data_into_cache()
    try:
        OriginNearByAirports = data.get(code=OriginLocationCode).near_by_airports
        DestinationNearByAirports = data.get(code=DestinationLocationCode).near_by_airports
        if OriginNearByAirports:
            OriginLocationCode = data.get(code=OriginLocationCode).mapping_code
        if DestinationNearByAirports:
            DestinationLocationCode = data.get(code=DestinationLocationCode).mapping_code
    except:
        try:
            OriginNearByAirports = Airport.objects.get(code=OriginLocationCode).near_by_airports
            DestinationNearByAirports = Airport.objects.get(code=DestinationLocationCode).near_by_airports
            if OriginNearByAirports == True:
                OriginLocationCode = Airport.objects.get(code=OriginLocationCode).mapping_code
            if DestinationNearByAirports == True:
                DestinationLocationCode = Airport.objects.get(code=OriginLocationCode).mapping_code

        except Exception as ex:
            OriginNearByAirports = DestinationNearByAirports = False

    # try:
    #     OriginNearByAirports = Airport.objects.get(code=OriginLocationCode).near_by_airports
    #     DestinationNearByAirports = Airport.objects.get(code=DestinationLocationCode).near_by_airports

    # except Exception as ex:
    #     pass

    if len(OriginDestinationInformations) > 1:
        ArrivalLocationInfo = OriginDestinationInformations[1]
        ArrivalDateTime = ArrivalLocationInfo["DepartureDateTime"]
        ArrivalDate = ArrivalDateTime.split("T")[0]
        ArrivalTime = ArrivalDateTime.split("T")[1]

    if TravelPreferences["AirTripType"] == "Return":
        isReturn = True

    for PassengerTypeQuantity in PassengerTypeQuantities:
        if PassengerTypeQuantity["Code"] == PASSENGER_TYPE["adult"]:
            adults = PassengerTypeQuantity["Quantity"]

        elif PassengerTypeQuantity["Code"] == PASSENGER_TYPE["children"]:
            children = PassengerTypeQuantity["Quantity"]

        elif PassengerTypeQuantity["Code"] == PASSENGER_TYPE["infant"]:
            infants = PassengerTypeQuantity["Quantity"]

    search_url = f"{RYANAIR_HOME_URL}/trip/flights/select?adults={adults}&teens={teens}" \
                 f"&children={children}&infants={infants}&dateOut={DepartureDate}&dateIn={ArrivalDate}" \
                 f"&isConnectedFlight=false&isReturn={isReturn}&discount=0" \
                 f"&promoCode=" \
                 f"&originIata={OriginLocationCode}&destinationIata={DestinationLocationCode}&tpAdults={adults}" \
                 f"&tpTeens={teens}" \
                 f"&tpChildren={children}&tpInfants={infants}&tpStartDate={DepartureDate}" \
                 f"&tpEndDate={ArrivalDate}" \
                 f"&tpDiscount=0&tpPromoCode=&tpOriginIata={OriginLocationCode}" \
                 f"&tpDestinationIata={DestinationLocationCode}"

    # Small change in url when user is including all airports of origin country- "originIata to originMac"
    if OriginNearByAirports:
        search_url = f"{RYANAIR_HOME_URL}/trip/flights/select?adults={adults}&teens={teens}" \
                     f"&children={children}&infants={infants}&dateOut={DepartureDate}&dateIn={ArrivalDate}" \
                     f"&isConnectedFlight=false&isReturn={isReturn}&discount=0" \
                     f"&promoCode=" \
                     f"&originMac={OriginLocationCode}&destinationIata={DestinationLocationCode}&tpAdults={adults}" \
                     f"&tpTeens={teens}" \
                     f"&tpChildren={children}&tpInfants={infants}&tpStartDate={DepartureDate}" \
                     f"&tpEndDate={ArrivalDate}" \
                     f"&tpDiscount=0&tpPromoCode=&tpOriginMac={OriginLocationCode}" \
                     f"&tpDestinationIata={DestinationLocationCode}"

    # Small change in url when user is including all airports of destination country- "destinationIata to
    # destinationMac"
    if DestinationNearByAirports:
        search_url = f"https://www.ryanair.com/gb/en/trip/flights/select?adults={adults}&teens={teens}" \
                     f"&children={children}&infants={infants}&dateOut={DepartureDate}&dateIn={ArrivalDate}" \
                     f"&isConnectedFlight=false&isReturn={isReturn}&discount=0" \
                     f"&promoCode=" \
                     f"&originIata={OriginLocationCode}&destinationMac={DestinationLocationCode}&tpAdults={adults}" \
                     f"&tpTeens={teens}" \
                     f"&tpChildren={children}&tpInfants={infants}&tpStartDate={DepartureDate}" \
                     f"&tpEndDate={ArrivalDate}" \
                     f"&tpDiscount=0&tpPromoCode=&tpOriginIata={OriginLocationCode}" \
                     f"&tpDestinationMac={DestinationLocationCode}"

    if OriginNearByAirports and DestinationNearByAirports:
        search_url = f"{RYANAIR_HOME_URL}/trip/flights/select?adults={adults}&teens={teens}" \
                     f"&children={children}&infants={infants}&dateOut={DepartureDate}&dateIn={ArrivalDate}" \
                     f"&isConnectedFlight=false&isReturn={isReturn}&discount=0" \
                     f"&promoCode=" \
                     f"&originMac={OriginLocationCode}&destinationMac={DestinationLocationCode}&tpAdults={adults}" \
                     f"&tpTeens={teens}" \
                     f"&tpChildren={children}&tpInfants={infants}&tpStartDate={DepartureDate}" \
                     f"&tpEndDate={ArrivalDate}" \
                     f"&tpDiscount=0&tpPromoCode=&tpOriginMac={OriginLocationCode}" \
                     f"&tpDestinationMac={DestinationLocationCode}"

    required_data = {
        "search_url": search_url,
        "adults": adults,
        "children": children,
        "teens": teens,
        "infants": infants,
        "isReturn": isReturn
    }

    return required_data


def search_url_and_other_req_info_v3(validated_data):
    OriginDestinationInformations = validated_data.get('OriginDestinationInformations')
    TravelPreferences = validated_data.get('TravelPreferences')
    PassengerTypeQuantities = validated_data.get('PassengerTypeQuantities')
    OriginNearByAirports = validated_data.get('OriginNearByAirports')
    DestinationNearByAirports = validated_data.get('DestinationNearByAirports')

    isReturn = False
    ArrivalDate = ""
    adults = teens = children = infants = 0

    DepartureLocationInfo = OriginDestinationInformations[0]
    OriginLocationCode = DepartureLocationInfo["OriginLocationCode"]
    DestinationLocationCode = DepartureLocationInfo["DestinationLocationCode"]
    DepartureDateTime = DepartureLocationInfo["DepartureDateTime"]
    DepartureDate = DepartureDateTime.split("T")[0]
    DepartureTime = DepartureDateTime.split("T")[1]
    data = cache.get('cached_data')
    if data is None:
        data = views.load_data_into_cache()
    try:
        OriginNearByAirports = data.get(code=OriginLocationCode).near_by_airports
        DestinationNearByAirports = data.get(code=DestinationLocationCode).near_by_airports
        if OriginNearByAirports:
            OriginLocationCode = data.get(code=OriginLocationCode).mapping_code
        if DestinationNearByAirports:
            DestinationLocationCode = data.get(code=DestinationLocationCode).mapping_code
    except:
        try:
            OriginNearByAirports = Airport.objects.get(code=OriginLocationCode).near_by_airports
            DestinationNearByAirports = Airport.objects.get(code=DestinationLocationCode).near_by_airports
            if OriginNearByAirports == True:
                OriginLocationCode = Airport.objects.get(code=OriginLocationCode).mapping_code
            if DestinationNearByAirports == True:
                DestinationLocationCode = Airport.objects.get(code=OriginLocationCode).mapping_code

        except Exception as ex:
            OriginNearByAirports = DestinationNearByAirports = False
    
    if len(OriginDestinationInformations) > 1:
        ArrivalLocationInfo = OriginDestinationInformations[1]
        ArrivalDateTime = ArrivalLocationInfo["DepartureDateTime"]
        ArrivalDate = ArrivalDateTime.split("T")[0]
        ArrivalTime = ArrivalDateTime.split("T")[1]

    if TravelPreferences["AirTripType"] == "Return":
        isReturn = True

    for PassengerTypeQuantity in PassengerTypeQuantities:
        if PassengerTypeQuantity["Code"] == PASSENGER_TYPE["adult"]:
            adults = PassengerTypeQuantity["Quantity"]

        elif PassengerTypeQuantity["Code"] == PASSENGER_TYPE["children"]:
            children = PassengerTypeQuantity["Quantity"]

        elif PassengerTypeQuantity["Code"] == PASSENGER_TYPE["infant"]:
            infants = PassengerTypeQuantity["Quantity"]

    search_url = f"{RYANAIR_SEARCH_API_ENDPOINT}?ADT={adults}&CHD={children}&" \
                 f"DateIn={ArrivalDate}&DateOut={DepartureDate}&Destination={DestinationLocationCode}&Disc=0&INF={infants}" \
                 f"&Origin={OriginLocationCode}&" \
                 f"TEEN=0&promoCode=&IncludeConnectingFlights=false&FlexDaysBeforeOut=2&" \
                 f"FlexDaysOut=2&FlexDaysBeforeIn=2&FlexDaysIn=2&OriginIsMac={OriginNearByAirports}&" \
                 f"DestinationIsMac={DestinationNearByAirports}&RoundTrip={isReturn}&ToUs=AGREED"

    required_data = {
        "website_search_url": search_url_and_other_req_info(validated_data)["search_url"],
        "search_url": search_url,
        "adults": adults,
        "children": children,
        "teens": teens,
        "infants": infants,
        "isReturn": isReturn
    }

    return required_data

