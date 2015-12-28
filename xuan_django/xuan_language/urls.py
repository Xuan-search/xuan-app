from django.conf.urls import patterns, include, url
from . import views

urlpatterns = patterns(
	'',
	url(r'^tokenize/',views.tokenize,name='es_lang'),
)
