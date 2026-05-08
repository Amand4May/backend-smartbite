import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Usuário customizado do SmartBite."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(max_length=20, blank=True, verbose_name="Telefone")
    avatar_url = models.URLField(blank=True, verbose_name="Avatar URL")
    notification_email = models.BooleanField(default=True, verbose_name="Notificação por e-mail")
    notification_push = models.BooleanField(default=True, verbose_name="Notificação push")
    notification_low_food = models.BooleanField(default=True, verbose_name="Alerta de ração baixa")
    notification_pet_not_eating = models.BooleanField(default=True, verbose_name="Alerta pet não comeu")
    notification_device_offline = models.BooleanField(default=True, verbose_name="Alerta dispositivo offline")
    low_food_threshold = models.PositiveIntegerField(default=20, verbose_name="Limite baixo ração (%)")

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self) -> str:
        return self.get_full_name() or self.username
