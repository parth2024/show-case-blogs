import uuid
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.views import View
from .models import *
from .forms import ArticleForm, ProfileForm, AdminCreationForm, CategoryForm
from django.http import JsonResponse, Http404
from django.db.models import Q, Count
from django.urls import reverse
from django.utils import timezone
import re
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .utils import *
import os
from django.core.paginator import Paginator


class LoginView(View):
    template_name = 'blog/login.html'

    def get(self, request):
        """Display login form"""
        # Redirect to dashboard if already logged in
        if request.session.get('admin_id'):
            return redirect('blog:admin_dashboard')
        return render(request, self.template_name)

    def post(self, request):
        """Handle login form submission"""
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        if not email or not password:
            messages.error(request, 'Please fill in all fields.')
            return render(request, self.template_name)

        try:
            admin = Admin.objects.get(email=email, is_active=True)
            if admin.check_password(password):
                # Set session
                request.session['admin_id'] = admin.id
                request.session['admin_name'] = admin.name
                request.session['admin_email'] = admin.email

                messages.success(request, f'Welcome back, {admin.name}!')
                return redirect('blog:admin_dashboard')
            else:
                messages.error(request, 'Invalid email or password.')
        except Admin.DoesNotExist:
            messages.error(request, 'Invalid email or password.')

        return render(request, self.template_name)


def logout_view(request):
    """Handle admin logout"""
    request.session.flush()
    messages.success(request, 'You have been logged out successfully.')
    return redirect('blog:admin_login')


def admin_required(view_func):
    """Decorator to require admin login"""
    def wrapper(request, *args, **kwargs):
        if not request.session.get('admin_id'):
            messages.error(request, 'Please log in to access the admin panel.')
            return redirect('blog:admin_login')
        return view_func(request, *args, **kwargs)
    return wrapper


@admin_required
def dashboard_view(request):
    """Main dashboard with statistics and article management"""

    # Role-based authorization
    is_authorized_creator = False
    try:
        current_admin = Admin.objects.get(id=request.session.get('admin_id'))
        is_authorized_creator = current_admin.role == 'admin'
    except Admin.DoesNotExist:
        pass

    # Get statistics
    stats = {
        'published_articles': Article.objects.filter(status='published').count(),
        'subscribers': User.objects.filter(is_active=True).count(),
        'total_likes': Like.objects.count(),
        'total_comments': Comment.objects.count(),
        'draft_articles': Article.objects.filter(status='draft').count(),
        'archived_articles': Article.objects.filter(status='archived').count(),
    }

    # Get search query if any
    search_query = request.GET.get('search', '').strip()

    # Get all articles (excluding archived by default) - optimized with select_related
    articles = Article.objects.filter(status__in=['published', 'draft']).select_related('author', 'showcase_image').prefetch_related('categories').order_by('-created_at')

    # Apply search filter if provided
    if search_query:
        articles = articles.filter(
            Q(title__icontains=search_query) |
            Q(summary__icontains=search_query) |
            Q(content__icontains=search_query)
        )

    # Pagination (optional - showing first 20 for now)
    articles = articles[:20]

    # Add public URLs for published articles
    for article in articles:
        if article.status == 'published' and article.slug:
            article.public_url = request.build_absolute_uri(article.get_absolute_url())
        else:
            article.public_url = None

    context = {
        'stats': stats,
        'articles': articles,
        'search_query': search_query,
        'admin_name': request.session.get('admin_name', 'Admin'),
        'is_authorized_creator': is_authorized_creator,
    }

    return render(request, 'blog/admin_dashboard.html', context)


class PublicArticleView(View):
    """Public view for displaying published articles"""
    template_name = 'blog/public_article.html'

    def calculate_reading_time(self, content):
        """Calculate estimated reading time based on content"""
        # Remove HTML tags for word count
        text = re.sub(r'<[^>]+>', '', content)
        words = len(text.split())
        # Average reading speed is about 200 words per minute
        reading_time = max(1, round(words / 200))
        return reading_time

    def get(self, request, slug):
        """Display a published article"""
        try:
            # Only show published articles to public
            article = get_object_or_404(Article, slug=slug, status='published')

            # Increment view count
            article.increment_view_count()

            reading_time = self.calculate_reading_time(article.content)
            processed_content = process_content_for_display(article.content)

            # Get related articles (same author, excluding current) - optimized
            related_articles = Article.objects.filter(
                author=article.author,
                status='published'
            ).select_related('author', 'showcase_image').exclude(id=article.id)[:3]

            # Get approved comments
            comments = article.comments.filter(is_approved=True)

            # Get like count
            like_count = article.likes.count()

            # Check if user has liked this article
            user_has_liked = False
            if request.session.get('user_id'):
                user_has_liked = article.likes.filter(id=request.session['user_id']).exists()

            context = {
                'article': article,
                'processed_content': processed_content,
                'reading_time': reading_time,
                'related_articles': related_articles,
                'comments': comments,
                'like_count': like_count,
                'user_has_liked': user_has_liked,
            }

            return render(request, self.template_name, context)

        except Article.DoesNotExist:
            raise Http404("Article not found or not published")

    def post(self, request, slug):
        """Handle comment submission"""
        article = get_object_or_404(Article, slug=slug, status='published')

        user_name = request.POST.get('name', '').strip()
        user_email = request.POST.get('email', '').strip()
        content = request.POST.get('content', '').strip()

        if not user_name or not user_email or not content:
            messages.error(request, 'Please fill in all fields.')
            return redirect('blog:public_article', slug=slug)

        # Create comment (initially not approved)
        comment = Comment.objects.create(
            article=article,
            user_name=user_name,
            user_email=user_email,
            content=content,
            is_approved=False  # Comments need approval
        )

        messages.success(request, 'Your comment has been submitted and is awaiting approval.')
        return redirect('blog:public_article', slug=slug)


class BlogHomeView(View):
    """Public blog homepage showing published articles"""
    template_name = 'blog/blog_home.html'

    def get(self, request):
        """Display blog homepage with published articles"""
        # Get featured articles - optimized
        featured_articles = Article.objects.filter(
            status='published',
            is_featured=True
        ).select_related('author', 'showcase_image').prefetch_related('categories').order_by('-published_at')[:3]

        # Get recent articles - optimized
        articles = Article.objects.filter(status='published').select_related('author', 'showcase_image').prefetch_related('categories').order_by('-published_at')

        # Get search query if any
        search_query = request.GET.get('search', '').strip()

        if search_query:
            articles = articles.filter(
                Q(title__icontains=search_query) |
                Q(summary__icontains=search_query) |
                Q(content__icontains=search_query)
            )

        # Pagination
        paginator = Paginator(articles, 10)  # Show 10 articles per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'featured_articles': featured_articles,
            'articles': page_obj,
            'search_query': search_query,
        }

        return render(request, self.template_name, context)


@admin_required
def view_article(request, article_id):
    """View article in admin preview mode"""
    try:
        article = Article.objects.get(id=article_id)
        # Calculate reading time (same as in preview)
        text = re.sub(r'<[^>]+>', '', article.content)
        words = len(text.split())
        reading_time = max(1, round(words / 200))

        # Generate public URL if published
        public_url = None
        if article.status == 'published' and article.slug:
            public_url = request.build_absolute_uri(article.get_absolute_url())

        context = {
            'article': article,
            'reading_time': reading_time,
            'public_url': public_url,
            'admin_name': request.session.get('admin_name', 'Admin'),
        }
        return render(request, 'blog/view_article.html', context)

    except Article.DoesNotExist:
        messages.error(request, 'Article not found.')
        return redirect('blog:admin_dashboard')


@method_decorator(admin_required, name='dispatch')
class CreateArticleView(View):
    template_name = 'blog/create_article.html'

    def get(self, request):
        """Display the article creation form"""
        form = ArticleForm()
        categories = Category.objects.all().order_by('name')
        can_manage_categories = False
        try:
            current_admin = Admin.objects.get(id=request.session.get('admin_id'))
            can_manage_categories = current_admin.role == 'admin'
        except Admin.DoesNotExist:
            pass
        context = {
            'form': form,
            'admin_name': request.session.get('admin_name', 'Admin'),
            'categories': categories,
            'can_manage_categories': can_manage_categories,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle article creation"""
        form = ArticleForm(request.POST)
        showcase_image_id = request.POST.get('showcase_image')
        
        try:
            admin_id = request.session.get('admin_id')
            author = Admin.objects.get(id=admin_id)

            # Optionally create a new category (admins only)
            new_category_name = request.POST.get('new_category', '').strip()
            if new_category_name and author.role == 'admin':
                Category.objects.get_or_create(name=new_category_name)

            if form.is_valid():
                article = form.save(commit=False)
                article.author = author

                # Set showcase image if provided
                if showcase_image_id:
                    try:
                        showcase_image = Attachment.objects.get(id=showcase_image_id)
                        article.showcase_image = showcase_image
                    except Attachment.DoesNotExist:
                        pass

                # Set published_at if status is published
                if article.status == 'published':
                    article.published_at = timezone.now()

                article.save()
                form.save_m2m()  # Save many-to-many relationships (categories)

                if article.status == 'published':
                    messages.success(request, f'Article "{article.title}" published successfully.')
                else:
                    messages.success(request, f'Article "{article.title}" saved as draft.')

                return redirect('blog:admin_dashboard')
            else:
                messages.error(request, 'Please correct the errors in the form.')

        except Admin.DoesNotExist:
            messages.error(request, 'Author not found. Please log in again.')
            return redirect('blog:admin_login')
        except Exception as e:
            messages.error(request, f'An error occurred: {e}')
        
        # Re-render form with errors
        categories = Category.objects.all().order_by('name')
        can_manage_categories = False
        try:
            current_admin = Admin.objects.get(id=request.session.get('admin_id'))
            can_manage_categories = current_admin.role == 'admin'
        except Admin.DoesNotExist:
            pass
        
        context = {
            'form': form,
            'admin_name': request.session.get('admin_name', 'Admin'),
            'categories': categories,
            'can_manage_categories': can_manage_categories,
        }
        return render(request, self.template_name, context)


@method_decorator(admin_required, name='dispatch')
class PreviewArticleView(View):
    template_name = 'blog/article_preview.html'

    def calculate_reading_time(self, content):
        """Calculate estimated reading time based on content"""
        # Remove HTML tags for word count
        text = re.sub(r'<[^>]+>', '', content)
        words = len(text.split())
        # Average reading speed is about 200 words per minute
        reading_time = max(1, round(words / 200))
        return reading_time

    def post(self, request):
        """Handle article preview"""
        title = request.POST.get('title', '').strip()
        summary = request.POST.get('summary', '').strip()
        content = request.POST.get('content', '').strip()
        showcase_image_id = request.POST.get('showcase_image')
        processed_content = process_content_for_display(content)

        if not title or not content:
            messages.error(request, 'Title and content are required to preview the article.')
            return redirect('blog:create_article')

        try:
            admin_id = request.session.get('admin_id')
            author = Admin.objects.get(id=admin_id)

            # Get showcase image if provided
            showcase_image = None
            if showcase_image_id:
                try:
                    showcase_image = Attachment.objects.get(id=showcase_image_id)
                except Attachment.DoesNotExist:
                    pass

            # Create a temporary article object for preview (not saved to database)
            article_preview = {
                'title': title,
                'summary': summary,
                'content': processed_content,  # Use the processed content
                'author': author,
                'showcase_image': showcase_image,
                'created_at': timezone.now()
            }

            reading_time = self.calculate_reading_time(content)

            context = {
                'article': article_preview,
                'reading_time': reading_time,
                'admin_name': request.session.get('admin_name', 'Admin'),
            }

            return render(request, self.template_name, context)

        except Admin.DoesNotExist:
            messages.error(request, 'Author not found. Please log in again.')
            return redirect('blog:admin_login')
        except Exception as e:
            messages.error(request, f'An error occurred while generating preview: {e}')
            return redirect('blog:create_article')


@admin_required
def search_articles_ajax(request):
    """AJAX endpoint for quick article search"""
    query = request.GET.get('q', '').strip()

    if len(query) < 2:  # Minimum 2 characters for search
        return JsonResponse({'articles': []})

    articles = Article.objects.filter(
        Q(title__icontains=query) |
        Q(summary__icontains=query),
        status__in=['published', 'draft']
    ).values('id', 'title', 'status', 'created_at')[:10]

    articles_list = []
    for article in articles:
        articles_list.append({
            'id': article['id'],
            'title': article['title'],
            'status': article['status'],
            'created_at': article['created_at'].strftime('%Y-%m-%d') if article['created_at'] else '',
        })

    return JsonResponse({'articles': articles_list})


@admin_required
def archive_article(request, article_id):
    """Archive an article"""
    try:
        article = Article.objects.get(id=article_id)
        article.status = 'archived'
        article.save()
        messages.success(request, f'Article "{article.title}" has been archived.')
    except Article.DoesNotExist:
        messages.error(request, 'Article not found.')

    return redirect('blog:admin_dashboard')


@admin_required
def delete_article(request, article_id):
    """Delete an article permanently"""
    try:
        article = Article.objects.get(id=article_id)
        title = article.title
        article.delete()
        messages.success(request, f'Article "{title}" has been deleted permanently.')
    except Article.DoesNotExist:
        messages.error(request, 'Article not found.')

    return redirect('blog:admin_dashboard')


@admin_required
def toggle_article_status(request, article_id):
    """Toggle between draft and published status"""
    try:
        article = Article.objects.get(id=article_id)
        if article.status == 'draft':
            article.status = 'published'
            if not article.published_at:
                article.published_at = timezone.now()
            messages.success(request, f'Article "{article.title}" has been published.')
        elif article.status == 'published':
            article.status = 'draft'
            messages.success(request, f'Article "{article.title}" has been moved to draft.')

        article.save()
    except Article.DoesNotExist:
        messages.error(request, 'Article not found.')

    return redirect('blog:admin_dashboard')


@method_decorator(admin_required, name='dispatch')
class ProfileView(View):
    template_name = 'blog/profile.html'

    def get(self, request):
        """Display the profile form with the current admin's data."""
        try:
            admin = Admin.objects.get(id=request.session.get('admin_id'))
            form = ProfileForm(instance=admin)
            context = {
                'form': form,
                'admin': admin,
                'admin_name': admin.name
            }
            return render(request, self.template_name, context)
        except Admin.DoesNotExist:
            messages.error(request, 'Admin profile not found. Please log in again.')
            return redirect('blog:admin_login')

    def post(self, request):
        """Handle profile update form submission."""
        try:
            admin = Admin.objects.get(id=request.session.get('admin_id'))
            form = ProfileForm(request.POST, instance=admin)

            if form.is_valid():
                # Check if email is being changed and if it's unique
                new_email = form.cleaned_data.get('email')
                if new_email != admin.email:
                    if Admin.objects.filter(email=new_email).exclude(id=admin.id).exists():
                        messages.error(request, 'This email address is already in use by another account.')
                        return redirect('blog:admin_profile')

                # Handle password change
                current_password = form.cleaned_data.get('current_password')
                new_password = form.cleaned_data.get('new_password')
                
                if new_password:
                    if not current_password:
                        messages.error(request, 'Current password is required to set a new password.')
                        return redirect('blog:admin_profile')
                    
                    if not admin.check_password(current_password):
                        messages.error(request, 'Your current password is not correct.')
                        return redirect('blog:admin_profile')
                    
                    admin.set_password(new_password)
                    messages.success(request, 'Password updated successfully.')

                # Save form data
                admin = form.save()

                # Update session variables
                request.session['admin_name'] = admin.name
                request.session['admin_email'] = admin.email

                messages.success(request, 'Profile updated successfully.')
                return redirect('blog:admin_profile')
            else:
                messages.error(request, 'Please correct the errors in the form.')
                context = {
                    'form': form,
                    'admin': admin,
                    'admin_name': admin.name
                }
                return render(request, self.template_name, context)

        except Admin.DoesNotExist:
            messages.error(request, 'Admin profile not found. Please log in again.')
            return redirect('blog:admin_login')


@admin_required
def archived_articles_view(request):
    """Display a list of archived articles with search functionality."""
    # Get search query if any
    search_query = request.GET.get('search', '').strip()

    # Role-based authorization
    is_authorized_creator = False
    try:
        current_admin = Admin.objects.get(id=request.session.get('admin_id'))
        is_authorized_creator = current_admin.role == 'admin'
    except Admin.DoesNotExist:
        pass

    # Get all archived articles - optimized
    articles = Article.objects.filter(status='archived').select_related('author', 'showcase_image').prefetch_related('categories').order_by('-updated_at')

    # Apply search filter if provided
    if search_query:
        articles = articles.filter(
            Q(title__icontains=search_query) |
            Q(summary__icontains=search_query) |
            Q(content__icontains=search_query)
        )

    context = {
        'articles': articles,
        'search_query': search_query,
        'admin_name': request.session.get('admin_name', 'Admin'),
        'is_authorized_creator': is_authorized_creator,
    }

    return render(request, 'blog/archived_articles.html', context)


@admin_required
def restore_article(request, article_id):
    """Restore an archived article by setting its status to 'draft'."""
    try:
        article = Article.objects.get(id=article_id, status='archived')
        article.status = 'draft'
        article.save()
        messages.success(request, f'Article "{article.title}" has been restored to drafts.')
    except Article.DoesNotExist:
        messages.error(request, 'Article not found or is not archived.')

    return redirect('blog:admin_archived')


@method_decorator(admin_required, name='dispatch')
class CreateAdminView(View):
    template_name = 'blog/create_admin.html'

    def dispatch(self, request, *args, **kwargs):
        """Restrict access to admins only."""
        try:
            current_admin = Admin.objects.get(id=request.session.get('admin_id'))
            if current_admin.role != 'admin':
                messages.error(request, 'You do not have permission to create new admin users.')
                return redirect('blog:admin_dashboard')
        except Admin.DoesNotExist:
            messages.error(request, 'Please log in again.')
            return redirect('blog:admin_login')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        """Display the form to create a new admin."""
        form = AdminCreationForm()
        context = {
            'form': form,
            'admin_name': request.session.get('admin_name')
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle the creation of a new admin user."""
        form = AdminCreationForm(request.POST)

        if form.is_valid():
            # Check if email already exists
            email = form.cleaned_data.get('email')
            if Admin.objects.filter(email=email).exists():
                messages.error(request, f'An admin with the email "{email}" already exists.')
                context = {
                    'form': form,
                    'admin_name': request.session.get('admin_name')
                }
                return render(request, self.template_name, context)

            # Save the new admin (form handles password hashing)
            new_admin = form.save()

            role_label = 'Administrator' if new_admin.role == 'admin' else 'Editor'
            messages.success(request, f'Successfully created new {role_label}: {new_admin.name}.')
            return redirect('blog:admin_dashboard')
        else:
            messages.error(request, 'Please correct the errors in the form.')
            context = {
                'form': form,
                'admin_name': request.session.get('admin_name')
            }
            return render(request, self.template_name, context)


@admin_required
def edit_article(request, article_id):
    """Edit an existing article"""
    try:
        article = Article.objects.get(id=article_id)
    except Article.DoesNotExist:
        messages.error(request, 'Article not found.')
        return redirect('blog:admin_dashboard')

    # Role-based authorization
    is_authorized = False
    is_authorized_creator = False
    try:
        current_admin = Admin.objects.get(id=request.session.get('admin_id'))
        is_authorized = current_admin.role == 'admin'
        is_authorized_creator = is_authorized
    except Admin.DoesNotExist:
        pass

    # Only allow author or admins to edit
    if article.author and article.author.id != request.session.get('admin_id') and not is_authorized:
        messages.error(request, 'You are not authorized to edit this article.')
        return redirect('blog:admin_dashboard')

    if request.method == 'POST':
        # Create form with POST data and instance
        form = ArticleForm(request.POST, instance=article)
        
        # Handle form submission
        showcase_image_id = request.POST.get('showcase_image')

        # Optionally create a new category (admins only)
        new_category_name = request.POST.get('new_category', '').strip()
        if new_category_name and is_authorized:
            Category.objects.get_or_create(name=new_category_name)

        if form.is_valid():
            article = form.save(commit=False)
            
            # Handle showcase image
            if showcase_image_id:
                try:
                    showcase_image = Attachment.objects.get(id=showcase_image_id)
                    article.showcase_image = showcase_image
                except Attachment.DoesNotExist:
                    article.showcase_image = None
            else:
                article.showcase_image = None

            # Only set published_at if transitioning to published
            if article.status == 'published' and not article.published_at:
                article.published_at = timezone.now()

            # Clear published_at if reverting to draft
            if article.status == 'draft' and article.published_at:
                article.published_at = None

            article.save()
            form.save_m2m()  # Save many-to-many relationships (categories)

            messages.success(request, f'Article "{article.title}" updated successfully.')
            return redirect('blog:view_article', article_id=article.id)
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        # Create form with article instance for GET request
        form = ArticleForm(instance=article)

    context = {
        'form': form,
        'article': article,
        'admin_name': request.session.get('admin_name', 'Admin'),
        'is_authorized_creator': is_authorized_creator,
        'categories': Category.objects.all().order_by('name'),
    }
    return render(request, 'blog/edit_article.html', context)


@admin_required
@csrf_protect
def upload_image_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method.'}, status=405)

    # Handle both CKEditor 'upload' and custom 'images' field
    files = request.FILES.getlist('images') or [request.FILES.get('upload')]
    files = [f for f in files if f]  # Filter out None values
    
    if not files:
        return JsonResponse({'error': 'No image files found in request.'}, status=400)

    # --- Configuration ---
    ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
    MAX_SIZE_MB = 10
    SIZES_TO_GENERATE = [400, 800, 1200, 1600] # Widths in pixels for responsive versions

    media_root = settings.MEDIA_ROOT
    media_url = settings.MEDIA_URL
    upload_dir = os.path.join(media_root, 'uploads', timezone.now().strftime('%Y/%m'))
    os.makedirs(upload_dir, exist_ok=True)

    response_images = []

    for image_file in files:
        # --- Validation ---
        if image_file.content_type not in ALLOWED_TYPES:
            continue # Silently skip invalid file types
        if image_file.size > MAX_SIZE_MB * 1024 * 1024:
            continue # Silently skip files that are too large

        # --- File Naming ---
        original_filename, extension = os.path.splitext(image_file.name)
        unique_id = uuid.uuid4().hex[:8]
        base_filename = f"{slugify(original_filename)}-{unique_id}"

        # --- Save Original File ---
        original_file_path = os.path.join(upload_dir, f"{base_filename}{extension}")
        with open(original_file_path, 'wb+') as f:
            for chunk in image_file.chunks():
                f.write(chunk)

        # --- Generate Responsive Versions ---
        image_versions = create_responsive_images(image_file, upload_dir, media_url)
        with open(original_file_path, 'rb') as saved_image_file:
            for size in SIZES_TO_GENERATE:
                resized_content = resize_image(saved_image_file, size)
                if resized_content:
                    file_path = os.path.join(upload_dir, resized_content.name)
                    with open(file_path, 'wb+') as f:
                        f.write(resized_content.read())

                    rel_path = os.path.relpath(file_path, media_root)
                    url = os.path.join(media_url, rel_path).replace("\\", "/")
                    image_versions[f"{size}w"] = url

        # --- Create Database Record ---
        main_rel_path = os.path.relpath(original_file_path, media_root)
        main_image_url = os.path.join(media_url, main_rel_path).replace("\\", "/")

        attachment = Attachment.objects.create(
            wording=original_filename,
            link=main_image_url,
            caption=original_filename,
            file_path=original_file_path,
            attachment_type='image',
            image_sizes=image_versions,
            article=None
        )

        # --- Prepare data for JSON response ---
        response_images.append({
            'url': main_image_url, # The URL to insert into the editor
            'id': attachment.id,
            'sizes': image_versions # Pass sizes to JS as a bonus
        })

    # Return format compatible with both CKEditor and custom uploads
    if len(response_images) == 1 and request.FILES.get('upload'):
        # CKEditor single upload format
        return JsonResponse({'url': response_images[0]['url']})
    else:
        # Multiple images format
        return JsonResponse({'images': response_images})


def associate_attachments_with_article(article, content):
    """Associate unattached images with an article after it's saved."""
    soup = BeautifulSoup(content, 'html.parser')
    image_urls = [img['src'] for img in soup.find_all('img') if img.get('src')]

    for url in image_urls:
        Attachment.objects.filter(link=url, article__isnull=True).update(article=article)


# ===========================
# Category Management Views
# ===========================

@admin_required
def manage_categories(request):
    """View and manage all categories (admin only)"""
    try:
        current_admin = Admin.objects.get(id=request.session.get('admin_id'))
        if current_admin.role != 'admin':
            messages.error(request, 'Only admins can manage categories.')
            return redirect('blog:admin_dashboard')
    except Admin.DoesNotExist:
        messages.error(request, 'Admin not found.')
        return redirect('blog:admin_login')

    categories = Category.objects.annotate(article_count=Count('articles')).order_by('name')
    form = CategoryForm()

    context = {
        'categories': categories,
        'form': form,
        'admin_name': request.session.get('admin_name', 'Admin'),
    }
    return render(request, 'blog/manage_categories.html', context)


@admin_required
def create_category(request):
    """Create a new category (admin only)"""
    try:
        current_admin = Admin.objects.get(id=request.session.get('admin_id'))
        if current_admin.role != 'admin':
            messages.error(request, 'Only admins can create categories.')
            return redirect('blog:admin_dashboard')
    except Admin.DoesNotExist:
        messages.error(request, 'Admin not found.')
        return redirect('blog:admin_login')

    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" created successfully.')
            return redirect('blog:manage_categories')
        else:
            messages.error(request, 'Please correct the errors in the form.')
    
    return redirect('blog:manage_categories')


@admin_required
def edit_category(request, category_id):
    """Edit an existing category (admin only)"""
    try:
        current_admin = Admin.objects.get(id=request.session.get('admin_id'))
        if current_admin.role != 'admin':
            messages.error(request, 'Only admins can edit categories.')
            return redirect('blog:admin_dashboard')
    except Admin.DoesNotExist:
        messages.error(request, 'Admin not found.')
        return redirect('blog:admin_login')

    try:
        category = Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        messages.error(request, 'Category not found.')
        return redirect('blog:manage_categories')

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" updated successfully.')
            return redirect('blog:manage_categories')
        else:
            messages.error(request, 'Please correct the errors in the form.')
    
    return redirect('blog:manage_categories')


@admin_required
def delete_category(request, category_id):
    """Delete a category (admin only)"""
    try:
        current_admin = Admin.objects.get(id=request.session.get('admin_id'))
        if current_admin.role != 'admin':
            messages.error(request, 'Only admins can delete categories.')
            return redirect('blog:admin_dashboard')
    except Admin.DoesNotExist:
        messages.error(request, 'Admin not found.')
        return redirect('blog:admin_login')

    try:
        category = Category.objects.get(id=category_id)
        category_name = category.name
        article_count = category.articles.count()
        
        if article_count > 0:
            messages.warning(request, f'Category "{category_name}" is used by {article_count} article(s). It has been removed from those articles.')
        
        category.delete()
        messages.success(request, f'Category "{category_name}" deleted successfully.')
    except Category.DoesNotExist:
        messages.error(request, 'Category not found.')
    
    return redirect('blog:manage_categories')


# ===========================
# Comment Management Views
# ===========================

@admin_required
def manage_comments(request):
    """View and manage all comments"""
    # Get filter parameters
    status_filter = request.GET.get('status', 'all')  # all, pending, approved
    search_query = request.GET.get('search', '').strip()

    # Base queryset with optimizations
    comments = Comment.objects.select_related('article', 'article__author').order_by('-created_at')

    # Apply filters
    if status_filter == 'pending':
        comments = comments.filter(is_approved=False)
    elif status_filter == 'approved':
        comments = comments.filter(is_approved=True)

    # Apply search
    if search_query:
        comments = comments.filter(
            Q(user_name__icontains=search_query) |
            Q(user_email__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(article__title__icontains=search_query)
        )

    # Get statistics
    stats = {
        'total_comments': Comment.objects.count(),
        'pending_comments': Comment.objects.filter(is_approved=False).count(),
        'approved_comments': Comment.objects.filter(is_approved=True).count(),
    }

    # Pagination
    paginator = Paginator(comments, 20)  # 20 comments per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'comments': page_obj,
        'stats': stats,
        'status_filter': status_filter,
        'search_query': search_query,
        'admin_name': request.session.get('admin_name', 'Admin'),
    }
    return render(request, 'blog/manage_comments.html', context)


@admin_required
def approve_comment(request, comment_id):
    """Approve a comment"""
    if request.method == 'POST':
        try:
            comment = Comment.objects.get(id=comment_id)
            comment.is_approved = True
            comment.save()
            messages.success(request, f'Comment by {comment.user_name} approved successfully.')
        except Comment.DoesNotExist:
            messages.error(request, 'Comment not found.')
    
    return redirect('blog:manage_comments')


@admin_required
def reject_comment(request, comment_id):
    """Reject (unapprove) a comment"""
    if request.method == 'POST':
        try:
            comment = Comment.objects.get(id=comment_id)
            comment.is_approved = False
            comment.save()
            messages.success(request, f'Comment by {comment.user_name} rejected.')
        except Comment.DoesNotExist:
            messages.error(request, 'Comment not found.')
    
    return redirect('blog:manage_comments')


@admin_required
def delete_comment(request, comment_id):
    """Delete a comment permanently"""
    if request.method == 'POST':
        try:
            comment = Comment.objects.get(id=comment_id)
            user_name = comment.user_name
            comment.delete()
            messages.success(request, f'Comment by {user_name} deleted successfully.')
        except Comment.DoesNotExist:
            messages.error(request, 'Comment not found.')
    
    return redirect('blog:manage_comments')


@csrf_protect
def subscribe_newsletter(request):
    """Handle newsletter subscription"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()

        if not name or not email:
            messages.error(request, 'Please provide both name and email.')
            return redirect('blog:blog_home')

        # Check if already subscribed
        if User.objects.filter(email=email).exists():
            messages.info(request, 'You are already subscribed to our newsletter.')
            return redirect('blog:blog_home')

        # Create new subscriber
        User.objects.create(name=name, email=email)
        messages.success(request, 'Thank you for subscribing to our newsletter!')

        return redirect('blog:blog_home')

    return redirect('blog:blog_home')


@csrf_protect
def like_article(request, article_id):
    """Handle article likes"""
    if request.method == 'POST':
        try:
            article = Article.objects.get(id=article_id, status='published')

            # Check if user is logged in (using session)
            if not request.session.get('user_id'):
                # Create anonymous user
                user = User.objects.create(
                    name='Anonymous',
                    email=f'anonymous_{uuid.uuid4().hex[:8]}@example.com'
                )
                request.session['user_id'] = user.id
            else:
                user = User.objects.get(id=request.session['user_id'])

            # Check if already liked
            if Like.objects.filter(article=article, user=user).exists():
                messages.info(request, 'You have already liked this article.')
                return redirect('blog:public_article', slug=article.slug)

            # Create like
            Like.objects.create(article=article, user=user)
            messages.success(request, 'Thank you for liking this article!')

            return redirect('blog:public_article', slug=article.slug)

        except Article.DoesNotExist:
            messages.error(request, 'Article not found.')
            return redirect('blog:blog_home')

    return redirect('blog:blog_home')


def load_more_articles(request):
    """AJAX endpoint to load more articles"""
    if request.method == 'GET':
        page = request.GET.get('page', 1)
        articles = Article.objects.filter(status='published').select_related('author', 'showcase_image').prefetch_related('categories', 'likes', 'comments').order_by('-published_at')

        paginator = Paginator(articles, 10)  # 10 articles per page
        try:
            articles_page = paginator.page(page)
        except EmptyPage:
            return JsonResponse({'articles': [], 'has_next': False})

        # Serialize articles
        articles_data = []
        for article in articles_page:
            articles_data.append({
                'id': article.id,
                'title': article.title,
                'summary': article.summary,
                'slug': article.slug,
                'published_at': article.published_at.strftime('%B %d, %Y') if article.published_at else '',
                'author_name': article.author.name if article.author else '',
                'showcase_image': article.showcase_image.link if article.showcase_image else '',
                'like_count': article.likes.count(),
                'comment_count': article.comments.filter(is_approved=True).count(),
            })

        return JsonResponse({
            'articles': articles_data,
            'has_next': articles_page.has_next()
        })

    return JsonResponse({'error': 'Invalid request'}, status=400)