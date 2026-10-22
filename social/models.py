
from django.db import models


class PostComment(models.Model):
    post_id = models.CharField(max_length=100)
    author_name = models.CharField(max_length=100)
    comment_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author_name}: {self.comment_text[:30]}"


class PostLike(models.Model):
    post_id = models.CharField(max_length=100)
    user_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user_name} liked post {self.post_id}"
