import uuid

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.contrib.sessions.models import Session
from django.utils.decorators import method_decorator
from django.views import View
from .models import *
from django.http import JsonResponse, Http404
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
import re
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .utils import *
import os


class LoginView(View):
    template_name = 'blog/login.html'

    def get(self, request):
        """Display login form"""
        # Redirect to dashboard if already logged in
        if request.session.get('admin_id'):
            return redirect('admin_dashboard')
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
                return redirect('admin_dashboard')
            else:
                messages.error(request, 'Invalid email or password.')
        except Admin.DoesNotExist:
            messages.error(request, 'Invalid email or password.')

        return render(request, self.template_name)


def logout_view(request):
    """Handle admin logout"""
    request.session.flush()
    messages.success(request, 'You have been logged out successfully.')
    return redirect('admin_login')


def admin_required(view_func):
    """Decorator to require admin login"""
    def wrapper(request, *args, **kwargs):
        if not request.session.get('admin_id'):
            messages.error(request, 'Please log in to access the admin panel.')
            return redirect('admin_login')
        return view_func(request, *args, **kwargs)
    return wrapper


@admin_required
def dashboard_view(request):
    """Main dashboard with statistics and article management"""

    authorized_admins = ['Franck Yoteu', 'Arsene Minkam', 'Liboire Minkam', 'Yoteu Rovani']
    is_authorized_creator = request.session.get('admin_name') in authorized_admins

    print(f"Authorized creator: {is_authorized_creator}")
    
    # Get statistics
    stats = {
        'published_articles': Article.objects.filter(status='published').count(),
        'subscribers': User.objects.count(),
        # For now, we'll use a placeholder for average rating since we don't have ratings yet
        'average_rating': 4.2,  # This will be calculated from actual ratings later
        'draft_articles': Article.objects.filter(status='draft').count(),
        'archived_articles': Article.objects.filter(status='archived').count(),
    }
    
    # Get search query if any
    search_query = request.GET.get('search', '').strip()
    
    # Get all articles (excluding archived by default)
    articles = Article.objects.filter(status__in=['published', 'draft']).order_by('-created_at')
    
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
            
            reading_time = self.calculate_reading_time(article.content)
            processed_content = process_content_for_display(article.content)
            # Get related articles (same author, excluding current)
            related_articles = Article.objects.filter(
                author=article.author,
                status='published'
            ).exclude(id=article.id)[:3]
            
            context = {
                'article': article,
                'processed_content': processed_content,
                'reading_time': reading_time,
                'related_articles': related_articles,
            }
            
            return render(request, self.template_name, context)
            
        except Article.DoesNotExist:
            raise Http404("Article not found or not published")


class BlogHomeView(View):
    """Public blog homepage showing published articles"""
    template_name = 'blog/blog_home.html'

    def get(self, request):
        """Display blog homepage with published articles"""
        # Get featured articles
        featured_articles = Article.objects.filter(
            status='published',
            islike=True
        ).order_by('-published_at')[:3]
        
        # Get recent articles
        recent_articles = Article.objects.filter(
            status='published'
        ).order_by('-published_at')[:6]
        
        # Get search query if any
        search_query = request.GET.get('search', '').strip()
        articles = Article.objects.filter(status='published').order_by('-published_at')
        
        if search_query:
            articles = articles.filter(
                Q(title__icontains=search_query) |
                Q(summary__icontains=search_query) |
                Q(content__icontains=search_query)
            )
        
        # Pagination (show 10 per page)
        articles = articles[:10]
        
        context = {
            'featured_articles': featured_articles,
            'recent_articles': recent_articles,
            'articles': articles,
            'search_query': search_query,
        }
        
        return render(request, self.template_name, context)


# Update existing admin view_article to show public URL
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
        return redirect('admin_dashboard')


@method_decorator(admin_required, name='dispatch')
class CreateArticleView(View):
    template_name = 'blog/create_article.html'

    def get(self, request):
        """Display the article creation form"""
        context = {
            'admin_name': request.session.get('admin_name', 'Admin'),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle article creation"""
        title = request.POST.get('title', '').strip()
        summary = request.POST.get('summary', '').strip()
        content = request.POST.get('content', '').strip()
        content_json = request.POST.get('content_json')
        status = request.POST.get('status', 'draft')

        if not title or not content:
            messages.error(request, 'Title and content are required.')
            context = {
                'admin_name': request.session.get('admin_name', 'Admin'),
                'title': title,
                'summary': summary,
                'content': content,
                'status': status
            }
            return render(request, self.template_name, context)

        try:
            admin_id = request.session.get('admin_id')
            author = Admin.objects.get(id=admin_id)
            article = Article(
                title=title,
                summary=summary,
                content=content,
                content_json=content_json,
                status=status,
                author=author
            )
            if status == 'published':
                article.published_at = timezone.now()
            article.save()
            # Associate images
            associate_attachments_with_article(article, content)

            if status == 'published':
                messages.success(request, f'Article "{title}" published successfully.')
            else:
                messages.success(request, f'Article "{title}" saved as draft.')
            
            return redirect('admin_dashboard')

        except Admin.DoesNotExist:
            messages.error(request, 'Author not found. Please log in again.')
            return redirect('admin_login')
        except Exception as e:
            messages.error(request, f'An error occurred: {e}')
            context = {
                'admin_name': request.session.get('admin_name', 'Admin'),
                'title': title,
                'summary': summary,
                'content': content,
                'status': status
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
        processed_content = process_content_for_display(content)

        if not title or not content:
            messages.error(request, 'Title and content are required to preview the article.')
            return redirect('create_article')

        try:
            admin_id = request.session.get('admin_id')
            author = Admin.objects.get(id=admin_id)
            
            # Create a temporary article object for preview (not saved to database)
            article = Article(
                title=title,
                summary=summary,
                content=content,
                author=author,
                created_at=timezone.now()
            )
            article_preview = {
                'title': request.POST.get('title'),
                'summary': request.POST.get('summary'),
                'content': processed_content, # Use the processed content
                'author': Admin.objects.get(id=request.session.get('admin_id')),
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
            return redirect('admin_login')
        except Exception as e:
            messages.error(request, f'An error occurred while generating preview: {e}')
            return redirect('create_article')


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
    
    return redirect('admin_dashboard')


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
    
    return redirect('admin_dashboard')


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
    
    return redirect('admin_dashboard')


@method_decorator(admin_required, name='dispatch')
class ProfileView(View):
    template_name = 'blog/profile.html'

    def get(self, request):
        """Display the profile form with the current admin's data."""
        try:
            admin = Admin.objects.get(id=request.session.get('admin_id'))
            context = {
                'admin': admin,
                'admin_name': admin.name
            }
            return render(request, self.template_name, context)
        except Admin.DoesNotExist:
            messages.error(request, 'Admin profile not found. Please log in again.')
            return redirect('admin_login')

    def post(self, request):
        """Handle profile update form submission."""
        try:
            admin = Admin.objects.get(id=request.session.get('admin_id'))
            
            # Get form data
            name = request.POST.get('name', '').strip()
            email = request.POST.get('email', '').strip()
            
            # Password fields
            current_password = request.POST.get('current_password', '')
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')
            
            # Basic validation
            if not name or not email:
                messages.error(request, 'Name and email fields cannot be empty.')
                return redirect('admin_profile')

            # Update name and email
            admin.name = name
            
            # Check if email is being changed and if it's unique
            if email != admin.email:
                if Admin.objects.filter(email=email).exclude(id=admin.id).exists():
                    messages.error(request, 'This email address is already in use by another account.')
                    return redirect('admin_profile')
                admin.email = email

            # Handle password change
            if current_password and new_password and confirm_password:
                if not admin.check_password(current_password):
                    messages.error(request, 'Your current password is not correct.')
                    return redirect('admin_profile')
                
                if new_password != confirm_password:
                    messages.error(request, 'The new passwords do not match.')
                    return redirect('admin_profile')
                
                admin.set_password(new_password)
                messages.success(request, 'Password updated successfully.')
            
            admin.save()
            
            # Update session variables
            request.session['admin_name'] = admin.name
            request.session['admin_email'] = admin.email
            
            messages.success(request, 'Profile updated successfully.')
            return redirect('admin_profile')

        except Admin.DoesNotExist:
            messages.error(request, 'Admin profile not found. Please log in again.')
            return redirect('admin_login')
        

@admin_required
def archived_articles_view(request):
    """Display a list of archived articles with search functionality."""
    # Get search query if any
    search_query = request.GET.get('search', '').strip()

    authorized_admins = ['Franck Yoteu', 'Arsene Minkam', 'Liboire Minkam', 'Yoteu Rovani']
    is_authorized_creator = request.session.get('admin_name') in authorized_admins
    
    # Get all archived articles
    articles = Article.objects.filter(status='archived').order_by('-updated_at')
    
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
    
    return redirect('admin_archived')


@method_decorator(admin_required, name='dispatch')
class CreateAdminView(View):
    template_name = 'blog/create_admin.html'
    authorized_admins = ['Franck Yoteu', 'Arsene Minkam', 'Liboire Minkam', 'Yoteu Rovani']

    def dispatch(self, request, *args, **kwargs):
        """
        Overrides the default dispatch method to check for authorization
        before the GET or POST methods are called.
        """
        admin_name = request.session.get('admin_name')
        if admin_name not in self.authorized_admins:
            messages.error(request, 'You do not have permission to create new admin users.')
            return redirect('admin_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        """Display the form to create a new admin."""
        context = {'admin_name': request.session.get('admin_name')}
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle the creation of a new admin user."""
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        if not name or not email or not password:
            messages.error(request, 'Please fill in all fields.')
            return render(request, self.template_name, {'admin_name': request.session.get('admin_name')})

        if Admin.objects.filter(email=email).exists():
            messages.error(request, f'An admin with the email "{email}" already exists.')
            return render(request, self.template_name, {'admin_name': request.session.get('admin_name')})

        # Create the new admin
        new_admin = Admin(name=name, email=email)
        new_admin.set_password(password)
        new_admin.save()

        messages.success(request, f'Successfully created new admin: {name}.')
        return redirect('admin_dashboard')


@admin_required
def edit_article(request, article_id):
    """Edit an existing article"""
    try:
        article = Article.objects.get(id=article_id)
        authorized_admins = ['Franck Yoteu', 'Arsene Minkam', 'Liboire Minkam', 'Yoteu Rovani']
        is_authorized = request.session.get('admin_name') in authorized_admins
        is_authorized_creator = request.session.get('admin_name') in authorized_admins

        # Only allow author or authorized admins to edit
        if article.author.id != request.session.get('admin_id') and not is_authorized:
            messages.error(request, 'You are not authorized to edit this article.')
            return redirect('admin_dashboard')

        if request.method == 'POST':
            # Handle form submission
            title = request.POST.get('title', '').strip()
            summary = request.POST.get('summary', '').strip()
            content = request.POST.get('content', '').strip()
            content_json = request.POST.get('content_json', '')
            status = request.POST.get('status', 'draft')

            if not title or not content:
                messages.error(request, 'Title and content are required.')
            else:
                article.title = title
                article.summary = summary
                article.content = content
                article.content_json = content_json
                article.status = status

                # Only set published_at if transitioning to published
                if status == 'published' and not article.published_at:
                    article.published_at = timezone.now()

                # Clear published_at if reverting to draft
                if status == 'draft' and article.published_at:
                    article.published_at = None

                article.save()
                # Associate images
                associate_attachments_with_article(article, content)
                messages.success(request, f'Article "{title}" updated successfully.')
                return redirect('view_article', article_id=article.id)

        context = {
            'article': article,
            'admin_name': request.session.get('admin_name', 'Admin'),
            'is_authorized_creator': is_authorized_creator,
        }
        return render(request, 'blog/edit_article.html', context)

    except Article.DoesNotExist:
        messages.error(request, 'Article not found.')
        return redirect('admin_dashboard')




@admin_required
@csrf_protect
def upload_image_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method.'}, status=405)

    files = request.FILES.getlist('images')
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
        image_versions = create_responsive_images(image_file)
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

    return JsonResponse({'images': response_images})

def associate_attachments_with_article(article, content):
    """Associate unattached images with an article after it's saved."""
    soup = BeautifulSoup(content, 'html.parser')
    image_urls = [img['src'] for img in soup.find_all('img') if img.get('src')]

    for url in image_urls:
        Attachment.objects.filter(link=url, article__isnull=True).update(article=article)