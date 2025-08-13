from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image as PilImage
import io
from PIL import Image
from io import BytesIO
import os
from bs4 import BeautifulSoup
from django.utils.text import slugify

from blog.models import Attachment


def create_thumbnail(image, size=(100, 100)):
    img = PilImage.open(image)
    img.thumbnail(size)
    buffer = io.BytesIO()
    img.save(buffer, format='WEBP', quality=80)
    return InMemoryUploadedFile(
        buffer,
        'ImageField',
        image.name.rsplit('.', 1)[0] + '_thumb.webp',
        'image/webp',
        buffer.getbuffer().nbytes,
        None
    )

def optimize_image(image_file):
    img = Image.open(image_file)

    # Resize if too large
    if img.width > 1200:
        ratio = 1200 / img.width
        new_height = int(img.height * ratio)
        img = img.resize((1200, new_height), Image.LANCZOS)

    # Convert to webp
    output = BytesIO()
    img.save(output, format='WEBP', quality=85)
    output.seek(0)

    return ContentFile(output.read(), name=f"{image_file.name.split('.')[0]}.webp")

def resize_image(image_file, max_width):
    """Resizes an image to a specific width, maintaining aspect ratio, and converts to WebP."""
    try:
        image_file.seek(0)
        img = PilImage.open(image_file).convert("RGB")
    except Exception as e:
        print(f"Error opening image: {e}")
        return None

    if img.width <= max_width:
        return None # Don't upscale images

    ratio = max_width / float(img.width)
    new_height = int(float(img.height) * float(ratio))
    img = img.resize((max_width, new_height), PilImage.Resampling.LANCZOS)

    buffer = io.BytesIO()
    img.save(buffer, format='WEBP', quality=85)
    buffer.seek(0)

    original_filename, _ = os.path.splitext(image_file.name)
    # Use a consistent naming scheme for resized images
    new_filename = f"{slugify(original_filename)}_{max_width}w.webp"

    return ContentFile(buffer.read(), name=new_filename)

def process_content_for_display(content):
    """Parse article HTML and add responsive image attributes"""
    if not content:
        return ""

    soup = BeautifulSoup(content, 'html.parser')
    images = soup.find_all('img')

    for img_tag in images:
        src = img_tag.get('src')
        if not src:
            continue

        try:
            # Find attachment based on URL
            attachment = Attachment.objects.filter(link=src).first()
            if not attachment:
                continue

            # Add responsive attributes
            if attachment.image_sizes:
                srcset = []
                for width, url in attachment.image_sizes.items():
                    srcset.append(f"{url} {width}w")
                img_tag['srcset'] = ', '.join(srcset)
                img_tag['sizes'] = "(max-width: 768px) 100vw, 80vw"

            # Add alt text
            if not img_tag.get('alt') and attachment.caption:
                img_tag['alt'] = attachment.caption

            # Add loading attribute
            img_tag['loading'] = 'lazy'

        except Exception as e:
            print(f"Error processing image: {e}")

    return str(soup)

def create_responsive_images(image_file):
    """Generate responsive image sizes and return a dict of width:url"""
    sizes = [400, 800, 1200, 1600]
    image_versions = {}

    try:
        img = PilImage.open(image_file)
        original_format = img.format
        original_filename, extension = os.path.splitext(image_file.name)

        for size in sizes:
            # Don't upscale images smaller than requested size
            if img.width < size:
                continue

            buffer = io.BytesIO()
            resized = img.copy()
            resized.thumbnail((size, size * 2))  # Maintain aspect ratio

            # Convert to WEBP if possible
            if resized.mode != 'RGB':
                resized = resized.convert('RGB')

            resized.save(buffer, format='WEBP', quality=85)
            buffer.seek(0)

            # Create new filename
            new_filename = f"{slugify(original_filename)}_{size}w.webp"
            content_file = ContentFile(buffer.read(), name=new_filename)

            # Save to storage and get URL
            # You'll need to implement your storage system here
            # For example:
            # file_path = default_storage.save(new_filename, content_file)
            # url = default_storage.url(file_path)

            # For now, we'll just store the filename
            image_versions[size] = new_filename

    except Exception as e:
        print(f"Error creating responsive images: {e}")

    return image_versions