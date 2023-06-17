import datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count, Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, UpdateView

from blog.models import Category, Comment, Post
from .forms import CommentForm, PostForm, UserForm

PAGINATOR_VALUE = 10
PAGE_NUMBER = "page"


def get_post_filter():
    time_now = datetime.datetime.now()
    return Post.objects.select_related(
        "location", "category", "author"
    ).filter(
        pub_date__lte=time_now,
        is_published=True,
        category__is_published=True,
    )


@login_required
def index(request):
    template = "blog/index.html"
    post_list = (
        get_post_filter()
        .order_by("-pub_date")
        .annotate(comment_count=Count("comments"))
    )
    paginator = Paginator(post_list, PAGINATOR_VALUE)
    page_number = request.GET.get(PAGE_NUMBER)
    page_obj = paginator.get_page(page_number)
    context = {"page_obj": page_obj}
    return render(request, template, context)


@login_required
def post_detail(request, id):
    template = "blog/detail.html"
    post = get_object_or_404(get_post_filter(), id=id)
    context = {
        "post": post,
        "form": CommentForm(),
        "comments": Comment.objects.filter(post_id=id),
    }
    return render(request, template, context)


@login_required
def category_posts(request, category_slug):
    template = "blog/category.html"
    category = get_object_or_404(
        Category.objects.prefetch_related(
            Prefetch(
                "posts",
                get_post_filter()
                .order_by("-pub_date")
                .annotate(comment_count=Count("comments")),
            )
        ).filter(slug=category_slug),
        is_published=True,
    )
    post_list = category.posts.all()
    paginator = Paginator(post_list, PAGINATOR_VALUE)
    page_number = request.GET.get(PAGE_NUMBER)
    page_obj = paginator.get_page(page_number)
    context = {
        "category": category,
        "page_obj": page_obj,
    }
    return render(request, template, context)


def get_profile(request, username_slug):
    template = "blog/profile.html"
    if request.user.username == username_slug:
        queryset = Post.objects.select_related(
            "location", "category", "author"
        )
    else:
        queryset = get_post_filter()
    user = get_object_or_404(
        User.objects.prefetch_related(
            Prefetch(
                "posts_user",
                queryset.order_by("-pub_date").annotate(
                    comment_count=Count("comments")
                ),
            ),
        ).filter(username=username_slug)
    )
    post_list = user.posts_user.all()
    paginator = Paginator(post_list, PAGINATOR_VALUE)
    page_number = request.GET.get(PAGE_NUMBER)
    page_obj = paginator.get_page(page_number)
    context = {"profile": user, "page_obj": page_obj}
    return render(request, template, context)


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = "blog/create.html"

    def get_success_url(self):
        slug = self.request.user.username
        return reverse("blog:profile", kwargs={"username_slug": slug})

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = "blog/create.html"

    def dispatch(self, request, *args, **kwargs):
        publication = get_object_or_404(Post, pk=kwargs["pk"])
        if publication.author != request.user:
            return redirect("blog:post_detail", id=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("blog:post_detail", kwargs={"id": self.kwargs["pk"]})

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = "blog/user.html"
    form_class = UserForm
    success_url = reverse_lazy("blog:index")


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm

    def form_valid(self, form):
        comment = get_object_or_404(Post, pk=self.kwargs["pk"])
        form.instance.author = self.request.user
        form.instance.post = comment
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("blog:post_detail", kwargs={"id": self.kwargs["pk"]})


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    model = Comment
    template_name = "blog/comment.html"
    form_class = CommentForm

    def dispatch(self, request, *args, **kwargs):
        comment = get_object_or_404(Comment, pk=kwargs["pk"])
        if comment.author != request.user:
            return redirect("blog:post_detail", comment.post_id)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            "blog:post_detail", kwargs={"id": self.kwargs["post_id"]}
        )


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = "blog/create.html"
    success_url = reverse_lazy("blog:index")

    def dispatch(self, request, *args, **kwargs):
        publication = get_object_or_404(Post, pk=kwargs["pk"])
        if publication.author != request.user:
            return redirect("blog:post_detail", id=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = {"instance": self.object}
        return context


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    model = Comment
    template_name = "blog/comment.html"
    success_url = reverse_lazy("blog:index")

    def dispatch(self, request, *args, **kwargs):
        comment = get_object_or_404(Comment, pk=kwargs["pk"])
        if comment.author != request.user:
            return redirect("blog:post_detail", id=kwargs["post_id"])
        return super().dispatch(request, *args, **kwargs)
