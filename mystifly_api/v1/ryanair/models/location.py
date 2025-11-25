import uuid
from django.db import models
from utils.models import TimeStampedModel


class Country(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid1, editable=False)
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name
