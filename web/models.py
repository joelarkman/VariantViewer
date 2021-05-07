import os
import json
from django.db import models
from db.models import VCF, SampleTranscriptVariant
from django.utils.translation import gettext_lazy as _
from easyaudit.models import CRUDEvent


@models.Field.register_lookup
class NotEqual(models.Lookup):
    # Create custom lookup to objects not equal (ne) to value.
    lookup_name = 'ne'

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        return '%s <> %s' % (lhs, rhs), params


# Create your models here.
class Filter(models.Model):
    # genekey = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=1000, blank=True,)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    class Match(models.TextChoices):
        ALL = 'all', _('Match all of the above rules')
        ANY = 'any', _('Match any of the above rules')

    match = models.CharField(
        max_length=15,
        choices=Match.choices,
        default=Match.ALL,
    )


class FilterItem(models.Model):
    filter = models.ForeignKey(
        Filter, related_name='items', on_delete=models.CASCADE)
    field = models.CharField(max_length=100)
    value = models.CharField(max_length=100)

    class FilterType(models.TextChoices):
        IS = '__iexact', _('is')
        # __ne is a custom lookup. See above.
        IS_NOT = '__ne', _('is not')
        CONTAINS = '__icontains', _('contains')
        LESS_THAN = '__lt', _('<')
        GREATER_THAN = '__gt', _('>')
        LESS_THAN_OR_EQUAL_TO = '__lte', _('≤')
        GREATER_THAN_OR_EQUAL_TO = '__gte', _('≥')

    filter_type = models.CharField(
        max_length=15,
        choices=FilterType.choices,
        default=FilterType.IS,
    )


class Document(models.Model):
    sample_transcript_variant = models.ForeignKey(
        SampleTranscriptVariant,
        on_delete=models.CASCADE,
        related_name='evidence_files'
    )
    description = models.CharField(max_length=1000, blank=True,)
    document = models.FileField(upload_to='documents/%Y/%m/%d/',)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    def extension(self):
        name, extension = os.path.splitext(self.document.name)
        return extension

    def filename(self):
        return os.path.basename(self.document.name)

    def get_user_created(self):
        try:
            crud = CRUDEvent.objects.filter(object_repr=self).first().user
        except:
            crud = None
        return crud


class Comment(models.Model):
    sample_transcript_variant = models.ForeignKey(
        SampleTranscriptVariant,
        on_delete=models.CASCADE,
        related_name='comments'
    )

    comment = models.CharField(max_length=2000, blank=True)

    # Choice field for run QC status
    class Classification(models.IntegerChoices):
        UNCLASSIFIED = 0
        PATHOGENIC = 1
        LIKELY_PATHOGENIC = 2
        VUS = 3
        LIKELY_BENIGN = 4
        BENIGN = 5

    classification = models.IntegerField(
        choices=Classification.choices,
        default=0,
    )

    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    def get_last_modified(self):
        cruds = CRUDEvent.objects.filter(object_repr=self)

        comment_events = []
        classification_events = []
        for crud in cruds:
            if crud.event_type == CRUDEvent.CREATE:
                data = json.loads(crud.object_json_repr)[0]
                if data['fields']['comment']:
                    comment_events.append(crud.id)
                classification_events.append(crud.id)
            elif crud.event_type == CRUDEvent.UPDATE:
                data = json.loads(crud.changed_fields)
                if data and 'comment' in data:
                    comment_events.append(crud.id)
                if data and 'classification' in data:
                    classification_events.append(crud.id)

        comment = CRUDEvent.objects.filter(id__in=comment_events).first()
        classification = CRUDEvent.objects.filter(
            id__in=classification_events).first()
        return {'comment': comment, 'classification': classification}

    def get_comment_history(self):
        cruds = CRUDEvent.objects.filter(object_repr=self)

        comment_events = []
        for crud in cruds:
            if crud.event_type == CRUDEvent.CREATE:
                data = json.loads(crud.object_json_repr)[0]
                if data['fields']['comment']:
                    comment_events.append(
                        {'type': 'create', 'user': crud.user, 'datetime': crud.datetime, 'value': data['fields']['comment']})
            elif crud.event_type == CRUDEvent.UPDATE:
                data = json.loads(crud.changed_fields)
                if data and 'comment' in data:
                    comment_events.append(
                        {'type': 'update', 'user': crud.user, 'datetime': crud.datetime, 'value_previous': data['comment'][0], 'value': data['comment'][1]})

        return comment_events
