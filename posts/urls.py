
from django.urls import path
from . import views

urlpatterns = [
    # Notifications
    path(
        "notifications/",
        views.notifications_list,
        name="notifications",
    ),
    path(
        "notifications/read/<str:notification_id>/",
        views.mark_notification_read,
        name="mark_notification_read",
    ),

    # Home
    path("", views.home, name="home"),

    # My Posts
    path("my-posts/", views.my_posts, name="my_posts"),

    # Edit Post
    path(
        "edit/<str:post_id>/",
        views.edit_post,
        name="edit_post",
    ),

    # Delete Post
    path(
        "delete/<str:post_id>/",
        views.delete_post,
        name="delete_post",
    ),

    # Bookmarks
    path("bookmarks/", views.my_bookmarks, name="my_bookmarks"),
    path(
        "bookmark/<str:post_id>/",
        views.toggle_bookmark,
        name="toggle_bookmark",
    ),

    # Like / Unlike
    path(
        "like/<str:post_id>/",
        views.toggle_like,
        name="toggle_like",
    ),

    # Add Comment
    path(
        "comment/<str:post_id>/",
        views.add_comment,
        name="add_comment",
    ),

    # Posts Dashboard
    path(
        "dashboard/",
        views.dashboard,
        name="posts_dashboard",
    ),

    # My Profile
    path(
        "profile/",
        views.my_profile,
        name="my_profile",
    ),

    # Study Post Details
    path(
        "post/<str:post_id>/",
        views.post_detail,
        name="post_detail",
    ),
]
