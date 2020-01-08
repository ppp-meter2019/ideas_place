from django.db import models

# Create your models here.

from django.contrib.auth.models import AbstractUser
from django.utils.translation import ugettext_lazy as _


class CustomUser(AbstractUser):

    email = models.EmailField(_('email address'), unique=True)

    def __str__(self):
        return self.username

