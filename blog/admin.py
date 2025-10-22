from django.contrib import admin
from .models import Article, Comment, Like, Attachment, Admin as BlogAdmin, Category

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'author', 'published_at', 'is_featured')
    list_filter = ('status', 'is_featured', 'published_at', 'categories')
    search_fields = ('title', 'summary', 'content')
    prepopulated_fields = {"slug": ("title",)}

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('article', 'user_name', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('user_name', 'content')

@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('wording', 'attachment_type', 'article', 'created_at')
    list_filter = ('attachment_type', 'created_at')
    search_fields = ('wording',)

@admin.register(BlogAdmin)
class BlogAdminAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active')
    search_fields = ('name', 'email')
