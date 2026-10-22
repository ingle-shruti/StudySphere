from pathlib import Path

from bson import ObjectId
from bson.errors import InvalidId

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from .models import (
    StudyPost,
    StudyBookmark,
    StudentProfile,
    StudyNotification,
    StudyLike,
    StudyComment,
)

from accounts.models import StudentProfile as AccountStudentProfile
from accounts.models import StudentFollow


MAX_PDF_SIZE = 10 * 1024 * 1024
MAX_PROFILE_PHOTO_SIZE = 5 * 1024 * 1024
POSTS_PER_PAGE = 10


def can_manage_post(user, post):
    """Allow only the post owner or a superuser to manage the post."""
    if not user.is_authenticated:
        return False

    return user.is_superuser or post.author_name == user.username


def validate_post_data(title, content, notes_file=None):
    """Validate study post fields and optional PDF upload."""
    if not title:
        return "Post title is required."

    if len(title) > 200:
        return "Title must be 200 characters or fewer."

    if not content:
        return "Post content is required."

    if notes_file:
        if Path(notes_file.name).suffix.lower() != ".pdf":
            return "Please upload a PDF file only."

        if notes_file.size > MAX_PDF_SIZE:
            return "PDF file must be 10 MB or smaller."

    return ""


@login_required
def home(request):
    """Display filtered, sorted and paginated study posts."""
    error = ""

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()
        subject = request.POST.get("subject", "").strip()
        notes_file = request.FILES.get("notes_file")

        error = validate_post_data(title, content, notes_file)

        if not error and len(subject) > 100:
            error = "Subject must be 100 characters or fewer."

        if not error:
            StudyPost.objects.create(
                title=title,
                content=content,
                subject=subject,
                author_name=request.user.username,
                notes_file=notes_file,
            )

            messages.success(request, "Your study post was published!")
            return redirect("home")

    search_query = request.GET.get("q", "").strip()
    selected_subject = request.GET.get("subject", "").strip()
    sort_by = request.GET.get("sort", "newest").strip()

    if sort_by not in ("newest", "oldest"):
        sort_by = "newest"

    posts = StudyPost.objects.all()

    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query)
            | Q(content__icontains=search_query)
        )

    if selected_subject:
        posts = posts.filter(subject=selected_subject)

    # Apply ordering before pagination.
    posts = posts.order_by(
        "created_at" if sort_by == "oldest" else "-created_at"
    )

    # Paginate after applying search, subject and sorting filters.
    paginator = Paginator(posts, POSTS_PER_PAGE)
    page_number = request.GET.get("page", 1)
    posts_page = paginator.get_page(page_number)

    all_subjects = StudyPost.objects.values_list("subject", flat=True)

    subjects = sorted({
        item.strip()
        for item in all_subjects
        if item and item.strip()
    })

    my_posts = StudyPost.objects.filter(
        author_name=request.user.username
    ).count()

    saved_post_ids = list(
        StudyBookmark.objects.filter(
            user=request.user
        ).values_list("post_id", flat=True)
    )

    # Posts liked by the current user.
    liked_post_ids = list(
        StudyLike.objects.filter(
            user=request.user
        ).values_list("post_id", flat=True)
    )

    # Get the current user's profile used by the follow system.
    current_profile, _ = AccountStudentProfile.objects.get_or_create(
        name=request.user.username,
        defaults={"username": request.user.username},
    )

    discover_students = []

    # Discover registered users who have a posts profile.
    registered_profiles = StudentProfile.objects.exclude(
        user=request.user
    )

    for user_profile in registered_profiles:
        username = user_profile.user.username

        account_profile = AccountStudentProfile.objects.filter(
            username=username
        ).first()

        if account_profile is None:
            account_profile = AccountStudentProfile.objects.filter(
                name=username,
                username__isnull=True,
            ).first()

            if account_profile is not None:
                account_profile.username = username
                account_profile.save()

        if account_profile is None:
            account_profile = AccountStudentProfile.objects.create(
                name=username,
                username=username,
            )

        is_following = StudentFollow.objects.filter(
            follower=current_profile,
            followed=account_profile,
        ).exists()

        discover_students.append({
            "profile": user_profile,
            "account_profile_id": account_profile.id,
            "is_following": is_following,
        })

    context = {
        "posts": posts_page,
        "page_obj": posts_page,
        "paginator": paginator,
        "total_posts": StudyPost.objects.count(),
        "my_posts": my_posts,
        "total_subjects": len(subjects),
        "subjects": subjects,
        "search_query": search_query,
        "selected_subject": selected_subject,
        "sort_by": sort_by,
        "error": error,
        "saved_post_ids": saved_post_ids,
        "liked_post_ids": liked_post_ids,
        "discover_students": discover_students,
    }

    return render(request, "posts/home.html", context)


@login_required
@require_POST
def delete_post(request, post_id):
    """Delete a post only when the requester has permission."""
    try:
        object_id = ObjectId(post_id)
    except (InvalidId, TypeError):
        messages.error(request, "Invalid post ID.")
        return redirect("home")

    post = get_object_or_404(StudyPost, pk=object_id)

    if not can_manage_post(request.user, post):
        messages.error(
            request,
            "You do not have permission to delete this post.",
        )
        return redirect("home")

    post.delete()
    messages.success(request, "Study post deleted successfully!")
    return redirect("home")


@login_required
def edit_post(request, post_id):
    """Edit a post only when the requester has permission."""
    try:
        object_id = ObjectId(post_id)
    except (InvalidId, TypeError):
        messages.error(request, "Invalid post ID.")
        return redirect("home")

    post = get_object_or_404(StudyPost, pk=object_id)

    if not can_manage_post(request.user, post):
        messages.error(
            request,
            "You do not have permission to edit this post.",
        )
        return redirect("home")

    error = ""

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        subject = request.POST.get("subject", "").strip()
        content = request.POST.get("content", "").strip()
        notes_file = request.FILES.get("notes_file")

        error = validate_post_data(title, content, notes_file)

        if not error and len(subject) > 100:
            error = "Subject must be 100 characters or fewer."

        if not error:
            post.title = title
            post.subject = subject
            post.content = content

            if notes_file:
                post.notes_file = notes_file

            post.save()

            messages.success(request, "Study post updated successfully!")
            return redirect("home")

    return render(
        request,
        "posts/edit_post.html",
        {"post": post, "error": error},
    )


@login_required
def my_posts(request):
    posts = StudyPost.objects.filter(
        author_name=request.user.username
    ).order_by("-created_at")

    return render(request, "posts/my_posts.html", {"posts": posts})


@login_required
def my_bookmarks(request):
    bookmarks = StudyBookmark.objects.filter(user=request.user)

    return render(
        request,
        "posts/my_bookmarks.html",
        {"bookmarks": bookmarks},
    )


@login_required
@require_POST
def toggle_bookmark(request, post_id):
    try:
        object_id = ObjectId(post_id)
    except (InvalidId, TypeError):
        messages.error(request, "Invalid post ID.")
        return redirect("home")

    post = get_object_or_404(StudyPost, pk=object_id)

    bookmark = StudyBookmark.objects.filter(
        user=request.user,
        post=post,
    ).first()

    if bookmark:
        bookmark.delete()
        messages.success(request, "Post removed from My Bookmarks.")
    else:
        StudyBookmark.objects.create(user=request.user, post=post)
        messages.success(request, "Post added to My Bookmarks.")

    next_url = request.POST.get("next", "home")

    if next_url not in ("home", "my_bookmarks"):
        next_url = "home"

    return redirect(next_url)


@login_required
@require_POST
def toggle_like(request, post_id):
    """Like or unlike a study post."""
    try:
        object_id = ObjectId(post_id)
    except (InvalidId, TypeError):
        messages.error(request, "Invalid post ID.")
        return redirect("home")

    post = get_object_or_404(StudyPost, pk=object_id)

    like = StudyLike.objects.filter(
        user=request.user,
        post=post,
    ).first()

    if like:
        like.delete()
        messages.success(request, "Like removed.")
    else:
        StudyLike.objects.create(
            user=request.user,
            post=post,
        )
        messages.success(request, "You liked this post.")

    return redirect("home")


@login_required
@require_POST
def add_comment(request, post_id):
    """Add a comment to a study post."""
    try:
        object_id = ObjectId(post_id)
    except (InvalidId, TypeError):
        messages.error(request, "Invalid post ID.")
        return redirect("home")

    post = get_object_or_404(StudyPost, pk=object_id)
    content = request.POST.get("content", "").strip()

    if not content:
        messages.error(request, "Comment cannot be empty.")
    elif len(content) > 1000:
        messages.error(
            request,
            "Comment must be 1000 characters or fewer.",
        )
    else:
        StudyComment.objects.create(
            user=request.user,
            post=post,
            content=content,
        )
        messages.success(request, "Comment added successfully.")

    return redirect("home")


@login_required
def my_profile(request):
    profile, created = StudentProfile.objects.get_or_create(
        user=request.user,
        defaults={
            "name": request.user.get_full_name() or request.user.username
        },
    )

    error = ""

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        bio = request.POST.get("bio", "").strip()
        college = request.POST.get("college", "").strip()
        branch = request.POST.get("branch", "").strip()
        study_year = request.POST.get("study_year", "").strip()
        skills = request.POST.get("skills", "").strip()
        profile_image = request.POST.get("profile_image", "").strip()
        uploaded_photo = request.FILES.get("uploaded_photo")

        if not name:
            error = "Name is required."
        elif len(name) > 100:
            error = "Name must be 100 characters or fewer."
        elif len(college) > 200:
            error = "College name must be 200 characters or fewer."
        elif len(branch) > 100:
            error = "Branch must be 100 characters or fewer."
        elif len(study_year) > 50:
            error = "Study year must be 50 characters or fewer."
        elif len(skills) > 300:
            error = "Skills must be 300 characters or fewer."
        elif len(bio) > 500:
            error = "Bio must be 500 characters or fewer."
        elif len(profile_image) > 200:
            error = "Profile image URL is too long."

        if not error and uploaded_photo:
            if uploaded_photo.size > MAX_PROFILE_PHOTO_SIZE:
                error = "Profile photo must be 5 MB or smaller."
            else:
                extension = Path(uploaded_photo.name).suffix.lower()

                if extension not in (".jpg", ".jpeg", ".png", ".webp"):
                    error = "Upload a JPG, PNG, or WEBP photo only."

        if not error:
            profile.name = name
            profile.bio = bio
            profile.college = college
            profile.branch = branch
            profile.study_year = study_year
            profile.skills = skills
            profile.profile_image = profile_image

            if uploaded_photo:
                profile.uploaded_photo = uploaded_photo

            profile.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("my_profile")

    user_posts = StudyPost.objects.filter(
        author_name=request.user.username
    ).count()

    total_bookmarks = StudyBookmark.objects.filter(
        user=request.user
    ).count()

    context = {
        "profile": profile,
        "profile_user": request.user,
        "user_posts": user_posts,
        "total_bookmarks": total_bookmarks,
        "error": error,
    }

    return render(request, "posts/profile.html", context)


@login_required
def dashboard(request):
    user_posts = StudyPost.objects.filter(
        author_name=request.user.username
    ).count()

    total_posts = StudyPost.objects.count()
    total_bookmarks = StudyBookmark.objects.filter(
        user=request.user
    ).count()

    all_subjects = StudyPost.objects.values_list("subject", flat=True)

    subjects = sorted({
        item.strip()
        for item in all_subjects
        if item and item.strip()
    })

    recent_posts = StudyPost.objects.all().order_by("-created_at")[:5]

    context = {
        "user_posts": user_posts,
        "total_posts": total_posts,
        "total_bookmarks": total_bookmarks,
        "total_subjects": len(subjects),
        "recent_posts": recent_posts,
        "username": request.user.username,
    }

    return render(request, "posts/dashboard.html", context)


@login_required
def notifications_list(request):
    notifications = StudyNotification.objects.filter(
        recipient=request.user
    ).order_by("-created_at")

    unread_count = notifications.filter(is_read=False).count()

    return render(
        request,
        "posts/notifications.html",
        {
            "notifications": notifications,
            "unread_count": unread_count,
        },
    )


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    try:
        object_id = ObjectId(notification_id)
    except (InvalidId, TypeError):
        messages.error(request, "Invalid notification ID.")
        return redirect("notifications")

    notification = get_object_or_404(
        StudyNotification,
        pk=object_id,
        recipient=request.user,
    )

    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=["is_read"])

    messages.success(request, "Notification marked as read.")
    return redirect("notifications")



@login_required
def post_detail(request, post_id):
    """Display one study post."""
    try:
        object_id = ObjectId(post_id)
    except (InvalidId, TypeError):
        messages.error(request, "Invalid study post ID.")
        return redirect("home")

    post = get_object_or_404(StudyPost, pk=object_id)

    liked = StudyLike.objects.filter(
        user=request.user,
        post=post,
    ).exists()

    saved = StudyBookmark.objects.filter(
        user=request.user,
        post=post,
    ).exists()

    context = {
        "post": post,
        "liked": liked,
        "saved": saved,
    }

    return render(request, "posts/post_detail.html", context)
