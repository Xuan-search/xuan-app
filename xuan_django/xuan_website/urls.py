from django.conf.urls import patterns, include, url
from django.views.generic import RedirectView
from . import views
from .views import XSSearchView

urlpatterns = patterns(
	'',
	url(r'^search/',XSSearchView.as_view(), name='xs_search')
)
