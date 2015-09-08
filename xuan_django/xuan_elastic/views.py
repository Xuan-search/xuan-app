from django.shortcuts import render
from django.template import RequestContext
from django.http import JsonResponse
from django.apps import apps
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
import urllib
import unicodedata
def search(request):
	searchstring = request.GET['q']
	searchstring = searchstring.decode('utf8')
	#terms = searchstring.split()
	client = Elasticsearch('localhost:9200')
	s = Search(client)
	s = s.extra(size=1000)
	s = s.extra(fields=['book_title'])
	s = s.extra(partial_fields={"authors":{"include":"book_authors"}})
	s = s.query("match",html_body={"query":searchstring.encode('utf8'),"operator":"and"})
	response = client.search(index="xuan",doc_type="book",body=s.to_dict())
	print response
	#print searchstring
	return JsonResponse(response, safe=False)
