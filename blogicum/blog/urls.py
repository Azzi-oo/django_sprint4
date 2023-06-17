from django.urls import path

from . import views

app_name = 'blog'

urlpatterns = [
    path(
        '',
        views.IndexListView.as_view(),
        name='index'
    ),
    path(
        'posts/<int:id>/',
        views.PostDetailView.as_view(),
        name='post_detail'
    ),
    path(
        'posts/create/',
        views.CreatePostCreateView.as_view(),
        name='create_post'
    ),
    path(
        'posts/<int:post_id>/edit/',
        views.EditPostUpdateView.as_view(),
        name='edit_post'
    ),
    path(
        'posts/<int:post_id>/delete/',
        views.DeletePostDeleteView.as_view(),
        name='delete_post',
    ),
    path(
        'posts/<int:post_id>/comment/',
        views.CommentCreateView.as_view(),
        name='add_comment',
    ),
    path(
        'posts/<int:post_id>/edit_comment/<int:comment_id>/',
        views.EditCommentUpdateView.as_view(),
        name='edit_comment',
    ),
    path(
        'posts/<int:post_id>/delete_comment/<int:comment_id>/',
        views.DeleteCommentDeleteView.as_view(),
        name='delete_comment',
    ),
    path(
        'category/<slug:category_slug>/',
        views.CategoryPostsListView.as_view(),
        name='category_posts'
    ),
    path(
        'profile/<slug:username>/',
        views.ProfileListView.as_view(),
        name='profile'
    ),
    path(
        'edit_profile/<slug:username>/',
        views.ProfilUpdateView.as_view(),
        name='edit_profile',
    ),
]
