from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods, require_POST
from team_finder.pagination import paginate_queryset
from django.contrib.auth import get_user_model

from .forms import ProjectForm
from .models import Project


def json_error(message, status):
    return JsonResponse(
        {"status": "error", "message": message},
        status=status,
    )


@require_http_methods(["GET"])
@ensure_csrf_cookie
def project_detail_view(request, pk):
    projects = Project.objects.select_related(
        "owner",
    ).prefetch_related(
        "participants",
    )
    project = get_object_or_404(projects, pk=pk)

    return render(
        request,
        "projects/project-details.html",
        {"project": project},
    )


@login_required
@require_http_methods(["GET", "POST"])
def project_create_view(request):
    form = ProjectForm(
        request.POST if request.method == "POST" else None,
    )

    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            project.participants.add(request.user)

        messages.success(request, "Проект создан.")
        return redirect("projects:detail", pk=project.pk)

    return render(
        request,
        "projects/create-project.html",
        {"form": form, "is_edit": False},
    )


@login_required
@require_http_methods(["GET", "POST"])
@transaction.atomic
def project_edit_view(request, pk):
    projects = Project.objects.all()

    if request.method == "POST":
        projects = projects.select_for_update()

    project = get_object_or_404(projects, pk=pk)

    if project.owner_id != request.user.pk:
        raise PermissionDenied(
            "Редактировать проект может только его автор."
        )

    form = ProjectForm(
        request.POST if request.method == "POST" else None,
        instance=project,
    )

    if request.method == "POST" and form.is_valid():
        project = form.save()
        project.participants.add(request.user)

        messages.success(request, "Проект обновлён.")
        return redirect("projects:detail", pk=project.pk)

    return render(
        request,
        "projects/create-project.html",
        {"form": form, "is_edit": True},
    )


@require_POST
def project_complete_view(request, pk):
    if not request.user.is_authenticated:
        return json_error("Необходимо войти в аккаунт.", 401)

    with transaction.atomic():
        project = (
            Project.objects.select_for_update()
            .filter(pk=pk)
            .first()
        )

        if project is None:
            return json_error("Проект не найден.", 404)

        if project.owner_id != request.user.pk:
            return json_error(
                "Завершить проект может только его автор.",
                403,
            )

        if project.status != Project.Status.OPEN:
            return json_error("Проект уже закрыт.", 409)

        project.status = Project.Status.CLOSED
        project.save(update_fields=["status"])

    return JsonResponse({
        "status": "ok",
        "project_status": Project.Status.CLOSED,
    })


@require_POST
def project_toggle_participate_view(request, pk):
    if not request.user.is_authenticated:
        return json_error("Необходимо войти в аккаунт.", 401)

    with transaction.atomic():
        project = (
            Project.objects.select_for_update()
            .filter(pk=pk)
            .first()
        )

        if project is None:
            return json_error("Проект не найден.", 404)

        if project.owner_id == request.user.pk:
            return json_error(
                "Автор не может отказаться от участия в своём проекте.",
                403,
            )

        is_participant = project.participants.filter(
            pk=request.user.pk,
        ).exists()

        if is_participant:
            project.participants.remove(request.user)
            participant = False
        else:
            if project.status != Project.Status.OPEN:
                return json_error(
                    "Нельзя вступить в закрытый проект.",
                    409,
                )

            project.participants.add(request.user)
            participant = True

    return JsonResponse({
        "status": "ok",
        "participant": participant,
    })
@require_http_methods(["GET"])
@ensure_csrf_cookie
def project_list_view(request):
    projects = (
        Project.objects
        .select_related("owner")
        .prefetch_related("participants")
        .order_by("-created_at", "-pk")
    )

    context = paginate_queryset(request, projects)
    context["projects"] = context["page_obj"].object_list

    return render(
        request,
        "projects/project_list.html",
        context,
    )

@login_required
@require_http_methods(["GET"])
@ensure_csrf_cookie
def favorite_projects_view(request):
    projects = (
        request.user.favorites
        .select_related("owner")
        .prefetch_related("participants")
        .order_by("-created_at", "-pk")
    )

    return render(
        request,
        "projects/favorite_projects.html",
        {"projects": projects},
    )


@require_POST
def toggle_favorite_view(request, pk):
    if not request.user.is_authenticated:
        return json_error("Необходимо войти в аккаунт.", 401)

    User = get_user_model()

    with transaction.atomic():
        user = (
            User.objects.select_for_update()
            .filter(pk=request.user.pk)
            .first()
        )

        if user is None:
            return json_error("Пользователь не найден.", 404)

        project = Project.objects.filter(pk=pk).first()

        if project is None:
            return json_error("Проект не найден.", 404)

        if user.favorites.filter(pk=project.pk).exists():
            user.favorites.remove(project)
            favorited = False
        else:
            user.favorites.add(project)
            favorited = True

    return JsonResponse({
        "status": "ok",
        "favorited": favorited,
    })