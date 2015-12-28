from __future__ import division
from django.shortcuts import render
from django.template import RequestContext
from django.http import JsonResponse
from django.apps import apps
from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from django.views.decorators.csrf import csrf_exempt
import xuan_language.views as xuan_lang
import sys
import urllib
import json
import unicodedata
#search functions
def search(request):
    searchstring = request.GET['q']
    searchstring = searchstring.decode('utf8')
    #client = Elasticsearch('localhost:9200')
    client = Elasticsearch(settings.ELASTIC_ADDRESS)
    s = Search(client)
    if 'from' in request.GET:
    	s= s[10,int(request.GET['from'])]
    #s = s.extra(size=10,from=offset)
    s = s.extra(fields=['book_title'])
    s = s.extra(partial_fields={"authors":{"include":"book_authors"}})	
    s = s.highlight('html_body',fragment_size=150,number_of_fragments=3)
    s = s.highlight_options(pre_tags=["<em>"])
    #s = s.highlight_options(tags_schema='styled')
    response = {}
    if request.GET['match']=='phrase':
        s = s.query('match_phrase', html_body=searchstring.encode('utf8'))
    else:        
        s = s.query('match', html_body=searchstring.encode('utf8'))
    if request.GET['exact']=='true':
        #s = s.query('match_phrase', html_body=searchstring.encode('utf8'))
        response = client.search(index="xuan",doc_type="book",body=s.to_dict(),request_timeout=90,analyzer='keyword')
    else:
        #s = s.query('match', html_body=searchstring.encode('utf8'))
        response = client.search(index="xuan",doc_type="book",body=s.to_dict(),request_timeout=90)
    return JsonResponse(response, safe=False)

def searchFull(book_id,searchstring):
    searchstring = searchstring.decode('utf8')
    client = Elasticsearch(settings.ELASTIC_ADDRESS)
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
    client = Elasticsearch(settings.ELASTIC_ADDRESS)
    return client.get(index='xuan',doc_type='book',id=book_id)

def getBookInfoDocument(bookid):
    client = Elasticsearch(settings.ELASTIC_ADDRESS)
    s = Search(client)
    s = s.query("match",book_id=bookid)
    response = client.search(index="xuan",doc_type="book_info",body=s.to_dict(),request_timeout=90)
    
    if len(response['hits']['hits']) >0:
        response = response['hits']['hits'][0]
    else:
        response = {"_id":"", "_source":{}}
    return response

def getBookInfoById(request):
    response = getBookInfoDocument(request.GET['id'])    
    return JsonResponse(response['_source'], safe=False)
#book insert
@csrf_exempt
def addBook(request):
    client = Elasticsearch(settings.ELASTIC_ADDRESS)
    response = client.index(index='xuan', doc_type='book',body=request.body,request_timeout=90)
    bookid = response["_id"]    
    data = json.loads(request.body)
    tokens = xuan_lang.tokensForString(data["html_body"]) 
    bookinfo = {}
    bookinfo["book_id"] = bookid
    bookinfo["book_title"] = data["book_title"]
    bookinfo["frequency_counts"] = tokens
    bookresponse = client.index(index ='xuan', doc_type='book_info', body=bookinfo,request_timeout=90)
    response['book_info'] = bookresponse
    return JsonResponse(response, safe=False)

    

@csrf_exempt
def analyzeBookFrequencies(request,*args, **kwargs):
    return JsonResponse(analyzeBookFrequency(kwargs['book_id']))


def analyzeBookFrequency(bookid):
    client = Elasticsearch(settings.ELASTIC_ADDRESS)
    s = Search(client)
    countResponse = client.count(index='xuan', doc_type="book_info")
    totalcount = countResponse['count']
    #get book_info of target book
    bookInfoDocument = getBookInfoDocument(bookid)
    bookInfoId = bookInfoDocument["_id"]
    bookInfo = bookInfoDocument['_source']
    #modify percentil
    for i in range(len(bookInfo['frequency_counts'])):
        s = Search(client)
        s = s.query("match",html_body=bookInfo['frequency_counts'][i]['word'])
        wordResponse = client.search(index="xuan",doc_type="book",body=s.to_dict(), search_type="count")
        appearenceRate = wordResponse['hits']['total']
        bookInfo['frequency_counts'][i]['percentile']=appearenceRate/totalcount
     #finally, put modified book object
    finalResponse = client.index(index='xuan', doc_type='book_info', id=bookInfoId, body=bookInfo)
    finalResponse['bookid'] = bookid
    return finalResponse
     #return JsonResponse(finalResponse, safe=False)


@csrf_exempt
def analyzeAllFrequencies(request):
    results = analyzeAll()
    return JsonResponse(results, safe=False)

def analyzeAll():
    client = Elasticsearch(settings.ELASTIC_ADDRESS)
    s = Search(client)
    s = s.query("match_all").fields([])
    idsResponse = client.search(index="xuan",doc_type="book",body=s.to_dict(),size=10000)
    bookIDs = idsResponse['hits']['hits']
    success = 0
    fail = 0
    print('process started:' + str(len(bookIDs)) + ' books in database')
    for i in range(len(bookIDs)):
        bookid = bookIDs[i]['_id']        
        response = analyzeBookFrequency(bookid)
        if bookid == response['bookid']:
            success+=1
            print("analyze succeeded for book "+ bookid)
        else:
            fail+=1
            print("analyze failed for book " + bookid)
        print("book " + str(i) + " finished")
    print('analysis:' + str(success) + ' succeeded.' + str(fail) + ' failed')
    return {'succeeded':success, 'failed':fail}

def addDifficultyMetrics():
    client = Elasticsearch(settings.ELASTIC_ADDRESS)
    s = Search(client)
    page = 0
    go = True
    while(go):
        query = s.query('match_all')
        query = query[page*10:(page+1)*10]
        print("updating items from " + str(page*10) + " to " + str((page+1)*10))
        page+=1
        bookInfos = client.search(index="xuan",doc_type="book_info",body=query.to_dict())
        bookInfos = bookInfos['hits']['hits']
        if(len(bookInfos)<=0):
            go = False
            break
        for i in range(len(bookInfos)):
            bookInfoId = bookInfos[i]['_id']
            bookInfo = bookInfos[i]['_source']
            totalTokens = 0
            lv1Tokens = 0
            lv2Tokens = 0
            lv3Tokens = 0
            lv4Tokens = 0
            lv5Tokens = 0

            for q in range(len(bookInfo['frequency_counts'])):
                entry = bookInfo['frequency_counts'][q]
                
                totalTokens += entry['count']
                percentile = entry['percentile']
                if(percentile>.8):
                    lv1Tokens+=entry['count']
                elif(percentile>=.75):
                    lv2Tokens+=entry['count']
                elif(percentile>=.7):
                    lv3Tokens+=entry['count']
                elif(percentile>=.65):
                    lv4Tokens+=entry['count']
                else:
                    lv5Tokens+=entry['count']
            if(totalTokens>0):
                percentdifficulty = round((lv1Tokens + (lv2Tokens*2) + (lv3Tokens*3) + (lv4Tokens*4) + (lv5Tokens*5))/totalTokens)
                bookInfo['difficulty_by_percentile']=percentdifficulty
                bookInfo['tokens_count']=totalTokens
            
                client.index(index='xuan', doc_type='book_info',id=bookInfoId,body=bookInfo, request_timeout=90)
            else:   
                print("bookinfo has no tokens::"+bookInfoId)
            
    print('title add finished')


def modifyCapitalization():
    client = Elasticsearch(settings.ELASTIC_ADDRESS)
    s = Search(client)
    #s = s.query("match_all")
    page = 0
    go = True
    while(go):
        query = s.query('match_all')
        query = query[page*10:(page+1)*10]
        print("updating items from " + str(page*10) + " to " + str((page+1)*10))
        page+=1
        bookInfos = client.search(index="xuan",doc_type="book_info",body=query.to_dict())
        bookInfos = bookInfos['hits']['hits']
        if(len(bookInfos)<=0):
            go = False
            break
        for i in range(len(bookInfos)):
            bookInfoId = bookInfos[i]['_id']
            print(bookInfoId)
            bookInfo = bookInfos[i]['_source']
            modifiedFrequencyMap = {}
            modifiedFrequencyCounts = []
            for q in range(len(bookInfo['frequency_counts'])):
                entry = bookInfo['frequency_counts'][q]
                word = entry['word'].lower()
                if word in modifiedFrequencyMap:
                    modifiedFrequencyMap[word]['count']+=entry['count']
                else:
                    entry['word']=word
                    modifiedFrequencyMap[word]=entry
            for key in modifiedFrequencyMap:
                modifiedFrequencyCounts.append(modifiedFrequencyMap[key])

            bookInfo['frequency_counts'] = modifiedFrequencyCounts
            client.index(index='xuan', doc_type='book_info',id=bookInfoId,body=bookInfo, request_timeout=90)
            print("book " + str(i) + " processed:"+bookInfoId)

    print('title add finished')

def addTitleToAll():    
    client = Elasticsearch(settings.ELASTIC_ADDRESS)
    s = Search(client)
    s = s.query("match_all").fields([])
    idsResponse = client.search(index="xuan",doc_type="book",body=s.to_dict(),size=10000)
    bookIDs = idsResponse['hits']['hits']
    print('process started:' + str(len(bookIDs)) + ' books in database')
    for i in range(len(bookIDs)):
        bookid = bookIDs[i]['_id']
        print(bookid)
        bookInfo = getBookInfoDocument(bookid)
        bookInfoId = bookInfo['_id']
        if bookInfoId=='':
            print("ALERT: book with id " + bookid + " has no book info")
            print(bookInfo)
            #break
        else:
            book = client.get(index='xuan',doc_type='book',id=bookid, fields='book_title')
            bookInfo = bookInfo['_source']
            bookInfo['book_title'] = book['fields']['book_title'][0]
            #bookInfo['frequency_counts']={}
            client.index(index='xuan', doc_type='book_info', id=bookInfoId,body=bookInfo)
            #print(bookInfo)
            
        print("book " + str(i) + " processed:"+bookInfoId)
    print('title add finished')

    #response = analyzeBookFrequency(request,None,{}
