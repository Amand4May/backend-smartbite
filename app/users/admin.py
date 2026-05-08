from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "is_staff")
    fieldsets = UserAdmin.fieldsets + (
        ("SmartBite", {"fields": ("phone", "avatar_url", "notification_email", "notification_push",
                                   "notification_low_food", "notification_pet_not_eating",
                                   "notification_device_offline", "low_food_threshold")}),
    )
