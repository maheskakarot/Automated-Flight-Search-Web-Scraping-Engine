import uuid
from django.db import models

class TimeStampedModelManager(models.Manager):
    def get_queryset(self):
        return super(TimeStampedModelManager, self).get_queryset().filter(is_deleted=False)


class TimeStampedModel(models.Model):
    created_on = models.DateTimeField(auto_now_add=True, db_column='created_on')
    updated_on = models.DateTimeField(auto_now=True, db_column='updated_on')
    is_deleted = models.BooleanField(default=False)

    objects = TimeStampedModelManager()

    class Meta:
        get_latest_by = 'updated_on'
        abstract = True
        default_permissions = ()



class Email_model(TimeStampedModel):
    email = models.EmailField(max_length=255)
    password = models.CharField(max_length=255)
    cookies = models.CharField(max_length=1000000)
    Airline_code = models.CharField(max_length=1000)

class client_config(TimeStampedModel):
    client_code = models.CharField(max_length=50)
    is_client_enabled = models.BooleanField(default=False)
    is_operations_enabled = models.BooleanField(default=False)
    service_type = models.CharField(max_length=50)


class client_emails(TimeStampedModel):
    client_code = models.CharField(max_length=50)
    email_id = models.EmailField(max_length=255)


class operations_internal_emails(TimeStampedModel):
    email_id = models.EmailField(max_length=255)
    is_ryanair_enabled = models.BooleanField(default=False)

class alert_schedules(TimeStampedModel):
    journey_start = models.DateTimeField()
    timezone = models.CharField(max_length=100)
    pnr = models.CharField(max_length=20)
    email_used = models.EmailField(max_length=255)
    client_code = models.CharField(max_length=20)
    origin_airport_code = models.CharField(max_length=20,default='LGW')



