
from django.db import models


class StudentProfile(models.Model):
    name = models.CharField(max_length=100)

    username = models.CharField(
        max_length=150,
        unique=True,
        blank=True,
        null=True,
    )

    bio = models.TextField(blank=True)
    college = models.CharField(max_length=200, blank=True)
    branch = models.CharField(max_length=100, blank=True)
    study_year = models.CharField(max_length=50, blank=True)
    skills = models.CharField(max_length=300, blank=True)

    profile_image = models.URLField(blank=True)

    uploaded_photo = models.ImageField(
        upload_to="profile_photos/",
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class StudentFollow(models.Model):
    follower = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="following",
    )

    followed = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="followers",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["follower", "followed"],
                name="unique_student_follow",
            )
        ]

    def __str__(self):
        return f"{self.follower.name} follows {self.followed.name}"
class Notification(models.Model):
    recipient = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    sender = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="sent_notifications",
    )

    message = models.CharField(max_length=255)

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message