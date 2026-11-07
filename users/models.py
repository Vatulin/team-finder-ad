from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.functions import Lower

from .avatars import generate_avatar
from .managers import UserManager


phone_validator = RegexValidator(
    regex=r"\A(?:8[0-9]{10}|\+7[0-9]{10})\Z",
    message="Введите телефон в формате 8XXXXXXXXXX или +7XXXXXXXXXX.",
)


def normalize_phone(phone):
    if not phone:
        return None

    phone = phone.strip()
    if len(phone) == 11 and phone.startswith("8"):
        phone = "+7" + phone[1:]

    return phone or None

class Skill(models.Model):
    name = models.CharField("Название", max_length=124)

    class Meta:
        verbose_name = "Навык"
        verbose_name_plural = "Навыки"
        ordering = [Lower("name"), "pk"]
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="users_skill_name_case_insensitive_unique",
            ),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        self.name = self.name.strip()

        if not self.name:
            raise ValidationError(
                {"name": "Название навыка не может быть пустым."}
            )

class User(AbstractUser):
    username = None
    first_name = None
    last_name = None

    email = models.EmailField("Email", unique=True)
    name = models.CharField("Имя", max_length=124)
    surname = models.CharField("Фамилия", max_length=124)

    avatar = models.ImageField(
        "Аватар",
        upload_to="avatars/",
        blank=True,
    )
    phone = models.CharField(
        "Телефон",
        max_length=12,
        blank=True,
        null=True,
        unique=True,
        validators=[phone_validator],
    )
    github_url = models.URLField("Ссылка на GitHub", blank=True)
    about = models.TextField("О себе", max_length=256, blank=True)
    skills = models.ManyToManyField(
        Skill,
        verbose_name="Навыки",
        related_name="users",
        blank=True,
    )
    favorites = models.ManyToManyField(
    "projects.Project",
    verbose_name="Избранные проекты",
    related_name="interested_users",
    blank=True,
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "surname"]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["-date_joined", "-pk"]
        constraints = [
            models.UniqueConstraint(
                Lower("email"),
                name="users_email_case_insensitive_unique",
            ),
        ]

    def __str__(self):
        return f"{self.name} {self.surname} ({self.email})"

    def get_full_name(self):
        return f"{self.name} {self.surname}".strip()

    def get_short_name(self):
        return self.name

    def clean(self):
        super().clean()
        self.email = type(self).objects.normalize_email(self.email)
        self.phone = normalize_phone(self.phone)
        self.name = self.name.strip()
        self.surname = self.surname.strip()

        errors = {}
        if not self.name:
            errors["name"] = "Укажите имя."
        if not self.surname:
            errors["surname"] = "Укажите фамилию."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.email = type(self).objects.normalize_email(self.email)
        self.phone = normalize_phone(self.phone)

        if not self.avatar:
            if not self.name.strip():
                raise ValidationError({"name": "Укажите имя."})

            avatar_file = generate_avatar(self.name)
            self.avatar.save(
                avatar_file.name,
                avatar_file,
                save=False,
            )
            if kwargs.get("update_fields") is not None:
                kwargs["update_fields"] = {
                    *kwargs["update_fields"],
                    "avatar",
                }

        super().save(*args, **kwargs)