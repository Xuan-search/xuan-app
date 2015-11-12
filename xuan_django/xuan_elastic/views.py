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
	if 'from' in request.GET:
 		s= s[10,int(request.GET['from'])]
	#s = s.extra(size=10,from=offset)
	s = s.extra(fields=['book_title'])
	s = s.extra(partial_fields={"authors":{"include":"book_authors"}})
	
	searchword = 'match_phrase' if request.GET['exact']=='true' else 'match'
	s = s.query(searchword,html_body={"query":searchstring.encode('utf8'),"operator":"and"})
        s = s.highlight('html_body',fragment_size=150,number_of_fragments=3)
        s = s.highlight_options(pre_tags=["<em>"])
	#s = s.highlight_options(tags_schema='styled')
	response = client.search(index="xuan",doc_type="book",body=s.to_dict(),request_timeout=90)
	return JsonResponse(response, safe=False)

def searchFull(book_id,searchstring):
        searchstring = searchstring.decode('utf8')
	#terms = searchstring.split()
        client = Elasticsearch('localhost:9200')
        s = Search(client)
        s = s.extra(fields=[])
        s = s.filter("ids",values=[book_id])\
	    .query("match",html_body={"query":searchstring.encode('utf8'),"operator":"and"})

	s = s.highlight('html_body',number_of_fragments=0)
        s = s.highlight_options(pre_tags=["<em class='xs-search-hit'>"])
        response = client.search(index="xuan",doc_type="book",body=s.to_dict(),request_timeout=90)
        #print searchstring
        return response


def getBookById(book_id):
	client = Elasticsearch('localhost:9200')
	return client.get(index='xuan',doc_type='book',id=book_id)

