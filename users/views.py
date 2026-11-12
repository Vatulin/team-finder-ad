from django.contrib import messages
from django.contrib.auth import (
    login,
    logout,
    update_session_auth_hash,
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods, require_POST
from team_finder.pagination import paginate_queryset
from django.db import transaction
from django.db.models.functions import Lower
from django.http import JsonResponse
from django.utils.html import escape
from django.views.decorators.csrf import ensure_csrf_cookie

import json

from .forms import (
    LoginForm,
    ProfileEditForm,
    RegistrationForm,
    SkillAddForm,
)
from .models import Skill, User


@sensitive_post_parameters("password")
@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.user.is_authenticated:
        return redirect("users:detail", pk=request.user.pk)

    form = RegistrationForm(
        request.POST if request.method == "POST" else None,
    )

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(
            request,
            "Аккаунт создан. Войдите по email и паролю.",
        )
        return redirect("users:login")

    return render(request, "users/register.html", {"form": form})


@sensitive_post_parameters("password")
@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect("users:detail", pk=request.user.pk)

    form = LoginForm(
        request=request,
        data=request.POST if request.method == "POST" else None,
    )
    next_url = (
        request.POST.get("next", "")
        if request.method == "POST"
        else request.GET.get("next", "")
    )

    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())

        if next_url and url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(next_url)

        return redirect("projects:list")

    return render(
        request,
        "users/login.html",
        {"form": form, "next": next_url},
    )


@require_http_methods(["GET"])
def logout_view(request):
    logout(request)
    messages.success(request, "Вы вышли из аккаунта.")
    return redirect("projects:list")


@require_http_methods(["GET"])
@ensure_csrf_cookie
def profile_view(request, pk):
    users = User.objects.prefetch_related(
        "skills",
        "owned_projects__participants",
    )
    profile_user = get_object_or_404(users, pk=pk)

    return render(
        request,
        "users/user-details.html",
        {"user": profile_user},
    )


@login_required
@require_http_methods(["GET", "POST"])
def edit_profile_view(request):
    form = ProfileEditForm(
        data=request.POST if request.method == "POST" else None,
        files=request.FILES if request.method == "POST" else None,
        instance=request.user,
    )

    if request.method == "POST" and form.is_valid():
        user = form.save()
        messages.success(request, "Профиль обновлён.")
        return redirect("users:detail", pk=user.pk)

    return render(
        request,
        "users/edit_profile.html",
        {"form": form},
    )


@sensitive_post_parameters(
    "old_password",
    "new_password1",
    "new_password2",
)
@login_required
@require_http_methods(["GET", "POST"])
def change_password_view(request):
    form = PasswordChangeForm(
        user=request.user,
        data=request.POST if request.method == "POST" else None,
    )

    if request.method == "POST" and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, "Пароль изменён.")
        return redirect("users:detail", pk=user.pk)

    return render(
        request,
        "users/change_password.html",
        {"form": form},
    )

@require_http_methods(["GET"])
def user_list_view(request):
    active_skill = request.GET.get("skill", "").strip()

    users = User.objects.order_by("-date_joined", "-pk")

    if active_skill:
        users = users.filter(
            skills__name=active_skill,
        ).distinct()

    all_skills = (
        Skill.objects
        .order_by(Lower("name"), "pk")
        .values_list("name", flat=True)
    )

    context = paginate_queryset(request, users)
    context.update({
        "participants": context["page_obj"].object_list,
        "all_skills": all_skills,
        "active_skill": active_skill,
    })

    return render(
        request,
        "users/participants.html",
        context,
    )


@require_http_methods(["GET"])
def skill_search_view(request):
    query = request.GET.get("q", "").strip()

    if not query:
        return JsonResponse([], safe=False)

    skills = (
        Skill.objects
        .filter(name__istartswith=query)
        .order_by(Lower("name"), "pk")
        .values("id", "name")[:10]
    )

    return JsonResponse(list(skills), safe=False)


@require_POST
def skill_add_view(request, pk):
    if not request.user.is_authenticated:
        return skill_error("Необходимо войти в аккаунт.", 401)

    if request.user.pk != pk:
        return skill_error(
            "Можно изменять навыки только своего профиля.",
            403,
        )

    try:
        payload = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return skill_error("Некорректный JSON.", 400)

    if not isinstance(payload, dict):
        return skill_error("Ожидается JSON-объект.", 400)

    form = SkillAddForm(payload)

    if not form.is_valid():
        return JsonResponse(
            {
                "status": "error",
                "errors": form.errors.get_json_data(),
            },
            status=400,
        )

    with transaction.atomic():
        profile_user = (
            User.objects.select_for_update()
            .filter(pk=pk)
            .first()
        )

        if profile_user is None:
            return skill_error("Пользователь не найден.", 404)

        skill_id = form.cleaned_data.get("skill_id")

        if skill_id:
            skill = Skill.objects.filter(pk=skill_id).first()

            if skill is None:
                return skill_error("Навык не найден.", 404)

            created = False
        else:
            name = form.cleaned_data["name"]
            skill, created = Skill.objects.get_or_create(
                name__iexact=name,
                defaults={"name": name},
            )

        added = not profile_user.skills.filter(pk=skill.pk).exists()

        if added:
            profile_user.skills.add(skill)

    return JsonResponse({
        "status": "ok",
        "id": skill.pk,
        "skill_id": skill.pk,
        "name": str(escape(skill.name)),
        "created": created,
        "added": added,
    })


@require_POST
def skill_remove_view(request, pk, skill_id):
    if not request.user.is_authenticated:
        return skill_error("Необходимо войти в аккаунт.", 401)

    if request.user.pk != pk:
        return skill_error(
            "Можно изменять навыки только своего профиля.",
            403,
        )

    with transaction.atomic():
        profile_user = (
            User.objects.select_for_update()
            .filter(pk=pk)
            .first()
        )

        if profile_user is None:
            return skill_error("Пользователь не найден.", 404)

        if not profile_user.skills.filter(pk=skill_id).exists():
            return skill_error(
                "Этот навык не добавлен в профиль.",
                404,
            )

        profile_user.skills.remove(skill_id)

    return JsonResponse({
        "status": "ok",
        "removed": True,
        "skill_id": skill_id,
    })