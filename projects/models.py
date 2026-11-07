from django.conf import settings
from django.db import models


class Project(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Открыт"
        CLOSED = "closed", "Закрыт"

    name = models.CharField("Название", max_length=200)
    description = models.TextField("Описание", blank=True)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects",
        verbose_name="Автор",
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="participated_projects",
        verbose_name="Участники",
        blank=True,
    )

    created_at = models.DateTimeField(
        "Дата создания",
        auto_now_add=True,
        db_index=True,
    )
    github_url = models.URLField("Ссылка на GitHub", blank=True)
    status = models.CharField(
        "Статус",
        max_length=6,
        choices=Status.choices,
        default=Status.OPEN,
    )

    class Meta:
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"
        ordering = ["-created_at", "-pk"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(status__in=["open", "closed"]),
                name="projects_status_valid",
            ),
        ]

    def __str__(self):
        return self.name