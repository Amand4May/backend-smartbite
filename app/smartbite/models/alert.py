from core.models.base import BaseModelMixin
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Alert(BaseModelMixin):
    class AlertType(models.TextChoices):
        PET_NOT_EATING = "pet_not_eating", _("Pet não comeu")
        FOOD_LOW = "food_low", _("Ração baixa")
        DEVICE_OFFLINE = "device_offline", _("Dispositivo offline")
        MOTOR_STUCK = "motor_stuck", _("Motor travado")
        FEEDING_BELOW = "feeding_below", _("Alimentação abaixo do recomendado")

    class Severity(models.TextChoices):
        CRITICAL = "critical", _("Crítico")
        WARNING = "warning", _("Aviso")
        INFO = "info", _("Informativo")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="alerts",
        verbose_name=_("Usuário"),
    )
    alert_type = models.CharField(
        max_length=20, choices=AlertType.choices, verbose_name=_("Tipo")
    )
    severity = models.CharField(
        max_length=10, choices=Severity.choices, default=Severity.INFO, verbose_name=_("Severidade")
    )
    message = models.TextField(verbose_name=_("Mensagem"))
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_("Data/hora"))
    read = models.BooleanField(default=False, verbose_name=_("Lido"))
    dismissed = models.BooleanField(default=False, verbose_name=_("Descartado"))

    class Meta:
        verbose_name = _("Alerta")
        verbose_name_plural = _("Alertas")
        ordering = ["-timestamp"]
        indexes = [models.Index(fields=["user", "timestamp"])]

    def __str__(self) -> str:
        return f"[{self.get_severity_display()}] {self.get_alert_type_display()} - {self.user}"
