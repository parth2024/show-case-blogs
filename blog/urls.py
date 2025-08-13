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
    
    # Public article viewing (NEW)
    path('article/<slug:slug>/', views.PublicArticleView.as_view(), name='public_article'),
    
    # Optional: Public blog homepage
    path('', views.BlogHomeView.as_view(), name='blog_home'),

    path('upload-image/', views.upload_image_view, name='upload_image'),
]