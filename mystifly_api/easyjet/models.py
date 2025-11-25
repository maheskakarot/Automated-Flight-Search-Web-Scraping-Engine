from django.db import models
from custom_logger.models import TimeStampedModel


class SearchIdentifier(TimeStampedModel):

   
    search_identifier = models.CharField(max_length=255, primary_key=True)
   
    def __str__(self):
        return f"search_identifier {self.search_identifier}"
    
class SearchIDWebdriver(TimeStampedModel):

    search_identifier = models.ForeignKey(SearchIdentifier,on_delete=models.CASCADE, related_name='subscriber')
    url = models.URLField(null=True)
    session_id = models.CharField(max_length=255)
    reuse_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Search_identifier is {self.search_identifier} session id {self.session_id}"

class ProxySelection(TimeStampedModel):
    proxy = models.CharField(max_length=100)
    
class Nearby_airports(TimeStampedModel):
    created_by = models.EmailField()
    updated_by = models.EmailField()
    id = models.UUIDField(primary_key=True)
    airport_code = models.CharField(max_length=255)
    mapping_airport_code = models.CharField(max_length=255)
    meta_data = models.JSONField()
    
    