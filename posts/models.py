
from django.db import models
from django.conf import settings


class StudyPost(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    subject = models.CharField(max_length=100, blank=True)
    author_name = models.CharField(max_length=100)

    notes_file = models.FileField(
        upload_to="study_notes/",
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class StudyBookmark(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="study_bookmarks",
    )
    post = models.ForeignKey(
        StudyPost,
        on_delete=models.CASCADE,
        related_name="bookmarks",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "post"],
                name="unique_user_study_bookmark",
            )
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} bookmarked {self.post}"


class StudyLike(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="study_likes",
    )
    post = models.ForeignKey(
        StudyPost,
        on_delete=models.CASCADE,
        related_name="likes",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "post"],
                name="unique_user_study_like",
            )
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} liked {self.post}"


class StudyComment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="study_comments",
    )
    post = models.ForeignKey(
        StudyPost,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    content = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.user} on {self.post}"


class StudentProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )
    name = models.CharField(max_length=100, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    college = models.CharField(max_length=200, blank=True)
    branch = models.CharField(max_length=100, blank=True)
    study_year = models.CharField(max_length=50, blank=True)
    skills = models.CharField(max_length=300, blank=True)
    profile_image = models.URLField(blank=True)
    uploaded_photo = models.ImageField(
        upload_to="profile_photos/",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or self.user.username


class StudyNotification(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="study_notifications",
    )
    message = models.CharField(max_length=250)
    link = models.CharField(max_length=300, default="/")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.message
