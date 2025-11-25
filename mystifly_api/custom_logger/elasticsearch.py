from elasticsearch import Elasticsearch
from django.conf import settings

es = Elasticsearch([settings.ELASTIC_SEARCH_HOST],
                   http_auth=(settings.ELASTIC_SEARCH_USER, settings.ELASTIC_SEARCH_PASS))
index = settings.ELASTIC_SEARCH_INDEX
