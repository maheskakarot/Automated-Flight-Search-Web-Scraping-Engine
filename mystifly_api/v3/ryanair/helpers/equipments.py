def validate_equipments_select_payload(payload):
    message = None

    result_id = payload.get("ResultId", None)

    if not result_id:
        message = "Result Id is missing, Please add to continue"
        return message

    result_id_items = result_id.split("-")

    if len(result_id_items) != 6 and len(result_id_items) != 4:
        message = "Result Id is not valid, Please enter correct id to continue"
        return message

    equipments_data = payload.get("EquipmentsData", [])

    if equipments_data:

        for equipment_data in equipments_data:
            equipment_name = equipment_data["Name"]
            departure_flight_data = equipment_data.get("DepartureFlightData", [])
            arrival_flight_data = equipment_data.get("ArrivalFlightData", [])

            if departure_flight_data:
                message = check_flight_wise_validity(equipment_name, departure_flight_data)

                if message:
                    return message

            if arrival_flight_data:
                message = check_flight_wise_validity(equipment_name, arrival_flight_data)

                if message:
                    return message

    return message


def check_flight_wise_validity(equipment_name, flight_data):
    message = None

    passengers_info = flight_data.get("PassengersInfo", [])

    if passengers_info:

        for passenger_info in passengers_info:
            passenger_name = passenger_info['Name']
            quantity = passenger_info['Quantity']

            if quantity < 0:
                message = f"Equipment Name - {equipment_name}, Passenger Name - {passenger_name}, " \
                          f"Quantity can't be in negative."
                return message

            max_limit = get_max_limit(equipment_name)

            if quantity > max_limit:
                message = f"Equipment Name - {equipment_name}, Passenger Name - {passenger_name}, " \
                          f"Quantity can't more than max limit. Max limit is {max_limit}"
                return message

    return message


def get_max_limit(equipment_name):
    SPORTS_EQUIPMENTS = ["bike", "golf", "ski", "large sports", "other sports"]

    EQUIPMENTS_LIMIT = {
        'SPORTS': 2,
        'MUSIC': 2,
        'BABY': 3
    }

    if equipment_name.lower() in SPORTS_EQUIPMENTS:
        max_limit = EQUIPMENTS_LIMIT['SPORTS']

    elif "music" in equipment_name.lower():
        max_limit = EQUIPMENTS_LIMIT['MUSIC']

    else:
        max_limit = EQUIPMENTS_LIMIT['BABY']

    return max_limit
