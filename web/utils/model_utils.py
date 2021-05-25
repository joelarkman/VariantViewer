from django.db import models


class BaseModel(models.Model):
    """Abstract base model to provide auto-date fields on children
    """
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        app_label = 'web'
