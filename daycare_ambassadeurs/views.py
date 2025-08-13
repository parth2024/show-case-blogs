from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from blog.models import *

# Create your views here.
def home(request):
    """
    Render the home page of the daycare ambassadors application.
    """
    articles = Article.objects.filter(status='published').order_by('-published_at')[:5]
    context = {
        'articles': articles,
    }
    return render(request, 'daycare_ambassadeurs/home.html', context)

def subscribe_newsletter(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()

        if name and email:
            # Create or update subscriber
            subscriber, created = User.objects.update_or_create(
                email=email,
                defaults={'name': name}
            )

            if created:
                messages.success(request, 'Thank you for subscribing!')
            else:
                messages.info(request, 'Subscription updated!')
        else:
            messages.error(request, 'Please provide both name and email.')

    # Redirect back to home page
    return HttpResponseRedirect(reverse('home'))

def home_fr(request):
    """
    Render the home page of the daycare ambassadors application in french.
    """
    articles = Article.objects.filter(status='published').order_by('-published_at')[:5]
    context = {
        'articles': articles,
    }
    return render(request, 'daycare_ambassadeurs/home_fr.html', context)