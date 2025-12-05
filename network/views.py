from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .models import User, Post


def index(request):
    if request.method == "POST":
        if request.user.is_authenticated:
            content = request.POST.get("content")
            if content:
                Post.objects.create(author=request.user, content=content)
                return redirect("index")

    posts = Post.objects.all().order_by("-timestamp")
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
    posts = Post.objects.filter(author=profile_user).order_by("-timestamp")

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

