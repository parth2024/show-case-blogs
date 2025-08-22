from django.urls import path
from . import views

urlpatterns = [
    # Admin authentication
    path('login/', views.LoginView.as_view(), name='admin_login'),
    path('logout/', views.logout_view, name='admin_logout'),

    # Admin dashboard
    path('dashboard/', views.dashboard_view, name='admin_dashboard'),
    path('profile/', views.ProfileView.as_view(), name='admin_profile'),
    path('archived/', views.archived_articles_view, name='admin_archived'),

    # Article management
    path('create/', views.CreateArticleView.as_view(), name='create_article'),
    path('article/<int:article_id>/', views.view_article, name='view_article'),
    path('article/<int:article_id>/edit/', views.edit_article, name='edit_article'),
    path('preview/', views.PreviewArticleView.as_view(), name='preview_article'),

    # Article actions
    path('article/<int:article_id>/toggle/', views.toggle_article_status, name='toggle_article_status'),
    path('article/<int:article_id>/archive/', views.archive_article, name='archive_article'),
    path('article/<int:article_id>/restore/', views.restore_article, name='restore_article'),
    path('article/<int:article_id>/delete/', views.delete_article, name='delete_article'),

    # Admin creation (restricted)
    path('create-admin/', views.CreateAdminView.as_view(), name='create_admin_user'),

    # AJAX endpoints
    path('search/', views.search_articles_ajax, name='search_articles_ajax'),
    path('load-more-articles/', views.load_more_articles, name='load_more_articles'),

    # Public article viewing
    path('article/<slug:slug>/', views.PublicArticleView.as_view(), name='public_article'),

    # Public actions
    path('subscribe/', views.subscribe_newsletter, name='subscribe_newsletter'),
    path('like/<int:article_id>/', views.like_article, name='like_article'),

    # Optional: Public blog homepage
    path('', views.BlogHomeView.as_view(), name='blog_home'),

    # Image upload
    path('upload-image/', views.upload_image_view, name='upload_image'),
]