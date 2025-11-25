def check_valid_request(request_data):
    departure_valid = True
    arrival_valid = True

    fast_track_info = request_data.get("FastTrackInfo", {})

    if fast_track_info:
        departure_flight = fast_track_info.get("DepartureFlight", {})

        if departure_flight:
            if not departure_flight.get('AddToAll', False):
                departure_valid = False

                passengers_info = departure_flight.get('PassengersInfo', [])
                for passenger_info in passengers_info:
                    passenger_code = passenger_info['Code']
                    fast_track_status = passenger_info['AddFastTrack']

                    if (passenger_code == "ADT" or passenger_code == "INF") and fast_track_status:
                        departure_valid = True

        arrival_flight = fast_track_info.get("ArrivalFlight", {})

        if arrival_flight:

            if not arrival_flight.get('AddToAll', False):
                arrival_valid = False

                passengers_info = arrival_flight.get('PassengersInfo', [])
                for passenger_info in passengers_info:
                    passenger_code = passenger_info['Code']
                    fast_track_status = passenger_info['AddFastTrack']

                    if (passenger_code == "ADT" or passenger_code == "INF") and fast_track_status:
                        arrival_valid = True

    return departure_valid, arrival_valid

