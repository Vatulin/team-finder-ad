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

from .forms import LoginForm, ProfileEditForm, RegistrationForm
from .models import User


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

        return redirect("users:detail", pk=request.user.pk)

    return render(
        request,
        "users/login.html",
        {"form": form, "next": next_url},
    )


@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, "Вы вышли из аккаунта.")
    return redirect("users:login")


@require_http_methods(["GET"])
def profile_view(request, pk):
    users = User.objects.prefetch_related(
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