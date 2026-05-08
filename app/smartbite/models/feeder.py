from core.models.base import BaseModelMixin
from django.db import models
from django.conf import settings


class Feeder(BaseModelMixin):
    DEVICE_STATE_CHOICES = [
        ("online", "Online"),
        ("processing", "Processando"),
        ("offline", "Offline"),
    ]
    MOTOR_STATUS_CHOICES = [
        ("ok", "OK"),
        ("stuck", "Travado"),
        ("unknown", "Desconhecido"),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="feeders",
        verbose_name="Dono",
    )
    pet = models.OneToOneField(
        "smartbite.Pet",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="feeder",
        verbose_name="Pet",
    )
    serial_number = models.CharField(max_length=50, unique=True, verbose_name="Número de série")
    name = models.CharField(max_length=100, default="Comedouro SmartBite", verbose_name="Nome")
    device_state = models.CharField(max_length=15, choices=DEVICE_STATE_CHOICES, default="offline", verbose_name="Estado do dispositivo")
    food_level_percent = models.PositiveSmallIntegerField(default=100, verbose_name="Nível de ração (%)")
    last_feeding_at = models.DateTimeField(null=True, blank=True, verbose_name="Última alimentação")
    last_feeding_amount = models.PositiveIntegerField(default=0, verbose_name="Última quantidade (g)")
    wifi_signal = models.IntegerField(default=-70, verbose_name="Sinal WiFi (dBm)")
    last_sync_at = models.DateTimeField(auto_now=True, verbose_name="Última sincronização")
    motor_status = models.CharField(max_length=10, choices=MOTOR_STATUS_CHOICES, default="unknown", verbose_name="Status do motor")
    estimated_days_remaining = models.PositiveSmallIntegerField(default=0, verbose_name="Dias restantes estimados")
    firmware_version = models.CharField(max_length=20, default="1.0.0", verbose_name="Versão do firmware")

    class Meta:
        verbose_name = "Comedouro"
        verbose_name_plural = "Comedouros"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.serial_number})"

    @property
    def online(self) -> bool:
        return self.device_state == "online"
