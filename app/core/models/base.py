import uuid
from django.db import models
from django.utils import timezone


class BaseModelMixin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    deactivate_reason = models.TextField(blank=True, verbose_name="Motivo da desativação")
    deactivated_at = models.DateTimeField("Desativado em", blank=True, null=True)
    deactivated_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        related_name="%(class)s_deactivated_by",
        blank=True,
        null=True,
        verbose_name="Desativado por",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        abstract = True

    def deactivate(self, reason: str, user) -> None:
        self.is_active = False
        self.deactivate_reason = reason
        self.deactivated_by = user
        self.deactivated_at = timezone.now()
        self.save()

    def activate(self) -> None:
        self.is_active = True
        self.deactivate_reason = ""
        self.deactivated_by = None
        self.deactivated_at = None
        self.save()
