from django.conf.urls import patterns, include, url
from . import views

urlpatterns = patterns(
	'',
	url(r'^books/',views.search,name='es_search'),
)
