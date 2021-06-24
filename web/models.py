import os
import json
from django.db import models
from web.utils.model_utils import BaseModel
from db.models import Run, SamplesheetSample, SampleTranscriptVariant
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
class Filter(BaseModel):
    # genekey = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=1000, blank=True,)

    class Match(models.TextChoices):
        ALL = 'all', _('Match all of the above rules')
        ANY = 'any', _('Match any of the above rules')

    match = models.CharField(
        max_length=15,
        choices=Match.choices,
        default=Match.ALL,
    )


class FilterItem(BaseModel):
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


class Document(BaseModel):
    sample_transcript_variant = models.ForeignKey(
        SampleTranscriptVariant,
        on_delete=models.CASCADE,
        related_name='evidence_files'
    )
    description = models.CharField(max_length=1000, blank=True,)

    document = models.FileField(upload_to='documents/%Y/%m/%d/',)

    archived = models.BooleanField(default=False)

    @property
    def extension(self):
        name, extension = os.path.splitext(self.document.name)
        return extension

    @property
    def filename(self):
        return os.path.basename(self.document.name)

    def get_user_created(self):
        try:
            crud = CRUDEvent.objects.filter(object_repr=self).first().user
        except:
            crud = None
        return crud

    class Meta:
        ordering = ['-date_created']
        unique_together = ('sample_transcript_variant', 'document')


class Comment(BaseModel):
    sample_transcript_variant = models.ForeignKey(
        SampleTranscriptVariant,
        on_delete=models.CASCADE,
        related_name='comments'
    )

    comment = models.CharField(max_length=2000, blank=True)

    # Choice field for run QC status
    class Classification(models.IntegerChoices):
        UNCLASSIFIED = 0
        BENIGN = 1
        LIKELY_BENIGN = 2
        VUS = 3
        LIKELY_PATHOGENIC = 4
        PATHOGENIC = 5

    classification = models.IntegerField(
        choices=Classification.choices,
        default=0,
    )

    @property
    def classification_colour(self):
        colours = {0: 'blue',
                   1: 'green',
                   2: 'olive',
                   3: 'yellow',
                   4: 'orange',
                   5: 'red'}
        return colours[self.classification]

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

    class Meta:
        ordering = ['classification']


class Report(BaseModel):
    run = models.ForeignKey(
        Run,
        on_delete=models.CASCADE,
        related_name='reports'
    )
    samplesheetsample = models.ForeignKey(
        SamplesheetSample,
        on_delete=models.CASCADE,
        related_name='reports'
    )

    name = models.CharField(max_length=255)
    summary = models.CharField(max_length=2000, blank=True)
    recommendations = models.CharField(max_length=2000, blank=True)
    data = models.JSONField(default=dict, blank=True)

    def get_user_created(self):
        try:
            crud = CRUDEvent.objects.filter(object_repr=self).first().user
        except:
            crud = None
        return crud
