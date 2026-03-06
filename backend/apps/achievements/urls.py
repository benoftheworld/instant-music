"""URL configuration for achievements app.
"""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.AchievementListView.as_view(), name="achievement-list"),
    path(
        "mine/",
        views.UserAchievementListView.as_view(),
        name="user-achievement-list",
    ),
    path(
        "user/<uuid:user_id>/",
        views.UserAchievementsByUserView.as_view(),
        name="user-achievements-by-user",
    ),
]
