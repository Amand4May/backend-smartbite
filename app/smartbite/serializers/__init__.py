from rest_framework import serializers
from django.contrib.auth import get_user_model
from smartbite.models import Pet, Feeder, FeedingRecord, FeedingSchedule, Alert
from smartbite.application.nutrition import calculate_pet_portion

User = get_user_model()


# ── Auth ──────────────────────────────────────────────────────────────────────

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "password", "confirm_password")

    def validate(self, data):
        if data["password"] != data.pop("confirm_password"):
            raise serializers.ValidationError({"confirm_password": "As senhas não coincidem."})
        return data

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id", "username", "email", "first_name", "last_name", "phone", "avatar_url",
            "notification_email", "notification_push", "notification_low_food",
            "notification_pet_not_eating", "notification_device_offline", "low_food_threshold",
        )
        read_only_fields = ("id",)


# ── Pet ───────────────────────────────────────────────────────────────────────

class PetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pet
        fields = (
            "id", "name", "species", "breed", "weight", "age",
            "activity_level", "feeding_goal", "avatar_emoji",
            "is_neutered", "body_condition", "breed_factor",
            "daily_recommended_grams", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def create(self, validated_data):
        if not validated_data.get("avatar_emoji"):
            validated_data["avatar_emoji"] = "🐕" if validated_data.get("species") == "dog" else "🐱"
        pet = super().create(validated_data)
        pet.daily_recommended_grams = calculate_pet_portion(pet)
        pet.save(update_fields=["daily_recommended_grams"])
        return pet

    def update(self, instance, validated_data):
        pet = super().update(instance, validated_data)
        pet.daily_recommended_grams = calculate_pet_portion(pet)
        pet.save(update_fields=["daily_recommended_grams"])
        return pet


# ── Feeder ────────────────────────────────────────────────────────────────────

class FeederSerializer(serializers.ModelSerializer):
    online = serializers.BooleanField(read_only=True)
    pet_name = serializers.CharField(source="pet.name", read_only=True)

    class Meta:
        model = Feeder
        fields = (
            "id", "serial_number", "name", "pet", "pet_name", "online",
            "device_state", "food_level_percent", "last_feeding_at",
            "last_feeding_amount", "wifi_signal", "last_sync_at",
            "motor_status", "estimated_days_remaining", "firmware_version",
            "created_at", "updated_at",
        )
        read_only_fields = ("id", "last_sync_at", "created_at", "updated_at")


class FeederSetupSerializer(serializers.Serializer):
    serial_number = serializers.CharField(max_length=50)
    name = serializers.CharField(max_length=100, default="Comedouro SmartBite")
    pet_id = serializers.UUIDField(required=False, allow_null=True)


class DispenseSerializer(serializers.Serializer):
    amount_grams = serializers.IntegerField(min_value=1, max_value=500)


# ── Feeding ───────────────────────────────────────────────────────────────────

class FeedingRecordSerializer(serializers.ModelSerializer):
    pet_name = serializers.CharField(source="pet.name", read_only=True)

    class Meta:
        model = FeedingRecord
        fields = (
            "id", "pet", "pet_name", "feeder", "timestamp",
            "amount_grams", "feeding_type", "created_at",
        )
        read_only_fields = ("id", "created_at")


class FeedingScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedingSchedule
        fields = (
            "id", "pet", "time", "amount_grams", "enabled", "days",
            "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class DailyConsumptionSerializer(serializers.Serializer):
    date = serializers.DateField()
    recommended = serializers.IntegerField()
    served = serializers.IntegerField()


# ── Alert ─────────────────────────────────────────────────────────────────────

class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = (
            "id", "alert_type", "severity", "message",
            "timestamp", "read", "dismissed",
        )
        read_only_fields = ("id", "timestamp")
