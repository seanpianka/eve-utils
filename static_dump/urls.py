from django.conf.urls import patterns, include, url

from static_dump import views

urlpatterns = [
	url('^system_name_autocomplete/$', views.system_name_autocomplete, name='static_dump.system_name_autocomplete'),
	url('^station_name_autocomplete/$', views.station_name_autocomplete, name='static_dump.station_name_autocomplete'),
	url('^region_name_autocomplete/$', views.region_name_autocomplete, name='static_dump.region_name_autocomplete'),
]