import asyncio
import json
import aiohttp
from asgiref import sync
import requests
from .proxy import proxyDict, HEADERS, MAX_TRY
from .urls import URLS


def create_basket():
    basket_id = None
    request_hit = 0

    query = """
            mutation CreateBasket {
          createBasket {
            ...BasketCommon
            gettingAround {
              ...GettingAroundPillar
            }
            thingsToDo {
              ...ThingsToDoPillar
            }
          }
        }
        
        
        fragment TotalCommon on PriceType {
          total
        }
        
        fragment PriceCommon on PriceType {
          amountWithTaxes
          total
          discount
          discountCode
        }
        
        fragment ComponentCommon on ComponentType {
          id
          parentId
          code
          type
          quantity
          removable
          price {
            ...PriceCommon
          }
        }
        
        fragment VariantUnionAddOn on VariantUnionType {
          ... on AddOn {
            itemId
            provider
            paxNumber
            pax
            src
            start
            end
          }
        }
        
        fragment VariantUnionFare on VariantUnionType {
          ... on Fare {
            fareOption
            journeyNumber
          }
        }
        
        fragment VariantUnionSsr on VariantUnionType {
          ... on Ssr {
            journeyNumber
            paxNumber
            segmentNumber
          }
        }
        
        fragment VariantUnionSeat on VariantUnionType {
          ... on Seat {
            paxNumber
            journeyNumber
            segmentNumber
            seatType
            designator
            childSeatsWithAdult
            hasAdditionalSeatCost
          }
        }
        
        fragment VariantUnionBundle on VariantUnionType {
          ... on Bundle {
            journeyNumber
            segmentNumber
          }
        }
        
        fragment VariantUnionVoucher on VariantUnionType {
          ... on Voucher {
            firstName
            lastName
            email
          }
        }
        
        fragment VariantUnionPhysicalVoucher on VariantUnionType {
          ... on PhysicalVoucher {
            sequenceNumber
            firstName
            lastName
            address1
            address2
            city
            postalCode
            country
            scheduleDate
            message
          }
        }
        
        fragment VariantUnionDigitalVoucher on VariantUnionType {
          ... on DigitalVoucher {
            sequenceNumber
            firstName
            lastName
            email
            theme
            scheduleDate
            scheduleTime
            message
          }
        }
        
        fragment VariantGroundTransfer on VariantUnionType {
          ... on GroundTransfer {
            locationPickUp
            locationDropOff
            routeType
            startDate
            endDate
            itemId
            location
          }
        }
        
        fragment GettingTherePillar on GettingThereType {
          price {
            ...TotalCommon
          }
          journeys {
            ... on JourneyType {
              arrival
              departure
              destination
              duration
              fareClass
              fareKey
              fareOption
              flightKey
              flightNumber
              isConnecting
              isDomestic
              journeyNum
              origin
              segments {
                ... on SegmentType {
                  aircraft
                  arrival
                  departure
                  destination
                  duration
                  hasGovernmentTax
                  flightNumber
                  segmentNum
                  origin
                  originCountry
                  destinationCountry
                }
              }
            }
          }
          discounts {
            ... on DiscountType {
              amount
              code
              journeyNum
              percentage
              zone
              description
              qty
            }
          }
          taxes {
            ... on TaxType {
              amount
              code
              journeyNum
              percentage
              zone
            }
          }
          vouchers {
            ... on VoucherType {
              amount
              code
              status
              accountNumber
            }
          }
          components {
            ... on ComponentType {
              ...ComponentCommon
              variant {
                ...VariantUnionAddOn
                ...VariantUnionFare
                ...VariantUnionSsr
                ...VariantUnionSeat
                ...VariantGroundTransfer
                ...VariantUnionBundle
                ...VariantUnionVoucher
                ...VariantUnionDigitalVoucher
                ...VariantUnionPhysicalVoucher
              }
            }
          }
          messages {
            ... on MessageType {
              type
              journeyNum
              key
              message
            }
          }
        }
        
        fragment StayingTherePillar on StayingThereType {
          price {
            ...TotalCommon
          }
          components {
            ...ComponentCommon
            price {
              ...PriceCommon
              fat
              amount
            }
            payLater {
              ...PriceCommon
              fat
              amount
            }
            variant {
              ... on Hotel {
                hotelName
                reservationDescription
                countryCode
                city
                startDate
                endDate
                provider
                propertySurcharges {
                  ... on PropertySurcharges {
                    type
                    price
                  }
                }
                guestTotals {
                  adults
                  children
                }
                reservationInfo {
                  rooms {
                    ... on HotelRoomReservationInfo {
                      roomAllocation {
                        adultCount
                        childAges
                      }
                    }
                  }
                }
              }
            }
          }
          payLater {
            total
          }
        }
        
        fragment PayLaterCommon on PriceType {
          total
        }
        
        fragment BasketCommon on BasketType {
          id
          tripId
          dotrezSessionId
          currency
          gettingThere {
            ...GettingTherePillar
          }
          stayingThere {
            ...StayingTherePillar
          }
          price {
            ...TotalCommon
          }
          payLater {
            ...PayLaterCommon
          }
          totalToPay
        }
        
        fragment VariantCar on VariantUnionType {
          ... on Car {
            rentPrice
            carName
            refId
            engineLoadId
            pickUpTime
            pickUpLocation {
              countryCode
              code
              name
            }
            dropOffTime
            dropOffLocation {
              countryCode
              code
              name
            }
            insurance
            extras {
              totalPrice
              includedInRate
              code
              price
              selected
              type
            }
            residence
            age
          }
        }
        
        fragment VariantCarRental on VariantUnionType {
          ... on CarRental {
            rentPrice
            carName
            clientId
            refId
            pickUpTime
            pickUpLocation {
              countryCode
              code
              name
            }
            dropOffTime
            dropOffLocation {
              countryCode
              code
              name
            }
            insurance
            extras {
              totalPrice
              includedInRate
              code
              price
              selected
              type
              payNow
            }
            residence
            age
            searchId
          }
        }
        
        fragment GettingAroundPillar on GettingAroundType {
          price {
            amount
            discount
            amountWithTaxes
            total
          }
          payLater {
            ...PayLaterCommon
          }
          taxes {
            amount
          }
          components {
            ...ComponentCommon
            payLater {
              amountWithTaxes
              total
            }
            variant {
              ...VariantCar
              ...VariantCarRental
              ...VariantGroundTransfer
            }
          }
        }
        
        fragment ThingsToDoPillar on ThingsToDoType {
          price {
            amount
            discount
            amountWithTaxes
            total
          }
          taxes {
            amount
          }
          components {
            ...ComponentCommon
            variant {
              ... on Ticket {
                name
                reservationCode
                activityTime
                address
              }
            }
          }
        }
    """

    while request_hit < MAX_TRY:

        response = requests.post(url=URLS['CREATE_BASKET'], json={"query": query}, headers=HEADERS, proxies=proxyDict)

        if response.status_code == 200:
            basket_id = response.json()['data']['createBasket']['id']
            break

        request_hit += 1

    return basket_id


def create_booking(request_data):
    flights = []

    departure_flights_data = {
        "fareKey": request_data['departureFareKey'],
        "flightKey": request_data['departureFlightKey'],
        "fareOption": None
    }
    flights.append(departure_flights_data)

    if request_data['arrivalFareKey']:
        arrival_flights_data = {
            "fareKey": request_data['arrivalFareKey'],
            "flightKey": request_data['arrivalFlightKey'],
            "fareOption": None
        }
        flights.append(arrival_flights_data)

    payload = json.dumps({
        "query": "mutation CreateBooking($basketId: String, $createBooking: CreateBookingInput!, $culture: String!) {\n  createBooking(basketId: $basketId, createBooking: $createBooking, culture: $culture) {\n    ...BasketCommon\n  }\n}\n\n\nfragment TotalCommon on PriceType {\n  total\n}\n\nfragment PriceCommon on PriceType {\n  amountWithTaxes\n  total\n  discount\n  discountCode\n}\n\nfragment ComponentCommon on ComponentType {\n  id\n  parentId\n  code\n  type\n  quantity\n  removable\n  price {\n    ...PriceCommon\n  }\n}\n\nfragment VariantUnionAddOn on VariantUnionType {\n  ... on AddOn {\n    itemId\n    provider\n    paxNumber\n    pax\n    src\n    start\n    end\n  }\n}\n\nfragment VariantUnionFare on VariantUnionType {\n  ... on Fare {\n    fareOption\n    journeyNumber\n  }\n}\n\nfragment VariantUnionSsr on VariantUnionType {\n  ... on Ssr {\n    journeyNumber\n    paxNumber\n    segmentNumber\n  }\n}\n\nfragment VariantUnionSeat on VariantUnionType {\n  ... on Seat {\n    paxNumber\n    journeyNumber\n    segmentNumber\n    seatType\n    designator\n    childSeatsWithAdult\n    hasAdditionalSeatCost\n  }\n}\n\nfragment VariantUnionBundle on VariantUnionType {\n  ... on Bundle {\n    journeyNumber\n    segmentNumber\n  }\n}\n\nfragment VariantUnionVoucher on VariantUnionType {\n  ... on Voucher {\n    firstName\n    lastName\n    email\n  }\n}\n\nfragment VariantUnionPhysicalVoucher on VariantUnionType {\n  ... on PhysicalVoucher {\n    sequenceNumber\n    firstName\n    lastName\n    address1\n    address2\n    city\n    postalCode\n    country\n    scheduleDate\n    message\n  }\n}\n\nfragment VariantUnionDigitalVoucher on VariantUnionType {\n  ... on DigitalVoucher {\n    sequenceNumber\n    firstName\n    lastName\n    email\n    theme\n    scheduleDate\n    scheduleTime\n    message\n  }\n}\n\nfragment VariantGroundTransfer on VariantUnionType {\n  ... on GroundTransfer {\n    locationPickUp\n    locationDropOff\n    routeType\n    startDate\n    endDate\n    itemId\n    location\n  }\n}\n\nfragment GettingTherePillar on GettingThereType {\n  price {\n    ...TotalCommon\n  }\n  journeys {\n    ... on JourneyType {\n      arrival\n      departure\n      destination\n      duration\n      fareClass\n      fareKey\n      fareOption\n      flightKey\n      flightNumber\n      isConnecting\n      isDomestic\n      journeyNum\n      origin\n      segments {\n        ... on SegmentType {\n          aircraft\n          arrival\n          departure\n          destination\n          duration\n          hasGovernmentTax\n          flightNumber\n          segmentNum\n          origin\n          originCountry\n          destinationCountry\n        }\n      }\n    }\n  }\n  discounts {\n    ... on DiscountType {\n      amount\n      code\n      journeyNum\n      percentage\n      zone\n      description\n      qty\n    }\n  }\n  taxes {\n    ... on TaxType {\n      amount\n      code\n      journeyNum\n      percentage\n      zone\n    }\n  }\n  vouchers {\n    ... on VoucherType {\n      amount\n      code\n      status\n      accountNumber\n    }\n  }\n  components {\n    ... on ComponentType {\n      ...ComponentCommon\n      variant {\n        ...VariantUnionAddOn\n        ...VariantUnionFare\n        ...VariantUnionSsr\n        ...VariantUnionSeat\n        ...VariantGroundTransfer\n        ...VariantUnionBundle\n        ...VariantUnionVoucher\n        ...VariantUnionDigitalVoucher\n        ...VariantUnionPhysicalVoucher\n      }\n    }\n  }\n  messages {\n    ... on MessageType {\n      type\n      journeyNum\n      key\n      message\n    }\n  }\n}\n\nfragment StayingTherePillar on StayingThereType {\n  price {\n    ...TotalCommon\n  }\n  components {\n    ...ComponentCommon\n    price {\n      ...PriceCommon\n      fat\n      amount\n    }\n    payLater {\n      ...PriceCommon\n      fat\n      amount\n    }\n    variant {\n      ... on Hotel {\n        hotelName\n        reservationDescription\n        countryCode\n        city\n        startDate\n        endDate\n        provider\n        propertySurcharges {\n          ... on PropertySurcharges {\n            type\n            price\n          }\n        }\n        guestTotals {\n          adults\n          children\n        }\n        reservationInfo {\n          rooms {\n            ... on HotelRoomReservationInfo {\n              roomAllocation {\n                adultCount\n                childAges\n              }\n            }\n          }\n        }\n      }\n    }\n  }\n  payLater {\n    total\n  }\n}\n\nfragment PayLaterCommon on PriceType {\n  total\n}\n\nfragment BasketCommon on BasketType {\n  id\n  tripId\n  dotrezSessionId\n  currency\n  gettingThere {\n    ...GettingTherePillar\n  }\n  stayingThere {\n    ...StayingTherePillar\n  }\n  price {\n    ...TotalCommon\n  }\n  payLater {\n    ...PayLaterCommon\n  }\n  totalToPay\n}\n\n",
        "variables": {
            "basketId": request_data['basketId'],
            "createBooking": {
                "adults": request_data['adults'],
                "children": request_data['children'],
                "infants": request_data['infants'],
                "teens": 0,
                "flights": flights,
                "discount": 0,
                "promoCode": ""
            },
            "culture": "en-gb"
        },
        "operationName": "CreateBooking"
    })

    url = URLS['CREATE_BOOKING']

    headers = {
        'Content-Type': 'application/json',
    }

    response = requests.request("POST", url, headers=headers, data=payload, proxies=proxyDict)

    if response.status_code == 200:
        response = response.json()

    return response


def async_aiohttp_get_all(payloads_data):
    url = URLS['CREATE_BOOKING']

    headers = {
        'Content-Type': 'application/json',
    }

    async def get_all():
        async with aiohttp.ClientSession() as session:
            async def fetch(payload):
                async with session.post(url, headers=headers, data=payload, proxy=proxyDict["https"]) as res:
                    try:
                        return await res.json()
                    except:
                        return None

            return await asyncio.gather(*[
                fetch(payload) for payload in payloads_data
            ])

    return sync.async_to_sync(get_all)()


def create_multiple_bookings_v2(multiple_requests_data):
    bookings_data = {}
    payloads_data = []

    for request_data in multiple_requests_data:
        flights = []
        departure_flights_data = {
            "fareKey": request_data['departureFareKey'],
            "flightKey": request_data['departureFlightKey'],
            "fareOption": None
        }
        flights.append(departure_flights_data)

        if request_data['arrivalFareKey']:
            arrival_flights_data = {
                "fareKey": request_data['arrivalFareKey'],
                "flightKey": request_data['arrivalFlightKey'],
                "fareOption": None
            }
            flights.append(arrival_flights_data)

        payload = json.dumps({
            "query": "mutation CreateBooking($basketId: String, $createBooking: CreateBookingInput!, $culture: String!) {\n  createBooking(basketId: $basketId, createBooking: $createBooking, culture: $culture) {\n    ...BasketCommon\n  }\n}\n\n\nfragment TotalCommon on PriceType {\n  total\n}\n\nfragment PriceCommon on PriceType {\n  amountWithTaxes\n  total\n  discount\n  discountCode\n}\n\nfragment ComponentCommon on ComponentType {\n  id\n  parentId\n  code\n  type\n  quantity\n  removable\n  price {\n    ...PriceCommon\n  }\n}\n\nfragment VariantUnionAddOn on VariantUnionType {\n  ... on AddOn {\n    itemId\n    provider\n    paxNumber\n    pax\n    src\n    start\n    end\n  }\n}\n\nfragment VariantUnionFare on VariantUnionType {\n  ... on Fare {\n    fareOption\n    journeyNumber\n  }\n}\n\nfragment VariantUnionSsr on VariantUnionType {\n  ... on Ssr {\n    journeyNumber\n    paxNumber\n    segmentNumber\n  }\n}\n\nfragment VariantUnionSeat on VariantUnionType {\n  ... on Seat {\n    paxNumber\n    journeyNumber\n    segmentNumber\n    seatType\n    designator\n    childSeatsWithAdult\n    hasAdditionalSeatCost\n  }\n}\n\nfragment VariantUnionBundle on VariantUnionType {\n  ... on Bundle {\n    journeyNumber\n    segmentNumber\n  }\n}\n\nfragment VariantUnionVoucher on VariantUnionType {\n  ... on Voucher {\n    firstName\n    lastName\n    email\n  }\n}\n\nfragment VariantUnionPhysicalVoucher on VariantUnionType {\n  ... on PhysicalVoucher {\n    sequenceNumber\n    firstName\n    lastName\n    address1\n    address2\n    city\n    postalCode\n    country\n    scheduleDate\n    message\n  }\n}\n\nfragment VariantUnionDigitalVoucher on VariantUnionType {\n  ... on DigitalVoucher {\n    sequenceNumber\n    firstName\n    lastName\n    email\n    theme\n    scheduleDate\n    scheduleTime\n    message\n  }\n}\n\nfragment VariantGroundTransfer on VariantUnionType {\n  ... on GroundTransfer {\n    locationPickUp\n    locationDropOff\n    routeType\n    startDate\n    endDate\n    itemId\n    location\n  }\n}\n\nfragment GettingTherePillar on GettingThereType {\n  price {\n    ...TotalCommon\n  }\n  journeys {\n    ... on JourneyType {\n      arrival\n      departure\n      destination\n      duration\n      fareClass\n      fareKey\n      fareOption\n      flightKey\n      flightNumber\n      isConnecting\n      isDomestic\n      journeyNum\n      origin\n      segments {\n        ... on SegmentType {\n          aircraft\n          arrival\n          departure\n          destination\n          duration\n          hasGovernmentTax\n          flightNumber\n          segmentNum\n          origin\n          originCountry\n          destinationCountry\n        }\n      }\n    }\n  }\n  discounts {\n    ... on DiscountType {\n      amount\n      code\n      journeyNum\n      percentage\n      zone\n      description\n      qty\n    }\n  }\n  taxes {\n    ... on TaxType {\n      amount\n      code\n      journeyNum\n      percentage\n      zone\n    }\n  }\n  vouchers {\n    ... on VoucherType {\n      amount\n      code\n      status\n      accountNumber\n    }\n  }\n  components {\n    ... on ComponentType {\n      ...ComponentCommon\n      variant {\n        ...VariantUnionAddOn\n        ...VariantUnionFare\n        ...VariantUnionSsr\n        ...VariantUnionSeat\n        ...VariantGroundTransfer\n        ...VariantUnionBundle\n        ...VariantUnionVoucher\n        ...VariantUnionDigitalVoucher\n        ...VariantUnionPhysicalVoucher\n      }\n    }\n  }\n  messages {\n    ... on MessageType {\n      type\n      journeyNum\n      key\n      message\n    }\n  }\n}\n\nfragment StayingTherePillar on StayingThereType {\n  price {\n    ...TotalCommon\n  }\n  components {\n    ...ComponentCommon\n    price {\n      ...PriceCommon\n      fat\n      amount\n    }\n    payLater {\n      ...PriceCommon\n      fat\n      amount\n    }\n    variant {\n      ... on Hotel {\n        hotelName\n        reservationDescription\n        countryCode\n        city\n        startDate\n        endDate\n        provider\n        propertySurcharges {\n          ... on PropertySurcharges {\n            type\n            price\n          }\n        }\n        guestTotals {\n          adults\n          children\n        }\n        reservationInfo {\n          rooms {\n            ... on HotelRoomReservationInfo {\n              roomAllocation {\n                adultCount\n                childAges\n              }\n            }\n          }\n        }\n      }\n    }\n  }\n  payLater {\n    total\n  }\n}\n\nfragment PayLaterCommon on PriceType {\n  total\n}\n\nfragment BasketCommon on BasketType {\n  id\n  tripId\n  dotrezSessionId\n  currency\n  gettingThere {\n    ...GettingTherePillar\n  }\n  stayingThere {\n    ...StayingTherePillar\n  }\n  price {\n    ...TotalCommon\n  }\n  payLater {\n    ...PayLaterCommon\n  }\n  totalToPay\n}\n\n",
            "variables": {
                "basketId": request_data['basketId'],
                "createBooking": {
                    "adults": request_data['adults'],
                    "children": request_data['children'],
                    "infants": request_data['infants'],
                    "teens": 0,
                    "flights": flights,
                    "discount": 0,
                    "promoCode": ""
                },
                "culture": "en-gb"
            },
            "operationName": "CreateBooking"
        })

        payloads_data.append(payload)

    responses = async_aiohttp_get_all(payloads_data)

    for r_response in responses:
        if r_response:
            create_booking_response = r_response['data']['createBooking']
            flight_key = create_booking_response['gettingThere']['journeys'][0]['flightKey']
            if len(create_booking_response['gettingThere']['journeys']) > 1:
                flight_key = "{}-{}".format(flight_key, create_booking_response['gettingThere']['journeys'][1]['flightKey'])
            bookings_data[flight_key] = create_booking_response

    return bookings_data
