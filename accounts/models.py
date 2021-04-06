from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model to allow extension with custom fields.
    This must be established in the first migration (0001_initial.py), if not
    then auth user model cannot be changed.
    """
    pass
