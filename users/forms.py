from urllib.parse import urlsplit

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import (
    BaseUserCreationForm,
    UserChangeForm,
)
from django.contrib.auth.password_validation import validate_password

from .models import User, normalize_phone, phone_validator


class UserAdminCreationForm(BaseUserCreationForm):
    class Meta:
        model = User
        fields = ("email", "name", "surname")


class UserAdminChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = "__all__"


class UniqueEmailMixin:
    def clean_email(self):
        email = User.objects.normalize_email(self.cleaned_data["email"])
        users = User.objects.filter(email__iexact=email)

        if self.instance.pk:
            users = users.exclude(pk=self.instance.pk)

        if users.exists():
            raise forms.ValidationError(
                "Пользователь с таким email уже существует."
            )

        return email


class RegistrationForm(UniqueEmailMixin, forms.ModelForm):
    password = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"autocomplete": "new-password"},
        ),
    )

    class Meta:
        model = User
        fields = ("name", "surname", "email", "password")
        widgets = {
            "name": forms.TextInput(
                attrs={"autocomplete": "given-name"},
            ),
            "surname": forms.TextInput(
                attrs={"autocomplete": "family-name"},
            ),
            "email": forms.EmailInput(
                attrs={"autocomplete": "email"},
            ),
        }

    def _post_clean(self):
        super()._post_clean()

        password = self.cleaned_data.get("password")
        if password:
            try:
                validate_password(password, self.instance)
            except forms.ValidationError as error:
                self.add_error("password", error)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()
            self.save_m2m()

        return user


class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={"autocomplete": "username"},
        ),
    )
    password = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"autocomplete": "current-password"},
        ),
    )

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.user_cache = None

    def clean_email(self):
        return User.objects.normalize_email(self.cleaned_data["email"])

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if email and password:
            self.user_cache = authenticate(
                self.request,
                username=email,
                password=password,
            )
            if self.user_cache is None:
                raise forms.ValidationError(
                    "Неверный имейл или пароль."
                )

        return cleaned_data

    def get_user(self):
        return self.user_cache


class ProfileEditForm(UniqueEmailMixin, forms.ModelForm):
    phone = forms.CharField(
        label="Телефон",
        required=False,
        max_length=12,
        validators=[phone_validator],
        widget=forms.TextInput(
            attrs={
                "type": "tel",
                "placeholder": "+79991234567",
                "autocomplete": "tel",
            },
        ),
    )

    class Meta:
        model = User
        fields = (
            "name",
            "surname",
            "email",
            "avatar",
            "about",
            "phone",
            "github_url",
        )
        widgets = {
            "avatar": forms.FileInput(
                attrs={"accept": "image/*"},
            ),
            "about": forms.Textarea(
                attrs={"rows": 4, "maxlength": 256},
            ),
            "email": forms.EmailInput(
                attrs={"autocomplete": "email"},
            ),
        }

    def clean_phone(self):
        phone = normalize_phone(self.cleaned_data.get("phone"))

        if phone is None:
            return None

        users = User.objects.filter(phone=phone).exclude(
            pk=self.instance.pk,
        )

        if users.exists():
            raise forms.ValidationError(
                "Этот телефон уже указан другим пользователем."
            )

        return phone

    def clean_github_url(self):
        url = self.cleaned_data.get("github_url")
        if not url:
            return ""

        parsed = urlsplit(url)
        if (
            parsed.scheme not in {"http", "https"}
            or parsed.hostname not in {"github.com", "www.github.com"}
            or parsed.username is not None
            or parsed.password is not None
        ):
            raise forms.ValidationError(
                "Укажите ссылку на github.com."
            )

        return url