from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from users.models import CustomUser
from django.dispatch import receiver


# Create your models here.


class Idea(models.Model):
    i_title = models.CharField(max_length=255, verbose_name=_('Ideas Title'),
                               blank=False, default="My New Ideas TITLE")
    i_text = models.TextField(null=False, blank=False, verbose_name=_('An incredible Idea'),
                              default="My New Idea about ...")
    author = models.ForeignKey(CustomUser, verbose_name=_('Idea Author'), null=True, default=None,
                               on_delete=models.SET_NULL, related_name='ideas')
    date_published = models.DateTimeField(verbose_name=_('date published'), default=timezone.now)

    def __str__(self):
        return self.i_title


class Likes(models.Model):
    parent_idea = models.ForeignKey(Idea, blank=False, null=False, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(CustomUser, null=True, default=None, on_delete=models.SET_NULL)
    is_like = models.BooleanField(blank=True, null=True, default=False)
    is_unlike = models.BooleanField(blank=True, null=True, default=False)
