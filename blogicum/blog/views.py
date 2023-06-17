# from django.http import HttpResponse, HttpRequest
from django.shortcuts import get_object_or_404, get_list_or_404, redirect
from django.views.generic import (
    CreateView,
    ListView,
    DetailView,
    UpdateView,
    DeleteView,
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Count, Q
from django.urls import reverse

from .models import Post, Category, Comment
from .forms import PostForm, CommentForm, UserForm

POST_PER_PAGE: int = 10

datenow = timezone.now()

User = get_user_model()


class PaginatorMixin:
    paginate_by = POST_PER_PAGE


class ProfileMixin:
    model = User


class IndexListView(PaginatorMixin, ListView):
    """Главная страница."""
    model = Post
    template_name = 'blog/index.html'

    def get_queryset(self):
        return Post.objects.filter(
            Q(pub_date__lte=datenow)
            & Q(is_published=True)
            & Q(category__is_published=True)
        ).order_by(
            '-pub_date',
            'title'
        ).annotate(comment_count=Count('comment'))


class PostDetailView(DetailView):
    """Страница поста."""
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = (Comment.objects.select_related(
            'author'
        ).filter(
            post_id=self.kwargs['id']
        ))
        return context


class CategoryPostsListView(PaginatorMixin, ListView):
    """Страница с категориями."""
    model = Post
    template_name = 'blog/category.html'
    slug_url_kwarg = 'category_slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context

    def get_queryset(self):
        self.category = get_object_or_404(
            Category.objects.filter(
                Q(slug=self.kwargs['category_slug'])
                & Q(is_published=True)
            ),
            slug=self.kwargs['category_slug']
        )
        return Post.objects.all().filter(
            Q(pub_date__lte=datenow)
            & Q(category__slug=self.kwargs['category_slug'])
            & Q(is_published=True)
        ).order_by(
            '-pub_date',
            'title'
        ).annotate(comment_count=Count('comment'))


class ProfileListView(ProfileMixin, PaginatorMixin, ListView):
    """Страница профиля."""
    template_name = 'blog/profile.html'
    slug_url_kwarg = 'username'

    def get_queryset(self):
        self.author = get_object_or_404(User, username=self.kwargs['username'])
        return Post.objects.all().filter(
            author=self.author
        ).order_by(
            '-pub_date',
            'title'
        ).annotate(
            comment_count=Count('comment')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.author
        return context


class ProfilUpdateView(ProfileMixin, LoginRequiredMixin, UpdateView):
    """Редактивование страници профиля. """
    form_class = UserForm
    template_name = 'blog/user.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_queryset(self):
        self.author = get_list_or_404(User, username=self.kwargs['username'])
        return super().get_queryset()

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user}
        )


class CreatePostCreateView(LoginRequiredMixin, CreateView):
    """Создание поста."""
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user}
        )


class EditPostUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование поста."""
    model = Post
    form_class = PostForm
    pk_url_kwarg = 'post_id'
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.kwargs['post_id']
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        posts = get_object_or_404(Post, id=self.kwargs['post_id'])
        if request.user != posts.author:
            return redirect('blog:post_detail', id=posts.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'id': self.kwargs['post_id']}
        )


class DeletePostDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление поста."""
    model = Post
    form_class = PostForm
    pk_url_kwarg = 'post_id'
    template_name = 'blog/create.html'

    def dispatch(self, request, *args, **kwargs):
        posts = get_object_or_404(Post, id=self.kwargs['post_id'])
        if request.user != posts.author:
            return redirect('blog:post_detail', id=posts.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user}
        )


class CommentCreateView(LoginRequiredMixin, CreateView):
    """Создание комментария."""
    posts = None
    model = Comment
    form_class = CommentForm
    pk_url_kwarg = 'post_id'
    # template_name = 'blog/comment.html'

    # Переопределяем dispatch()
    def dispatch(self, request, *args, **kwargs):
        self.posts = get_object_or_404(Post, pk=kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    # Переопределяем form_valid()
    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.posts
        return super().form_valid(form)

    # Переопределяем get_success_url()
    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'id': self.posts.pk}
        )


class EditCommentUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование комментария."""
    model = Comment
    form_class = CommentForm
    pk_url_kwarg = 'comment_id'
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        posts = get_object_or_404(Comment, id=self.kwargs['comment_id'])
        if request.user != posts.author:
            return redirect('blog:post_detail', id=posts.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'id': self.kwargs['post_id']}
        )


class DeleteCommentDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление комментария."""
    model = Comment
    pk_url_kwarg = 'comment_id'
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        posts = get_object_or_404(Comment, id=self.kwargs['comment_id'])
        if request.user != posts.author:
            return redirect('blog:post_detail', id=posts.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'id': self.kwargs['post_id']}
        )
