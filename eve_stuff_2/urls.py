"""eve_stuff_2 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import include, url
from django.views.generic.base import TemplateView
from django.conf.urls.static import static

urlpatterns = [
	#static files
	url(r'^robots\.txt$', TemplateView.as_view(template_name='static/robots.txt')),
	url(r'^sitemap\.txt$', TemplateView.as_view(template_name='static/sitemap.txt')),
	url(r'^googlefffb464ff0a5129c\.html',TemplateView.as_view(template_name='static/googlefffb464ff0a5129c.html')),
	
	url(r'^maps/', include('maps.urls')),
	url(r'^static_dump/', include('static_dump.urls')),
	
	#root url
	url(r'^$', TemplateView.as_view(template_name='index.html')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)