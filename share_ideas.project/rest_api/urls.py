from . import views
from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

app_name = 'rest_api'

urlpatterns = [
    path('users/signup/', views.NewUserRegister.as_view(), name='users-add'),
    path('users/activate/', views.NewUserActivate.as_view(), name='user-activate'),
    path('users/<int:pk>/', views.UserDetail.as_view(), name='user-detail'),
    path('ideas/', views.IdeaTools.as_view(), name='idea-tool'),
    path('ideas/<int:pk>/', views.IdeaTools.as_view(), name='idea-detail'),
    path('ideas/<int:pk>/add-likes/', views.AddLikes.as_view(), name='likes-add'),
]

urlpatterns = format_suffix_patterns(urlpatterns)
