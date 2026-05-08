from core.models.base import BaseModelMixin
from django.db import models


class FeedingRecord(BaseModelMixin):
    TYPE_CHOICES = [
        ("manual", "Manual"),
        ("scheduled", "Agendado"),
    ]

    pet = models.ForeignKey(
        "smartbite.Pet",
        on_delete=models.CASCADE,
        related_name="feeding_records",
        verbose_name="Pet",
    )
    feeder = models.ForeignKey(
        "smartbite.Feeder",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="feeding_records",
        verbose_name="Comedouro",
    )
    timestamp = models.DateTimeField(verbose_name="Data/hora")
    amount_grams = models.PositiveIntegerField(verbose_name="Quantidade (g)")
    feeding_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default="manual", verbose_name="Tipo")

    class Meta:
        verbose_name = "Registro de Alimentação"
        verbose_name_plural = "Registros de Alimentação"
        ordering = ["-timestamp"]

    def __str__(self) -> str:
        return f"{self.pet} - {self.timestamp} ({self.amount_grams}g)"


class FeedingSchedule(BaseModelMixin):
    DAYS_OF_WEEK = [(i, d) for i, d in enumerate(["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"])]

    pet = models.ForeignKey(
        "smartbite.Pet",
        on_delete=models.CASCADE,
        related_name="schedules",
        verbose_name="Pet",
    )
    time = models.TimeField(verbose_name="Horário")
    amount_grams = models.PositiveIntegerField(verbose_name="Quantidade (g)")
    enabled = models.BooleanField(default=True, verbose_name="Habilitado")
    days = models.JSONField(default=list, verbose_name="Dias da semana (0=Dom, 6=Sáb)")

    class Meta:
        verbose_name = "Agendamento de Alimentação"
        verbose_name_plural = "Agendamentos de Alimentação"
        ordering = ["time"]

    def __str__(self) -> str:
        return f"{self.pet} - {self.time} ({self.amount_grams}g)"
