import csv
from easyjet.models import Nearby_airports
def populate_airport_data_from_csvsheet(file=None):
    with open('easyjet_nearby_airports.csv', 'r', encoding='iso-8859-1') as f:
        next(f)
        reader = csv.reader(f)
        for row in reader:
            created_by = row[3]
            updated_by = row[4]
            id_ = row[5]
            airport_code = row[6]
            mapping_airport_code = row[7]
            meta_data = row[8]
            Nearby_airports.objects.get_or_create(
                created_by=created_by,
                updated_by=updated_by,
                id=id_,
                airport_code=airport_code,
                mapping_airport_code=mapping_airport_code,
                meta_data=meta_data
            )