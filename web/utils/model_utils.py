from django.db import models
from easyaudit.models import CRUDEvent
import json


class BaseModel(models.Model):
    """Abstract base model to provide auto-date fields on children
    """
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        app_label = 'web'


def LastUpdated(object, fields=None):

    events = {}
    cruds = CRUDEvent.objects.filter(
        object_repr=object, event_type=CRUDEvent.UPDATE)

    latest = cruds.first()

    events['latest'] = {'type': 'update',
                        'user': latest.user, 'datetime': latest.datetime}

    if fields:
        fields = fields if isinstance(fields, list) else [fields]
        field_latest = {}
        for field in fields:
            temp = []
            for crud in cruds:
                data = json.loads(crud.changed_fields)
                if data and field in data:
                    temp.append({'type': 'update', 'user': crud.user, 'datetime': crud.datetime,
                                 'value_previous': data[field][0], 'value': data[field][1]})

            temp = sorted(temp, key=lambda k: k['datetime'], reverse=True)[0]
            field_latest[field] = temp

        events['fields'] = field_latest

    return events
