import os
from django.db import models


# Create your models here.


class Document(models.Model):
    description = models.CharField(max_length=1000, blank=True,)
    document = models.FileField(upload_to='documents/%Y/%m/%d/',)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def extension(self):
        name, extension = os.path.splitext(self.document.name)
        return extension

    def filename(self):
        return os.path.basename(self.document.name)
