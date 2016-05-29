from django.conf.urls import patterns, include, url

from maps import views

urlpatterns = [
	url('^shortest_path/$', views.shortest_path, name='maps.shortest_path'),
	url('^waypoints/$', views.manage_waypoints, name='maps.manage_waypoints'),
]

urlpatterns += [
	url('^waypoints/add/$', views.add_waypoint, name='maps.add_waypoint'),
	url('^waypoints/save/$', views.save_waypoints, name='maps.save_waypoints'),
]
