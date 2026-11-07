from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .forms import UserAdminChangeForm, UserAdminCreationForm
from .models import Skill, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm

    list_display = (
        "email",
        "name",
        "surname",
        "is_active",
        "is_staff",
        "date_joined",
    )
    list_filter = ("is_active", "is_staff", "is_superuser")
    search_fields = ("email", "name", "surname", "phone")
    ordering = ("-date_joined", "-pk")
    readonly_fields = ("last_login", "date_joined")

    fieldsets = (
        (None, {
            "fields": ("email", "password"),
        }),
        ("Профиль", {
            "fields": (
                "name",
                "surname",
                "avatar",
                "phone",
                "github_url",
                "about",
                "skills",
            ),
        }),
        ("Права доступа", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            ),
        }),
        ("Даты", {
            "fields": ("last_login", "date_joined"),
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email",
                "name",
                "surname",
                "password1",
                "password2",
            ),
        }),
    )

    filter_horizontal = ("groups", "user_permissions", "skills")

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)