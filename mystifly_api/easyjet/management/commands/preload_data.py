from django.core.management.base import BaseCommand
from easyjet.models import Nearby_airports  # Import your model
from easyjet import static_data

class Command(BaseCommand):
    # help = 'Preload data from the database into static memory'
    
    def handle(self, *args, **options):
        data = {}  # Use a dictionary to store data in static memory
        queryset = Nearby_airports.objects.all()  # Retrieve data from the database
        # for item in queryset:
        #     data[item.airport_code] = {
        #         'mapping_code': item.mapping_airport_code,
        #         'meta_data': item.meta_data,
        #     }         
        static_data.data = queryset
        
