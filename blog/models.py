from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from django.utils.text import slugify
from django.db.models import JSONField


class Admin(models.Model):
    """Custom admin model for blog administration"""
    name = models.CharField(max_length=100, null=True, blank=True)
    email = models.CharField(max_length=254, null=True, blank=True, unique=True)
    password = models.CharField(max_length=128, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def set_password(self, raw_password):
        """Hash and set the password"""
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """Check if the provided password is correct"""
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.name or self.email or f"Admin {self.id}"

    class Meta:
        db_table = 'blog_admin'


class User(models.Model):
    """Newsletter subscribers"""
    name = models.CharField(max_length=100, null=True, blank=True)
    email = models.CharField(max_length=254, null=True, blank=True)
    registered_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.name or self.email or f"User {self.id}"

    class Meta:
        db_table = 'blog_user'


class Article(models.Model):
    """Blog articles"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    title = models.CharField(max_length=200, null=True, blank=True)
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)
    summary = models.TextField(null=True, blank=True)
    link = models.TextField(null=True, blank=True)  # For external links if needed
    content = models.TextField(null=True, blank=True)
    content_json = JSONField(null=True, blank=True)  # Stores Quill Delta
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    author = models.ForeignKey(Admin, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    islike = models.BooleanField(default=False)  # For featured articles

    def generate_unique_slug(self, title):
        """Generate a unique slug for the article"""
        base_slug = slugify(title)
        if not base_slug:
            base_slug = f"article-{self.id}"
        
        slug = base_slug
        counter = 1
        
        # Check if slug exists, if so, append a number
        while Article.objects.filter(slug=slug).exclude(id=self.id).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug

    def save(self, *args, **kwargs):
        """Auto-generate slug from title if not provided"""
        if not self.slug and self.title:
            self.slug = self.generate_unique_slug(self.title)
        elif self.title and self.slug:
            # Update slug if title changed
            expected_slug = self.generate_unique_slug(self.title)
            if self.slug != expected_slug and slugify(self.title) not in self.slug:
                self.slug = expected_slug
        
        # Set published_at when status changes to published
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Get the public URL for this article"""
        from django.urls import reverse
        return reverse('public_article', kwargs={'slug': self.slug})

    def __str__(self):
        return self.title or f"Article {self.id}"

    class Meta:
        db_table = 'blog_article'
        ordering = ['-created_at']


class Commenter(models.Model):
    """Comments on articles"""
    content = models.CharField(max_length=5000, null=True, blank=True)

    def __str__(self):
        return f"Comment {self.id}"

    class Meta:
        db_table = 'blog_commenter'


class Attachment(models.Model):
    """File attachments for articles"""
    wording = models.CharField(max_length=200, null=True, blank=True)  # Description
    link = models.CharField(max_length=500, null=True, blank=True)  # File URL
    file_path = models.CharField(max_length=500, null=True, blank=True)  # Local file path
    attachment_type = models.CharField(max_length=20, null=True, blank=True)  # image, document, etc.
    article = models.ForeignKey(Article, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    display_style = models.CharField(
        max_length=20,
        choices=[
            ('default', 'Default'),
            ('full-width', 'Full Width'),
            ('float-left', 'Float Left'),
            ('float-right', 'Float Right')
        ],
        default='default'
    )
    caption = models.CharField(max_length=255, blank=True, null=True)
    image_sizes = models.JSONField(
        null=True,
        blank=True,
        help_text="Stores URLs for different responsive image sizes in format {width: url}"
    )

    def __str__(self):
        return self.wording or f"Attachment {self.id}"

    class Meta:
        db_table = 'blog_attachment'