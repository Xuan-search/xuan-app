from django.conf.urls import patterns, include, url
from . import views

urlpatterns = patterns(
	'',
	url(r'^books/',views.search,name='es_search'),
        url(r'^book_info/$',views.getBookInfoById, name='es_book_info'),
        url(r'^book/', views.addBook,name='es_addbook'),
        url(r'^book_info/analyze_all/$', views.analyzeAllFrequencies, name='es_analyze_all'),
        url(r'^book_info/(?P<book_id>.*)/analyze/', views.analyzeBookFrequencies, name='es_analyze'),
)
