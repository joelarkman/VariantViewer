from django.db import models


class BaseModel(models.Model):
    """Abstract base model to provide auto-date fields on children
    """
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        app_label = 'db'


class BaseSingletonModel(BaseModel):
    """Abstract base model for singletons; only one instance may exist in db
    """
    @classmethod
    def load(cls):
        # call this method to access the instance, else load with defaults
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs):
        # if attempting to save new instance, set pk to 1 to overwrite instead
        self.pk = 1
        super(BaseSingletonModel, self).save()

    def delete(self, *args, **kwargs):
        # disallow deletion of the model
        pass

    class Meta(BaseModel.Meta):
        abstract = True


class PipelineOutputFileModel(BaseModel):
    path = models.TextField()
    file = models.FileField(null=True, default=None)
    run = models.ForeignKey(
        "Run",
        on_delete=models.PROTECT
    )

    def create_symlink(self):
        """Method to create a symlink of the path and store as self.file

        This enables access of files from within the django media functionality
        without having to copy files across to the desired location, nor allow
        access to the whole pipeline output directory.
        """
        raise NotImplementedError()

    class Meta(BaseModel.Meta):
        abstract = True
