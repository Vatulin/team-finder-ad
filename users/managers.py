from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    use_in_migrations = True

    @classmethod
    def normalize_email(cls, email):
        return super().normalize_email(email).strip().lower()

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Необходимо указать email.")

        for field in ("name", "surname"):
            if not str(extra_fields.get(field) or "").strip():
                raise ValueError(f"Необходимо заполнить поле {field}.")

        user = self.model(
            email=self.normalize_email(email),
            **extra_fields,
        )
        user.set_password(password)
        user.full_clean()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        for field in ("is_staff", "is_superuser", "is_active"):
            if extra_fields.get(field) is not True:
                raise ValueError(
                    f"Для суперпользователя {field} должно быть True."
                )

        return self.create_user(email, password, **extra_fields)