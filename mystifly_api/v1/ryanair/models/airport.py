import uuid
from django.db import models
from utils.models import TimeStampedModel
from .location import Country


class Airport(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid1, editable=False)
    name = models.CharField(max_length=255, null=True)
    country = models.ForeignKey(Country, on_delete=models.PROTECT, null=True)
    near_by_airports = models.BooleanField(default=False)
    code = models.CharField(max_length=255, null=True)
    mapping_code = models.CharField(max_length=255, null=True)

    def __str__(self):
        return f"{self.country}-{self.name}-{self.near_by_airports}-{self.code}-{self.mapping_code}"
