
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [
    # Authentication
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # Profile and Dashboard
    path("profile/", views.profile_view, name="profile"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("students/", views.students_list_view, name="students_list"),
    path("edit-profile/", views.edit_profile_view, name="edit_profile"),

    # Follow / Unfollow student
    path(
        "follow/<str:profile_id>/",
        views.follow_toggle_view,
        name="follow_toggle",
    ),

    # Notifications
    path(
        "notifications/",
        views.notifications_view,
        name="notifications",
    ),

    # Followers and Following
    path(
        "followers/",
        views.follow_list_view,
        {"kind": "followers"},
        name="followers_list",
    ),
    path(
        "following/",
        views.follow_list_view,
        {"kind": "following"},
        name="following_list",
    ),

    # Forgot username
    path(
        "forgot-username/",
        views.forgot_username,
        name="forgot_username",
    ),

    # Forgot password
    path(
        "forgot-password/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset_form.html",
            email_template_name="accounts/password_reset_email.html",
            subject_template_name="accounts/password_reset_subject.txt",
            success_url="/accounts/forgot-password/sent/",
        ),
        name="password_reset",
    ),
    path(
        "forgot-password/sent/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            success_url="/accounts/reset/complete/",
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
]
