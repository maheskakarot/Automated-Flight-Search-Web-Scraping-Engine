from v1.ryanair.constants.fares_data import FARE_TYPE_BUTTON_CODES


def validate_baggages_select_payload(payload):
    message = None
    twenty_kg_check_bag_name = "20kg Check-in Bag"
    check_in_bag_limit = 3

    result_id = payload.get("ResultId", None)

    if not result_id:
        return "Result Id is missing, Please add to continue"

    result_id_items = result_id.split("-")

    if len(result_id_items) == 6:
        is_return_trip = True

    elif len(result_id_items) == 4:
        is_return_trip = False

    else:
        message = "Result Id is not valid, Please enter correct id to continue"
        return message

    fare_type = result_id_items[-1]

    cabin_bags_data = payload.get("CabinBags", {})

    if not cabin_bags_data and fare_type not in [FARE_TYPE_BUTTON_CODES['REGULAR_FARE'],
                                                 FARE_TYPE_BUTTON_CODES['FLEXI_PLUS_FARE']]:
        message = "Cabin Bags data is missing, Please add to continue"
        return message

    check_in_bags_data = payload.get("CheckInBags", {})

    if check_in_bags_data:
        dept_check_in_bags_data = check_in_bags_data.get("DepartureFlightData", {})
        arvl_check_in_bags_data = check_in_bags_data.get("ArrivalFlightData", {})

        if dept_check_in_bags_data:
            dept_products_info = dept_check_in_bags_data.get("ProductsInfo", [])

            if dept_products_info:
                for dept_product_info in dept_products_info:
                    product_name = dept_product_info["Name"]

                    if product_name.lower() == twenty_kg_check_bag_name.lower():
                        passengers_info = dept_product_info.get("PassengersInfo", [])

                        if passengers_info:
                            for passenger_info in passengers_info:
                                passenger_name = passenger_info["Name"]
                                is_add = passenger_info["Add"]
                                quantity = passenger_info["Quantity"]

                                if quantity > check_in_bag_limit and is_add:
                                    message = f"Twenty kg Check in bags are selected more than the limit for passenger " \
                                              f"name - {passenger_name} in DepartureFlightData. Limit is {check_in_bag_limit}"

                                    return message

        if arvl_check_in_bags_data:
            arvl_products_info = dept_check_in_bags_data.get("ProductsInfo", [])

            if arvl_products_info:
                for arvl_product_info in arvl_products_info:
                    product_name = arvl_product_info["Name"]

                    if product_name.lower() == twenty_kg_check_bag_name.lower():
                        passengers_info = arvl_product_info.get("PassengersInfo", [])

                        if passengers_info:
                            for passenger_info in passengers_info:
                                passenger_name = passenger_info["Name"]
                                is_add = passenger_info["Add"]
                                quantity = passenger_info["Quantity"]

                                if quantity > check_in_bag_limit and is_add:
                                    message = f"Twenty kg Check in bags are selected more than the limit for passenger " \
                                              f"name - {passenger_name} in ArrivalFlightData. Limit is {check_in_bag_limit}"

                                    return message

    return message
