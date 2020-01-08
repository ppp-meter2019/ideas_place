from django.contrib import admin

from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .forms import CustomUser
# Register your models here.


class CustomUserAdmin(UserAdmin):

    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    readonly_fields = ('date_joined',)
    list_display = ('username', 'email', 'is_staff', 'is_active','date_joined',)
    list_filter = ('username', 'email', 'is_staff', 'is_active', 'date_joined')

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password', 'date_joined')}),
        ('Permissions', {'fields': ('is_staff', 'is_active')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_staff', 'is_active')}
         ),
    )

    search_fields = ('username', 'email', 'date_joined')
    ordering = ('username', 'email', 'date_joined')

admin.site.register(CustomUser,CustomUserAdmin)
