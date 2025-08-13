from django.core.management.base import BaseCommand
from django.db import transaction
from blog.models import Article
import re
from PIL import Image
import requests
from io import BytesIO


class Command(BaseCommand):
    help = 'Migrate existing articles to use enhanced styling system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run the command without making changes to see what would be updated',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit the number of articles to process',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']

        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )

        # Get articles to process
        articles = Article.objects.all()
        if limit:
            articles = articles[:limit]

        total_articles = articles.count()
        self.stdout.write(f'Processing {total_articles} articles...')

        updated_count = 0
        with transaction.atomic():
            for i, article in enumerate(articles, 1):
                self.stdout.write(f'Processing article {i}/{total_articles}: {article.title}')
                
                original_content = article.content
                updated_content = self.enhance_article_content(original_content)
                
                if original_content != updated_content:
                    if not dry_run:
                        article.content = updated_content
                        article.save(update_fields=['content'])
                    
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Updated: {article.title}')
                    )
                else:
                    self.stdout.write(f'  - No changes needed: {article.title}')

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would update {updated_count} articles')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully updated {updated_count} articles')
            )

    def enhance_article_content(self, content):
        """
        Enhance existing article content with new styling classes
        """
        if not content:
            return content

        # 1. Wrap images in containers and classify them
        content = self.wrap_and_classify_images(content)
        
        # 2. Enhance blockquotes
        content = self.enhance_blockquotes(content)
        
        # 3. Add proper heading hierarchy
        content = self.enhance_headings(content)
        
        # 4. Enhance lists
        content = self.enhance_lists(content)
        
        # 5. Add proper paragraph spacing
        content = self.enhance_paragraphs(content)

        return content

    def wrap_and_classify_images(self, content):
        """
        Find images and wrap them in proper containers with classification
        """
        # Pattern to match img tags
        img_pattern = r'<img([^>]*?)src=["\']([^"\']+)["\']([^>]*?)>'
        
        def replace_img(match):
            pre_src_attrs = match.group(1)
            src = match.group(2)
            post_src_attrs = match.group(3)
            
            # Try to determine image dimensions and classify
            img_class = self.classify_image_by_url(src)
            
            # Build the new img tag with classification
            img_tag = f'<img{pre_src_attrs}src="{src}"{post_src_attrs} class="{img_class}">'
            
            # Wrap in container
            return f'<div class="image-container">{img_tag}</div>'
        
        return re.sub(img_pattern, replace_img, content)

    def classify_image_by_url(self, image_url):
        """
        Attempt to classify image based on its dimensions
        Default to landscape if unable to determine
        """
        try:
            # Try to get image dimensions
            if image_url.startswith('http'):
                response = requests.get(image_url, timeout=5)
                img = Image.open(BytesIO(response.content))
                width, height = img.size
            else:
                # Local file - might need adjustment based on your setup
                return 'image-landscape'  # Default for local files
            
            aspect_ratio = width / height
            
            if width < 400 and height < 400:
                return 'image-small'
            elif aspect_ratio < 0.8:
                return 'image-portrait'
            elif aspect_ratio > 1.3:
                return 'image-landscape'
            else:
                return 'image-square'
                
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Could not classify image {image_url}: {e}')
            )
            return 'image-landscape'  # Default fallback

    def enhance_blockquotes(self, content):
        """
        Ensure blockquotes have proper styling
        """
        # Already styled blockquotes will be handled by CSS
        return content

    def enhance_headings(self, content):
        """
        Ensure headings have proper hierarchy
        """
        # The CSS will handle heading styling
        # This could be extended to fix heading hierarchy issues
        return content

    def enhance_lists(self, content):
        """
        Enhance list formatting
        """
        # CSS will handle list styling
        return content

    def enhance_paragraphs(self, content):
        """
        Ensure proper paragraph spacing
        """
        # Remove excessive line breaks and normalize spacing
        content = re.sub(r'<br\s*/?>\s*<br\s*/?>', '</p><p>', content)
        content = re.sub(r'(\n\s*){3,}', '\n\n', content)
        
        # Ensure paragraphs are properly wrapped
        content = re.sub(r'<p>\s*</p>', '', content)  # Remove empty paragraphs
        
        return content

    def add_text_colors_and_highlights(self, content):
        """
        Convert any existing color styling to use the new classes
        """
        # Map old color styles to new classes
        color_mapping = {
            'color: #111827': 'class="text-primary"',
            'color: #6b7280': 'class="text-secondary"', 
            'color: #2563eb': 'class="text-accent"',
            'color: #059669': 'class="text-success"',
            'color: #d97706': 'class="text-warning"',
            'color: #dc2626': 'class="text-danger"',
        }
        
        for old_style, new_class in color_mapping.items():
            content = content.replace(f'style="{old_style}"', new_class)
            content = content.replace(f"style='{old_style}'", new_class)
        
        # Map background colors to highlight classes
        highlight_mapping = {
            'background-color: #fef3c7': 'class="highlight-yellow"',
            'background-color: #dbeafe': 'class="highlight-blue"',
            'background-color: #d1fae5': 'class="highlight-green"',
            'background-color: #fecaca': 'class="highlight-red"',
            'background-color: #e5e7eb': 'class="highlight-gray"',
        }
        
        for old_style, new_class in highlight_mapping.items():
            content = content.replace(f'style="{old_style}"', new_class)
            content = content.replace(f"style='{old_style}'", new_class)
        
        return content