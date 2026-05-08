from django.contrib import admin
from smartbite.models import Pet, Feeder, FeedingRecord, FeedingSchedule, Alert


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "species", "breed", "weight", "age", "is_active")
    list_filter = ("species", "activity_level", "feeding_goal", "is_active")
    search_fields = ("name", "owner__username", "owner__email")


@admin.register(Feeder)
class FeederAdmin(admin.ModelAdmin):
    list_display = ("name", "serial_number", "owner", "pet", "device_state", "food_level_percent", "is_active")
    list_filter = ("device_state", "motor_status", "is_active")
    search_fields = ("serial_number", "name", "owner__username")


@admin.register(FeedingRecord)
class FeedingRecordAdmin(admin.ModelAdmin):
    list_display = ("pet", "feeder", "timestamp", "amount_grams", "feeding_type")
    list_filter = ("feeding_type",)
    search_fields = ("pet__name",)


@admin.register(FeedingSchedule)
class FeedingScheduleAdmin(admin.ModelAdmin):
    list_display = ("pet", "time", "amount_grams", "enabled")
    list_filter = ("enabled",)
    search_fields = ("pet__name",)


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("user", "alert_type", "severity", "timestamp", "read", "dismissed")
    list_filter = ("alert_type", "severity", "read", "dismissed")
    search_fields = ("user__username", "message")
