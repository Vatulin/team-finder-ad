from django.contrib import admin
from django.db.models import Count

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "owner",
        "status",
        "created_at",
        "participants_count",
    )
    list_filter = ("status", "created_at")
    search_fields = (
        "name",
        "description",
        "owner__email",
        "owner__name",
        "owner__surname",
    )
    autocomplete_fields = ("owner", "participants")
    readonly_fields = ("created_at",)
    list_select_related = ("owner",)
    ordering = ("-created_at", "-pk")

    fields = (
        "name",
        "description",
        "owner",
        "participants",
        "github_url",
        "status",
        "created_at",
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            member_count=Count("participants", distinct=True),
        )

    @admin.display(
        description="Участников",
        ordering="member_count",
    )
    def participants_count(self, obj):
        return obj.member_count

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.participants.add(form.instance.owner)