FARE_TYPE_BUTTON_CODES = {
    'VALUE_FARE': 'VF',
    'REGULAR_FARE': 'RF',
    'PLUS_FARE': 'PF',
    'FAMILY_PLUS_FARE': 'FMPF',
    'FLEXI_PLUS_FARE': 'FPF',
}


VALUE_FARE_DATA = {
    "fare_type": "Value",
    "fare_desc": "Travel light",
    "ancillaries": [
        {
            "ancillary_name": "1 small bag only",
            "ancillary_desc": "Must fit under the seat(40cm x 20cm x 25cm)"
        }
    ],
    "fare_currency": {},
    "fare_value": {}
}

REGULAR_FARE_DATA = {
    "fare_type": "Regular",
    "fare_desc": "Great for short trips",
    "ancillaries": [
        {
            "ancillary_name": "Priority & 2 Cabin Bags",
            "ancillary_desc": "Board first, 10kg Cabin Bag and 1 Small Bag"
        },
        {
            "ancillary_name": "Reserved Seat",
            "ancillary_desc": "Specific rows available"
        }
    ],
    "fare_currency": {},
    "fare_value": {}
}

PLUS_FARE_DATA = {
    "fare_type": "Plus",
    "fare_desc": "Includes 20kg Check-in Bag",
    "ancillaries": [
        {
            "ancillary_name": "1 small bag only",
            "ancillary_desc": "Must fit under the seat(40cm x 20cm x 25cm)"
        },
        {
            "ancillary_name": "Reserved Seat",
            "ancillary_desc": "Specific rows available"
        },
        {
            "ancillary_name": "20kg Check-in Bag",
            "ancillary_desc": "Drop bag at check-in desk"
        },
        {
            "ancillary_name": "Free check-in at the airport",
            "ancillary_desc": "Up to 40 minutes before your flight"
        }
    ],
    "fare_currency": {},
    "fare_value": {}
}

FLEXI_PLUS_FARE_DATA = {
    "fare_type": "Flexi Plus",
    "fare_desc": "If your plans change, so can your booking",
    "ancillaries": [
        {
            "ancillary_name": "Flight Change",
            "ancillary_desc": "No flight change fee when changing flight online (up to 2.5 hrs pre-departure) or at the airport (up to 40 mins pre-departure)"
        },
        {
            "ancillary_name": "Fare difference",
            "ancillary_desc": "Only pay the fare difference if applicable"
        }
    ],
    "also_includes": [
        {
            "bags": "Priority & 2 Cabin Bags"
        },
        {
            "seat_type": "Reserve any seat type"
        },
        {
            "fast_track": "Fast Track through security"
        },
        {
            "check_in": "Free check-in at the airport"
        }
    ],
    "fare_currency": {},
    "fare_value": {}
}

FAMILY_PLUS_FARE_DATA = {
    "fare_type": "Family Plus",
    "fare_desc": "Recommended for you!",
    "ancillaries": [
        {
            "ancillary_name": "1 small bag only",
            "ancillary_desc": "Must fit under the seat(40cm x 20cm x 25cm)"
        },
        {
            "ancillary_name": "Free seats for kids under 12",
            "ancillary_desc": "For up to 4 kids on your booking"
        },
        {
            "ancillary_name": "10kg Check-in Bag for all",
            "ancillary_desc": "Must be dropped at check-in desk"
        },
        {
            "ancillary_name": "1 x 20kg Check-in Bag",
            "ancillary_desc": "1 large Check-in Bag for your family trip"
        },
    ],
    "fare_currency": {},
    "fare_value": {}
}
