"""
accounts/admin.py
-----------------
Django admin integration for user service permissions.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserServiceProfile


class UserServiceProfileInline(admin.StackedInline):
    model = UserServiceProfile
    can_delete = False
    verbose_name_plural = "Purchased / Active Services"
    fk_name = "user"


class UserAdmin(BaseUserAdmin):
    inlines = (UserServiceProfileInline,)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(UserServiceProfile)
class UserServiceProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "has_vehicles_people", "has_object_count", "updated_at")
    list_filter = ("has_vehicles_people", "has_object_count")
    search_fields = ("user__username", "user__email")
