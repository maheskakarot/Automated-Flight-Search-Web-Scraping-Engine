from django.core.cache import cache
from v1.ryanair.models import Airport

def load_data_into_cache():
    data = Airport.objects.all()
    cache.set('cached_data', data)
    return data