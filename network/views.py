from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .models import User, Post
from django.core.paginator import Paginator

def index(request):
    if request.method == "POST":
        if request.user.is_authenticated:
            content = request.POST.get("content")
            if content:
                Post.objects.create(author=request.user, content=content)
                return redirect("index")
    
    posts_list = Post.objects.all().order_by("-timestamp")
    paginator = Paginator(posts_list, 10) # 10 posts per page
    page_number = request.GET.get("page")
    posts = paginator.get_page(page_number)

    return render(request, "network/index.html", {"posts": posts})

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))

def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")
    
def profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    posts_list = Post.objects.filter(author=profile_user).order_by("-timestamp")

    paginator = Paginator(posts_list, 10) # 10 posts per page
    page_number = request.GET.get("page")
    posts = paginator.get_page(page_number)

    is_following = False # value at the beggining
    if request.user.is_authenticated and request.user != profile_user:
        is_following = profile_user.followers.filter(id=request.user.id).exists()

    if request.method == "POST" and request.user.is_authenticated and request.user != profile_user:
        if is_following:
            profile_user.followers.remove(request.user)
        
        else:
            profile_user.followers.add(request.user)
        
        return redirect("profile", username=username)
    
    context = {
        "profile_user" : profile_user,
        "posts": posts,
        "followers_count": profile_user.followers.count(),
        "following_count": profile_user.following.count(),
        "is_following": is_following,
    }
    return render(request, "network/profile.html", context)

@login_required
def following(request):
    # All the users the current user follows
    following_users = request.user.following.all()

    # Posts by those users
    posts_list = Post.objects.filter(author__in=following_users).order_by("-timestamp")

    paginator = Paginator(posts_list, 10) # 10 posts per page
    page_number = request.GET.get("page")
    posts = paginator.get_page(page_number)

    return render(request, "network/following.html", {"posts": posts})

@login_required
def edit_post(request, post_id):
    if request.method == "POST":
        post = get_object_or_404(Post, id=post_id)

        # Only the author should be allowed to edit
        if post.author != request.user:
            return JsonResponse({"error": "You cannot edit this post."}, status=403)

        new_content = request.POST.get("content")
        if new_content:
            post.content = new_content
            post.edited = True   # mark as edited
            post.save()
            return JsonResponse({
                "message": "Post updated successfully.",
                "content": post.content,
                "edited": post.edited
            })
        
        return JsonResponse({"error": "No content provided."}, status=400)

    return JsonResponse({"error": "Invalid request method."}, status=405)

@login_required
def toggle_like(request, post_id):
    if request.method == "POST":
        post = get_object_or_404(Post, id=post_id)
        user = request.user

        if user in post.likes.all():
            post.likes.remove(user)
            liked = False
        else:
            post.likes.add(user)
            liked = True

        return JsonResponse({
            "liked": liked,
            "likes_count": post.likes.count()
        })

    return JsonResponse({"error": "Invalid request method."}, status=405) # Just in case