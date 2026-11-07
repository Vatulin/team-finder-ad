from django.urls import path

from . import views


app_name = "projects"

urlpatterns = [
    path(
        "create-project/",
        views.project_create_view,
        name="create",
    ),
    path(
        "<int:pk>/",
        views.project_detail_view,
        name="detail",
    ),
    path(
        "<int:pk>/edit/",
        views.project_edit_view,
        name="edit",
    ),
    path(
        "<int:pk>/complete/",
        views.project_complete_view,
        name="complete",
    ),
    path(
        "<int:pk>/toggle-participate/",
        views.project_toggle_participate_view,
        name="toggle_participate",
    ),
    path("list/", views.project_list_view, name="list"),
        path(
        "favorites/",
        views.favorite_projects_view,
        name="favorites",
    ),
    path(
        "<int:pk>/toggle-favorite/",
        views.toggle_favorite_view,
        name="toggle_favorite",
    ),
]