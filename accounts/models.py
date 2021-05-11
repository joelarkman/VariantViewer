from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.fields import BooleanField
from django.utils.translation import ugettext_lazy as _

from easyaudit.models import LoginEvent


class UserManager(BaseUserManager):
    """Model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

    def get_by_natural_key(self, username):
        case_insensitive_username_field = '{}__iexact'.format(
            self.model.USERNAME_FIELD)
        return self.get(**{case_insensitive_username_field: username})


# def get_validate_hash():
#     datetime_str = str(datetime.now())
#     m = hashlib.md5()
#     m.update(datetime_str.encode())
#     return m.hexdigest()


class User(AbstractUser):
    """Custom user model to allow extension with custom fields.
    This must be established in the first migration (0001_initial.py), if not
    then auth user model cannot be changed.
    """

    username = None
    email = models.EmailField(_('email address'), unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    filters = models.ManyToManyField(
        'web.Filter',
        through="UserFilter"
    )

    # validate_hash = models.CharField(
    #     max_length=255,
    #     default=get_validate_hash
    # )

    objects = UserManager()

    @property
    def last_logged_in(self):
        try:
            return LoginEvent.objects.filter(user=self, login_type=0)[1].datetime
        except:
            return None

    @property
    def avatar_url(self):
        if self.is_superuser:
            return "https://avatars.dicebear.com/api/initials/" \
                   "su.svg?b=%23000000&bold=1"
        else:
            return f"https://avatars.dicebear.com/api/initials/" \
                   f"{self.first_name[0]}{self.last_name[0]}:.svg" \
                   f"?r=5&bold=1"


class UserFilter(models.Model):
    """
    Representation of filter associated with a particular VCF file.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    filter = models.ForeignKey(
        'web.Filter',
        on_delete=models.CASCADE
    )
    selected = models.BooleanField(default=False)
