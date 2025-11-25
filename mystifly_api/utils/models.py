from django.db import models


class TimeStampedModelManager(models.Manager):
    def get_queryset(self):
        return super(TimeStampedModelManager, self).get_queryset().filter(is_deleted=False)


class TimeStampedModel(models.Model):
    """ TimeStampedModel
        An abstract base class model that provides self-managed "created" and
       "modified" fields.
    """

    created_on = models.DateTimeField(auto_now_add=True, db_column='created_on')
    updated_on = models.DateTimeField(auto_now=True, db_column='updated_on')
    is_deleted = models.BooleanField(default=False)

    objects = TimeStampedModelManager()

    class Meta:
        get_latest_by = 'updated_on'
        abstract = True
        default_permissions = ()
