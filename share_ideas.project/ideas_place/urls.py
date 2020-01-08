from . import views
from django.urls import path, re_path
app_name = 'ideas_place'

urlpatterns = [


    re_path(r'^activation/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
            views.UserActivation.as_view(), name='user-activation'),
]


