import os
from django.db import models
from db.models import SampleTranscriptVariant
from db.utils.model_utils import BaseModel


# Create your models here.


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
