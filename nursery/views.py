from django.shortcuts import render
from django.contrib import messages
from django.core.mail import send_mail, BadHeaderError
from django.conf import settings
from django.http import HttpResponse

from blog.models import Article
from .models import ContactMessage

# Create your views here.
def home(request):
    articles = Article.objects.filter(status='published').order_by('-published_at')[:6]
    return render(request, 'nursery/home.html', {'articles': articles})

def about(request):
    return render(request, 'nursery/apropos.html')

def contact(request):
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        message = request.POST.get('message', '').strip()
        
        # Validate required fields
        if not name or not email or not message:
            messages.error(request, 'Veuillez remplir tous les champs obligatoires.')
            return render(request, 'nursery/contact.html')
        
        # Prepare email content
        subject = f'Nouveau message de contact - {name}'
        email_message = f"""
        Vous avez reçu un nouveau message depuis le formulaire de contact.
        
        Nom: {name}
        Email: {email}
        Téléphone: {phone if phone else 'Non fourni'}
        
        Message:
        {message}
        
        ---
        Ce message a été envoyé depuis le formulaire de contact du site web.
        """
        
        try:
            # Save to database first (backup)
            contact_msg = ContactMessage.objects.create(
                name=name,
                email=email,
                phone=phone,
                message=message
            )
            
            # Send email to school
            send_mail(
                subject=subject,
                message=email_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_EMAIL],
                fail_silently=False,
            )
            messages.success(request, 'Votre message a été envoyé avec succès! Nous vous répondrons dans les plus brefs délais.')
        except BadHeaderError:
            messages.error(request, 'Une erreur est survenue. Veuillez vérifier vos informations.')
        except Exception as e:
            messages.error(request, f'Une erreur est survenue lors de l\'envoi de votre message. Veuillez réessayer plus tard.')
            print(f"Email error: {e}")  # For debugging
    
    return render(request, 'nursery/contact.html')

def maternelle(request):
    return render(request, 'nursery/maternelle.html')

