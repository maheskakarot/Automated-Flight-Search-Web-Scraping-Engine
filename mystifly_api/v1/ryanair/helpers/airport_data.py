import csv
from utils.google_sheet import SheetClient
from v1.ryanair.models import Country, Airport


def populate_airport_data(sheet_name, tab_name):
    """
    Previously we scraped the airports name, country and airport codes from Ryanair website and exported in a
    google sheet. So this function will add all those details into our DB.
    """

    airports_data_sheet_ob = SheetClient().get_sheet_instance(sheet_name, tab_name)
    airports_data = airports_data_sheet_ob.get_all_records()
    # import pdb;pdb.set_trace()
    # keys = airports_data[0].keys()
    # with open('ryanair_airports_input_data.csv', 'w', newline='') as output_file:
    #     dict_writer = csv.DictWriter(output_file, keys)
    #     dict_writer.writeheader()
    #     dict_writer.writerows(airports_data)

    for airport_data in airports_data:
        near_by_airports = False

        country = airport_data['Country Name']
        name = airport_data['Airport Name']
        code = airport_data['Airport Code']

        if 'All Airports' in name:
            near_by_airports = True

        country_obj, is_created = Country.objects.get_or_create(name=country)

        airport_obj, is_created = Airport.objects.get_or_create(
            name=name,
            country=country_obj,
            near_by_airports=near_by_airports,
            code=code
        )

def populate_airport_data_from_csvsheet(file=None):
    with open('ryanair_airports_input_data.csv', 'r', encoding='iso-8859-1') as f:
        next(f)
        reader = csv.reader(f)
        for row in reader:
            near_by_airports = False
            country = row[0]
            name = row[1]
            code = row[2]
            mapping_code = row[3]
            if code == mapping_code:
                near_by_airports = False
            else:
                near_by_airports = True
            if 'All Airports' in name:
                near_by_airports = True

            country_obj, is_created = Country.objects.get_or_create(name=country)
            airport_obj, is_created = Airport.objects.get_or_create(
                name=name,
                country=country_obj,
                near_by_airports=near_by_airports,
                code=code,
                mapping_code=mapping_code
            )