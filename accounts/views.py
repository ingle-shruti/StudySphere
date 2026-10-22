
from pathlib import Path

from bson import ObjectId
from bson.errors import InvalidId

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
from django.http import Http404

from .models import StudentProfile, StudentFollow, Notification
from posts.models import StudyPost, StudyBookmark


MAX_PROFILE_PHOTO_SIZE = 5 * 1024 * 1024


def signup_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if not username or not email or not password:
            messages.error(request, "Please fill in all required fields.")
        elif password != confirm_password:
            messages.error(request, "Passwords do not match.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
        else:
            User.objects.create_user(
                username=username,
                email=email,
                password=password,
            )
            messages.success(request, "Account created! Please log in.")
            return redirect("login")

    return render(request, "accounts/signup.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:
            login(request, user)
            return redirect("home")

        messages.error(request, "Invalid username or password.")

    return render(request, "accounts/login.html")


def logout_view(request):
    if request.method == "POST":
        logout(request)

    return redirect("home")


@login_required(login_url="login")
def dashboard_view(request):
    profile, created = StudentProfile.objects.get_or_create(
        name=request.user.username
    )

    my_posts = StudyPost.objects.filter(
        author_name=request.user.username
    ).order_by("-created_at")

    following_count = StudentFollow.objects.filter(
        follower=profile
    ).count()

    followers_count = StudentFollow.objects.filter(
        followed=profile
    ).count()

    total_bookmarks = StudyBookmark.objects.filter(
        user=request.user
    ).count()

    all_subjects = StudyPost.objects.values_list(
        "subject", flat=True
    )

    subjects = {
        subject.strip()
        for subject in all_subjects
        if subject and subject.strip()
    }

    recent_posts = StudyPost.objects.all().order_by(
        "-created_at"
    )[:5]

    # Count unread notifications for the logged-in student
    unread_notifications = Notification.objects.filter(
        recipient=profile,
        is_read=False,
    ).count()

    context = {
        "profile": profile,
        "username": request.user.username,
        "total_posts": StudyPost.objects.count(),
        "my_posts": my_posts,
        "my_posts_count": my_posts.count(),
        "user_posts": my_posts.count(),
        "following_count": following_count,
        "followers_count": followers_count,
        "total_bookmarks": total_bookmarks,
        "total_subjects": len(subjects),
        "recent_posts": recent_posts,
        "unread_notifications": unread_notifications,
    }

    return render(
        request,
        "accounts/dashboard.html",
        context,
    )


@login_required(login_url="login")
def profile_view(request):
    profile, created = StudentProfile.objects.get_or_create(
        name=request.user.username
    )

    followers_count = StudentFollow.objects.filter(
        followed=profile
    ).count()

    following_count = StudentFollow.objects.filter(
        follower=profile
    ).count()

    user_posts = StudyPost.objects.filter(
        author_name=request.user.username
    ).count()

    return render(
        request,
        "accounts/profile.html",
        {
            "profile": profile,
            "followers_count": followers_count,
            "following_count": following_count,
            "user_posts": user_posts,
        },
    )


@login_required(login_url="login")
def edit_profile_view(request):
    profile, created = StudentProfile.objects.get_or_create(
        name=request.user.username
    )

    error = ""

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        bio = request.POST.get("bio", "").strip()
        profile_image = request.POST.get("profile_image", "").strip()
        college = request.POST.get("college", "").strip()
        branch = request.POST.get("branch", "").strip()
        study_year = request.POST.get("study_year", "").strip()
        skills = request.POST.get("skills", "").strip()
        uploaded_photo = request.FILES.get("uploaded_photo")

        if not name:
            error = "Name is required."
        elif len(name) > 100:
            error = "Name must be 100 characters or fewer."
        elif len(bio) > 500:
            error = "Bio must be 500 characters or fewer."
        elif len(college) > 200:
            error = "College name must be 200 characters or fewer."
        elif len(branch) > 100:
            error = "Branch must be 100 characters or fewer."
        elif len(study_year) > 50:
            error = "Study year must be 50 characters or fewer."
        elif len(skills) > 300:
            error = "Skills must be 300 characters or fewer."
        elif len(profile_image) > 200:
            error = "Profile image URL is too long."

        if not error and uploaded_photo:
            if uploaded_photo.size > MAX_PROFILE_PHOTO_SIZE:
                error = "Photo must be 5 MB or smaller."
            else:
                extension = Path(uploaded_photo.name).suffix.lower()

                if extension not in (".jpg", ".jpeg", ".png", ".webp"):
                    error = "Please upload a JPG, PNG, or WEBP image."

        if error:
            messages.error(request, error)
        else:
            profile.name = name
            profile.bio = bio
            profile.profile_image = profile_image
            profile.college = college
            profile.branch = branch
            profile.study_year = study_year
            profile.skills = skills

            if uploaded_photo:
                profile.uploaded_photo = uploaded_photo

            profile.save()

            messages.success(request, "Profile updated successfully!")
            return redirect("edit_profile")

    return render(
        request,
        "accounts/edit_profile.html",
        {"profile": profile},
    )


def forgot_username(request):
    message = ""

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        UserModel = get_user_model()
        users = UserModel.objects.filter(email__iexact=email)

        if email and users.exists():
            usernames = list(
                users.values_list("username", flat=True)
            )

            send_mail(
                subject="StudySphere - Username Recovery",
                message=(
                    "Your StudySphere username(s):\n"
                    + "\n".join(usernames)
                ),
                from_email=None,
                recipient_list=[email],
                fail_silently=False,
            )

        message = (
            "If an account matches that email, "
            "username recovery instructions have been sent."
        )

    return render(
        request,
        "accounts/forgot_username.html",
        {"message": message},
    )


@login_required(login_url="login")
@require_POST
def follow_toggle_view(request, profile_id):
    try:
        target_id = ObjectId(profile_id)
    except (InvalidId, TypeError):
        raise Http404("Student profile not found.")

    target_profile = get_object_or_404(
        StudentProfile,
        id=target_id,
    )

    current_profile, created = StudentProfile.objects.get_or_create(
        name=request.user.username
    )

    if current_profile.id == target_profile.id:
        messages.error(request, "You cannot follow yourself.")
        return redirect("students_list")

    follow = StudentFollow.objects.filter(
        follower=current_profile,
        followed=target_profile,
    )

    if follow.exists():
        follow.delete()
        messages.success(request, "Student unfollowed.")
    else:
        StudentFollow.objects.create(
            follower=current_profile,
            followed=target_profile,
        )

        Notification.objects.create(
            recipient=target_profile,
            sender=current_profile,
            message=f"{current_profile.name} started following you.",
        )

        messages.success(request, "Student followed!")

    return redirect("students_list")


@login_required(login_url="login")
def students_list_view(request):
    current_profile, created = StudentProfile.objects.get_or_create(
        name=request.user.username
    )

    students = StudentProfile.objects.exclude(
        id=current_profile.id
    )

    following_ids = list(
        StudentFollow.objects.filter(
            follower=current_profile
        ).values_list("followed_id", flat=True)
    )

    return render(
        request,
        "accounts/students.html",
        {
            "students": students,
            "following_ids": following_ids,
        },
    )


@login_required(login_url="login")
def follow_list_view(request, kind):
    current_profile, created = StudentProfile.objects.get_or_create(
        name=request.user.username
    )

    if kind == "followers":
        follow_records = StudentFollow.objects.filter(
            followed=current_profile
        ).select_related("follower")

        page_title = "My Followers"
        students = [record.follower for record in follow_records]

    elif kind == "following":
        follow_records = StudentFollow.objects.filter(
            follower=current_profile
        ).select_related("followed")

        page_title = "Students I Follow"
        students = [record.followed for record in follow_records]

    else:
        raise Http404("Follow list not found.")

    following_ids = list(
        StudentFollow.objects.filter(
            follower=current_profile
        ).values_list("followed_id", flat=True)
    )

    return render(
        request,
        "accounts/follow_list.html",
        {
            "students": students,
            "following_ids": following_ids,
            "page_title": page_title,
            "kind": kind,
        },
    )


@login_required(login_url="login")
def notifications_view(request):
    current_profile, created = StudentProfile.objects.get_or_create(
        name=request.user.username
    )

    notifications = Notification.objects.filter(
        recipient=current_profile
    ).order_by("-created_at")

    unread_count = notifications.filter(is_read=False).count()

    if request.method == "POST":
        notifications.filter(is_read=False).update(is_read=True)
        messages.success(request, "All notifications marked as read.")
        return redirect("notifications")

    return render(
        request,
        "accounts/notifications.html",
        {
            "notifications": notifications,
            "unread_count": unread_count,
        },
    )
