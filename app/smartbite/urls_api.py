from django.urls import path
from smartbite.views import (
    RegisterView, LoginView, LogoutView, MeView, ChangePasswordView,
    PetListCreateView, PetDetailView,
    FeederListView, FeederSetupView, FeederDetailView, DispenseView,
    FeedingHistoryView, DailyConsumptionView,
    ScheduleListCreateView, ScheduleDetailView,
    AlertListView, AlertMarkReadView, AlertDismissView, AlertMarkAllReadView,
    NutritionCalculatorView, CurrentDateTimeView,
    ESP32DeviceRegisterView, ESP32HeartbeatView, ESP32FeedCommandView,
)

app_name = "smartbite-api"

urlpatterns = [
    # Auth
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("auth/change-password/", ChangePasswordView.as_view(), name="change-password"),

    # Pets
    path("pets/", PetListCreateView.as_view(), name="pet-list"),
    path("pets/<uuid:pk>/", PetDetailView.as_view(), name="pet-detail"),
    path("pets/<uuid:pet_pk>/history/", FeedingHistoryView.as_view(), name="feeding-history"),
    path("pets/<uuid:pet_pk>/consumption/", DailyConsumptionView.as_view(), name="daily-consumption"),
    path("pets/<uuid:pet_pk>/schedules/", ScheduleListCreateView.as_view(), name="schedule-list"),
    path("schedules/<uuid:pk>/", ScheduleDetailView.as_view(), name="schedule-detail"),
    path("nutrition/calculate/", NutritionCalculatorView.as_view(), name="nutrition-calculate"),

    # Feeders
    path("feeders/", FeederListView.as_view(), name="feeder-list"),
    path("feeders/setup/", FeederSetupView.as_view(), name="feeder-setup"),
    path("feeders/<uuid:pk>/", FeederDetailView.as_view(), name="feeder-detail"),
    path("feeders/<uuid:pk>/dispense/", DispenseView.as_view(), name="feeder-dispense"),
    path("feeders/<uuid:feeder_id>/feed-command/", ESP32FeedCommandView.as_view(), name="esp32-feed-command"),

    # Alerts
    path("alerts/", AlertListView.as_view(), name="alert-list"),
    path("alerts/mark-all-read/", AlertMarkAllReadView.as_view(), name="alert-mark-all-read"),
    path("alerts/<uuid:pk>/read/", AlertMarkReadView.as_view(), name="alert-read"),
    path("alerts/<uuid:pk>/dismiss/", AlertDismissView.as_view(), name="alert-dismiss"),

    # Utilities
    path("utils/datetime/", CurrentDateTimeView.as_view(), name="current-datetime"),

    # ESP32 Integration
    path("esp32/register/", ESP32DeviceRegisterView.as_view(), name="esp32-register"),
    path("esp32/heartbeat/", ESP32HeartbeatView.as_view(), name="esp32-heartbeat"),
]
