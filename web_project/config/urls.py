"""
URL configuration for web_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render

def main_page(request):
    return render(request, 'main.html')

def guide_page(request):
    return render(request, 'guide.html')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', main_page, name='main'), 
    path('guide/', guide_page, name='guide'),
    path('users/', include('users.urls')),
    path('analysis/', include('analysis.urls')),
    path('django_plotly_dash/', include('django_plotly_dash.urls')), 
]
