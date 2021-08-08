from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET

from posts.forms import CommentForm, PostForm
from yatube.settings import POSTS_PER_PAGE

from .models import Comment, Follow, Group, Post

User = get_user_model()


@require_GET
def index(request):
    post_list = cache.get('index_page')
    if post_list is None:
        post_list = Post.objects.all().prefetch_related('author', 'group')
        cache.set('index_page', post_list, timeout=20)

    paginator = Paginator(post_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    return render(request, 'posts/index.html', {
        'page': page,
        'post_list': post_list})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post = Post.objects.filter(group=group).prefetch_related('author', 'group')
    paginator = Paginator(post, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    return render(request, 'posts/group.html', {
        'group': group,
        'page': page, 'post': post})


def profile(request, username):
    profile = get_object_or_404(User, username=username)
    user = request.user
    posts = Post.objects.filter(author=profile).prefetch_related(
        'author', 'group')
    paginator = Paginator(posts, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = user.is_authenticated and (
        Follow.objects.filter(user=user, author=profile).exists())
    return render(request, 'posts/profile.html', {
        'profile': profile, 'page': page,
        'posts': posts, 'following': following})


def post_view(request, username, post_id):
    profile = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author__username=username)
    post = get_object_or_404(
        Post, author__username=username, id=post_id)
    comments = Comment.objects.filter(post_id=post)
    comment_form = CommentForm()
    return render(request, 'posts/post.html', {
        'profile': profile,
        'post': post, 'posts': posts,
        'comments': comments,
        'form': comment_form})


@login_required
def new_post(request):
    action_name = 'Добавить запись'
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('index')
    else:
        form = PostForm()
    return render(request, 'posts/new.html', {
        'form': form,
        'action_name': action_name})


@login_required
def post_edit(request, username, post_id):
    if request.user.username != username:
        return redirect('post', username=username, post_id=post_id)
    post = get_object_or_404(
        Post,
        author__username=username,
        id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    action_name = 'Редактировать запись'

    if form.is_valid():
        form.save()
        return redirect('post', username=post.author, post_id=post.pk)

    return render(request, 'posts/new.html', {
        'form': form,
        'action_name': action_name, 'post': post},)


def page_not_found(request, exception):
    return render(
        request,
        'misc/404.html',
        {'path': request.path},
        status=404
    )


def server_error(request):
    return render(request, 'misc/500.html', status=500)


@login_required
def add_comment(request, username, post_id):
    action_name = 'Добавить комментарий'
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(
        request.POST or None
    )
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('post', username=post.author, post_id=post_id)
    else:
        form = CommentForm()
    return render(request, 'posts/post.html', {
        'form': form,
        'action_name': action_name})


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "posts/follow.html", {'page': page, 'posts': posts})


@login_required
def profile_follow(request, username):
    if request.user.username != username:
        author = get_object_or_404(User, username=username)
        user = request.user
        Follow.objects.get_or_create(author=author, user=user)
    return redirect("profile", username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    Follow.objects.filter(author=author, user=user).delete()
    return redirect("profile", username=username)
