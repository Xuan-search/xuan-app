from django.conf.urls import patterns, include, url
from django.views.generic import RedirectView
from . import views
from .views import XSSearchView, XSBookView, XSLoginView, XSLogoutView, getAudioData

urlpatterns = patterns(
    '',
    url(r'^$', RedirectView.as_view(url='search/',permanent=False), name='xs_index'),
    url(r'^search/',XSSearchView.as_view(), name='xs_search'),
    url(r'^book/(?P<book_id>.*)/',XSBookView.as_view(), name='xs_book'),
    url(r'^account/login/$',XSLoginView.as_view(), name='xs_login'),
    url(r'^account/logout/$',XSLogoutView.as_view(),name='xs_logout'),
    url(r'^api/audio/', getAudioData, name='xs_tts')
)
