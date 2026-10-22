
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django Admin
    path("admin/", admin.site.urls),

    # Authentication, account profiles and student features
    path("accounts/", include("accounts.urls")),

    # Home, posts, bookmarks and StudySphere features
    path("", include("posts.urls")),
]

# Serve uploaded files during development
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
