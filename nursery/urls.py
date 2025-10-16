# core/urls.py

from django.urls import path

from blog.urls import app_name
from . import views
app_name = 'nursery'
urlpatterns = [
    path('', views.home, name='home'),
    path('a-propos/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('maternelle/', views.maternelle, name='maternelle'),

]