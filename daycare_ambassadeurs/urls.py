from django.urls import path
from . import views
from django.urls import reverse

app_name = 'daycare'

urlpatterns=[
    path('', views.home, name='home'),
    path('fr/', views.home_fr, name='home_fr'),
    path('subscribe/', views.subscribe_newsletter, name='subscribe_newsletter'),
]