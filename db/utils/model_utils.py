from django.db import models
from django.conf import settings
from pathlib import Path
import os


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
    file = models.FileField(null=True, default=None, max_length=500)
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
        try:
            file_path = Path(self.path)
            # target = settings.MEDIA_ROOT / 'symlinks' / file_path.name
            target = settings.MEDIA_ROOT / 'symlinks' / \
                file_path.relative_to(file_path.parent.parent.parent)

            if not os.path.islink(target):
                target.parent.mkdir(parents=True, exist_ok=True)
                target.symlink_to(file_path)
            self.file.name = str(target.relative_to(
                target.parent.parent.parent.parent))

            if '.xlsx' not in file_path.suffixes:
                index_file_path = [x for x in file_path.parent.glob(
                    file_path.name + '.*i') if x.is_file()][0]
                index_target = settings.MEDIA_ROOT / 'symlinks' / \
                    index_file_path.relative_to(
                        index_file_path.parent.parent.parent)
                # index_target = settings.MEDIA_ROOT / 'symlinks' / index_file_path.name
                if not os.path.islink(index_target):
                    index_target.symlink_to(index_file_path)

            self.save()
        except:
            print('Unable to create symlinks')
            raise

    def __str__(self):
        return self.path

    class Meta(BaseModel.Meta):
        abstract = True
        indexes = [
            models.Index(fields=['path'])
        ]
        indexes = [
            models.Index(fields=['path'])
        ]


def mode(array):
    '''
    returns a set containing valid modes
    returns None if no valid mode exists
      - when all values occur the same number of times
      - when only one value occurs in the list 
      - when no value occurs in the list 
    '''
    most = max(map(array.count, array)) if array else None
    mset = set(filter(lambda x: array.count(x) == most, array))
    return list(mset)[0] if set(array) - mset else None
