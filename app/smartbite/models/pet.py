from core.models.base import BaseModelMixin
from django.db import models
from django.conf import settings


class Pet(BaseModelMixin):
    SPECIES_CHOICES = [
        ("dog", "Cachorro"),
        ("cat", "Gato"),
    ]
    ACTIVITY_CHOICES = [
        ("low", "Baixo"),
        ("moderate", "Moderado"),
        ("high", "Alto"),
    ]
    GOAL_CHOICES = [
        ("weight_loss", "Perda de peso"),
        ("maintenance", "Manutenção"),
        ("weight_gain", "Ganho de peso"),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pets",
        verbose_name="Dono",
    )
    name = models.CharField(max_length=100, verbose_name="Nome")
    species = models.CharField(max_length=10, choices=SPECIES_CHOICES, verbose_name="Espécie")
    breed = models.CharField(max_length=100, blank=True, verbose_name="Raça")
    weight = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Peso (kg)")
    age = models.PositiveSmallIntegerField(verbose_name="Idade (meses)")
    activity_level = models.CharField(max_length=10, choices=ACTIVITY_CHOICES, default="moderate", verbose_name="Nível de atividade")
    feeding_goal = models.CharField(max_length=15, choices=GOAL_CHOICES, default="maintenance", verbose_name="Objetivo alimentar")
    avatar_emoji = models.CharField(max_length=10, default="🐾", verbose_name="Emoji")
    daily_recommended_grams = models.PositiveIntegerField(default=0, verbose_name="Recomendação diária (g)")

    class Meta:
        verbose_name = "Pet"
        verbose_name_plural = "Pets"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.owner})"
