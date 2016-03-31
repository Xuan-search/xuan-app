from __future__ import division#,absolute_import
from django.shortcuts import render
from django.template import RequestContext
from django.http import JsonResponse
from django.apps import apps
from django.conf import settings
from elasticsearch import Elasticsearch, exceptions
from elasticsearch_dsl import Search
from django.views.decorators.csrf import csrf_exempt
#from celery import shared_task
import xuan_language.views as xuan_lang
import sys
import urllib,httplib,requests
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
    #s = s.highlight('html_body',fragment_size=150,number_of_fragments=3)
    s = s.highlight_options(pre_tags=["<em>"])
    #s = s.highlight_options(tags_schema='styled')
    
    response = {}
#    if request.GET['match']=='phrase':
#        s = s.query('match_phrase', html_body=searchstring.encode('utf8'))
#    else:        
#        s = s.query('match', html_body=searchstring.encode('utf8'))

    matchingIds = []
    keywords = searchstring.encode('utf8').split()
        
    if request.GET['match']=='phrase':
        s = s.highlight('html_body.tokens', fragment_size=150, number_of_fragments=1)
        s = s.query('match_phrase', **{'html_body.tokens':searchstring.encode('utf8')})
    elif request.GET['exact']=='true':
        s = s.highlight('html_body.tokens', fragment_size=150, number_of_fragments=1)
        
        if len(keywords)>1:
            for i in range(len(keywords)):
                s = s.query('match', **{'html_body.tokens':keywords[i]})
        else:
            s = s.query('match', **{'html_body.tokens':searchstring.encode('utf8')})
    else:
        s = s.highlight('html_body', fragment_size=150,number_of_fragments=1)        
        
        if len(keywords)>1:
            for i in range(len(keywords)):
                s = s.query('match', html_body=keywords[i])
        else:
            s = s.query('match', html_body=searchstring.encode('utf8'))

    shouldFilter = request.GET['difficulty']
    if shouldFilter:
        #print("shouldfilter")
        #matchingIds = getIDsByDifficulty(request)
        #s = s.filter('ids', values=matchingIds)
        s = s.filter('term',**{request.GET['difficulty']:request.GET['from_difficulty']}) 

    response = client.search(index="xuan",doc_type="book",body=s.to_dict(),request_timeout=90)
    if request.GET['match']=='phrase':
        #filter out highlight size because of elasticsearch bug: github #9442
        for hit in response['hits']['hits']:
            print(hit)
            if len(hit['highlight']['html_body.tokens'][0])>250:
                #fix too long ES highlight return
                print("found hit")
                buggedHighlight = hit['highlight']['html_body.tokens'][0]
                buggedHighlight = buggedHighlight[:250]
                print("tailed pt1")
                hit['highlight']['html_body.tokens'][0]=buggedHighlight[:buggedHighlight.rfind(' ')]
                print("tailed pt2")
    return JsonResponse(response, safe=False)

    
def getIDsByDifficulty(request):
    client = Elasticsearch(settings.ELASTIC_ADDRESS)
    difficulty_metric = request.GET['difficulty']
    from_difficulty = request.GET['from_difficulty']
    to_difficulty = request.GET['to_difficulty']
    info = Search(client)
    info = info.fields(['book_id'])
    info = info.filter('range',**{difficulty_metric:{"gte":float(from_difficulty), "lt":float(to_difficulty)}})
    print("precall")
    ids = client.search(index="xuan", doc_type="book_info", body=info.to_dict(),request_timeout=500,size=99999)
    print(ids['hits']['hits'][0])
    matchingIds = []
    for hit in ids['hits']['hits']:
        bookId = hit['fields']['book_id'][0]
        matchingIds.append(bookId)
    return matchingIds


def searchFull(book_id,searchstring):
    searchstring = searchstring.decode('utf8')
    client = Elasticsearch(settings.ELASTIC_ADDRESS)
            #rank = rank['_source']['rank']
    s = Search(client)
    s = s.extra(fields=[])
    s = s.filter("ids",values=[book_id])\
	.query("match",html_body={"query":searchstring.encode('utf8'),"operator":"or"})
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
    data = json.loads(request.body)
    response = client.index(index='xuan', doc_type='book',body=data,request_timeout=90) 
    bookid = response["_id"]    
    print("book added:"+bookid)
    tokens = xuan_lang.tokensForString(data["html_body"]) 
    bookinfo = {}
    bookinfo["book_id"] = bookid
    bookinfo["book_title"] = data["book_title"]
    bookinfo["frequency_counts"] = tokens
    bookresponse = client.index(index ='xuan', doc_type='book_info', body=bookinfo,request_timeout=90)
    response['book_info'] = bookresponse
    return JsonResponse(response, safe=False)


def addMissingBookInfo():

    client = Elasticsearch(settings.ELASTIC_ADDRESS)
    s = Search(client)
    s = s.filter("not",nested={"path":"frequency_counts","filter":{"match_all":{}}}).fields(['book_id'])
    emptyBookInfos = client.search(index="xuan",doc_type="book_info",body=s.to_dict(),size=10000)
    bookIDs = idsResponse['hits']['hits']
    print('process started:' + str(len(bookIDs)) + ' books in database')
    for i in range(len(bookIDs)):
        bookinfoid = bookIDs[i]['_id']
        bookid = bookIDs[i]['_source']['book_id']
        s = Search(client)
        s = s.query("match",book_id=bookid).fields([])
        response = client.search(index="xuan",doc_type="book_info",body=s.to_dict(),request_timeout=90)
        if (response['hits']['total']==0):
            print('book with id ' + bookid + ' has no book info')
            analyzeBookFrequency(bookid)
            break


#helper functions

def attachBookFrequency(bookInfo):

    client = Elasticsearch(settings.ELASTIC_ADDRESS)    
    countResponse = client.count(index='xuan', doc_type="book_info")
    totalcount = countResponse['count']
   
    for i in range(len(bookInfo['frequency_counts'])):
        s = Search(client)
        s = s.query("match",html_body=bookInfo['frequency_counts'][i]['word'])
        wordResponse = client.search(index="xuan",doc_type="book",body=s.to_dict(), search_type="count")
        appearenceRate = wordResponse['hits']['total']
        bookInfo['frequency_counts'][i]['percentile']=appearenceRate/totalcount
    return bookInfo

#@shared_task
def attachDifficultyMetrics(bookInfo):
    totalTokens = 0
    totalUniqueTokens = 0
    lv1TokensPerc = 0
    lv2TokensPerc = 0
    lv3TokensPerc = 0
    lv4TokensPerc = 0
    lv5TokensPerc = 0
    lv1TokensFreq = 0
    lv2TokensFreq = 0
    lv3TokensFreq = 0
    lv4TokensFreq = 0
    lv5TokensFreq = 0

    for q in range(len(bookInfo['frequency_counts'])):
        entry = bookInfo['frequency_counts'][q]
        totalUniqueTokens+=1
        totalTokens += entry['count']
        if 'percentile' in entry:
            percentile = entry['percentile']
            
            if(percentile>.8):
                lv1TokensPerc+=1#+=entry['count']
            elif(percentile>=.75):
                lv2TokensPerc+=1#+=entry['count']
            elif(percentile>=.7):
                lv3TokensPerc+=1#=entry['count']
            elif(percentile>=.65):
                lv4TokensPerc+=1#=entry['count']
            else:
                lv5TokensPerc+=1#=entry['count']
        #else:
        #    if(q<5):
        #        print("percentile not found for word " + entry['word'])
        client = Elasticsearch(settings.ELASTIC_ADDRESS)
        rank = {} 
        try:
            rank = client.get(index='xuan', doc_type='wordcount',id=entry['word'])    
            if 'rank' not in rank['_source']:
                rank = 99999    
            else:
                rank = rank['_source']['rank']
        except:
            #print('wordcount not found for ' + entry['word'])
            rank = 99999
        if(rank <= 100):
            lv1TokensFreq+=entry['count']
        elif(rank<=200):
            lv2TokensFreq+=entry['count']
        elif(rank<=500):
            lv3TokensFreq+=entry['count']
        elif(rank<=5000):
            lv4TokensFreq+=entry['count']
        else:
            lv5TokensFreq+=entry['count']
        
        
    if(totalUniqueTokens>0):
        percentdifficulty = round((lv1TokensPerc + (lv2TokensPerc*2) + (lv3TokensPerc*3) + (lv4TokensPerc*4) + (lv5TokensPerc*5))/totalUniqueTokens)
        frequencydifficulty = round((lv1TokensFreq + (lv2TokensFreq*2) + (lv3TokensFreq*3) + (lv4TokensFreq*4) + (lv5TokensFreq*5))/totalTokens)
        
        bookInfo['difficulty_by_percentile']=percentdifficulty
        if(frequencydifficulty>0):
            bookInfo['difficulty_by_frequency']=frequencydifficulty

        tokensDifficulty=0
        if(totalTokens <= 1000):
            tokensDifficulty=1
        elif(totalTokens <= 2000):
            tokensDifficulty=2
        elif(totalTokens <= 6000):
            tokensDifficulty=3
        elif(totalTokens <= 10000):
            tokensDifficulty=4
        elif(totalTokens <= 15000):
            tokensDifficulty=5
        else:
            tokensDifficulty=6
        bookInfo['difficulty_by_unique_tokens']=tokensDifficulty
        bookInfo['unique_tokens_count']=totalUniqueTokens
        print("difficulties:" + str(percentdifficulty) +","+str(frequencydifficulty)+","+str(tokensDifficulty))
         #client.index(index='xuan', doc_type='book_info',id=bookInfoId,body=bookInfo, request_timeout=90)
    return bookInfo


def analyzeBookFrequencies(request,*args, **kwargs):
    return JsonResponse(analyzeBookFrequency(kwargs['book_id']))


def analyzeBookFrequency(bookid):
    client = Elasticsearch(settings.ELASTIC_ADDRESS)
    s = Search(client)
    bookInfoDocument = getBookInfoDocument(bookid)
    bookInfoId = bookInfoDocument["_id"]
    bookInfo = bookInfoDocument["_source"]
    
    #bookInfo = attachBookFrequency(bookInfo)
    bookInfo = attachDifficultyMetrics(bookInfo)
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
    page = 0
    go = True
    success = 0
    fail = 0
    while(go):
        #query = s.query('match_all')
        #query = query[page*10:(page+1)*10]
        #print("updating items from " + str(page*10) + " to " + str((page+1)*10))
        #page+=1
        #bookInfos = client.search(index="xuan",doc_type="book_info",body=query.to_dict())
        #bookInfos = bookInfos['hits']['hits']

        query = s.query("match_all").fields([])        
        query = query[page*10:(page+1)*10]
        print("updating items from " + str(page*10) + " to " + str((page+1)*10))
        page+=1
        idsResponse = client.search(index="xuan",doc_type="book",body=query.to_dict())
        bookIDs = idsResponse['hits']['hits']
        if(len(bookIDs)<=0):
            go=False
            break
        for i in range(len(bookIDs)):
            bookid = bookIDs[i]['_id']        
            response = analyzeBookFrequency(bookid)
            if bookid == response['bookid']:
                success+=1
                print("analyze succeeded for book "+ bookid)
            else:
                fail+=1
                print("analyze failed for book " + bookid)
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
            #bookInfo = attachDifficultyMetrics(bookInfo)
            bookId = bookInfo['book_id']
            

            if 'difficulty_by_unique_tokens' in bookInfo:
                difficulties = {'doc':{}}
                print(bookId)
                difficulties['doc']['difficulty_by_frequency']=bookInfo['difficulty_by_frequency']
                difficulties['doc']['difficulty_by_percentile']=bookInfo['difficulty_by_percentile']
                difficulties['doc']['difficulty_by_unique_tokens']=bookInfo['difficulty_by_unique_tokens']
                client.update(index='xuan', doc_type='book', id=bookId, body=difficulties)
            #client.index(index='xuan', doc_type='book_info',id=bookInfoId,body=bookInfo, request_timeout=90)
            
    print('difficulty add finished')


def rankWordCount():   
    client = Elasticsearch(settings.ELASTIC_ADDRESS)
    s = Search(client)
    #s = s.query("match_all")
    page = 22
    size = 10000
    go = True
    while(go):
        query = s.query('match_all')
        query = query.sort({'count':"desc"})
        query = query[page*size:(page+1)*size]
        offset = page*size
        print(str(query.to_dict()))
        print("updating items from " + str(offset) + " to " + str((page+1)*size))
        page+=1
        wordcounts = client.search(index="xuan",doc_type="wordcount",body=query.to_dict())
        wordcounts = wordcounts['hits']['hits']
        if(len(wordcounts)<=0):
            go = False
            break
        for i in range(len(wordcounts)):
            itemId = wordcounts[i]['_id']
            item = wordcounts[i]['_source']

            item['rank'] = offset+i+1
            #print("got rank " + str(offset+i+1))
            client.index(index='xuan', doc_type='wordcount',id=itemId,body=item)


def getWordCount():
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
            bookInfo = bookInfos[i]['_source']

            for q in range(len(bookInfo['frequency_counts'])):
                entry = bookInfo['frequency_counts'][q]
                body = {\
                        "script":"ctx._source.count+="+str(entry['count']),\
                        "upsert":{"word":entry['word'],'count':entry['count']}
                        }
                headers = { 'Content-type':'application/json; charset=UTF-8',\
                            'Accept':"text/plain"}
                #conn = httplib.HTTPConnection(settings.ELASTIC_ADDRESS)
                #conn.request('POST', '/xuan/wordcount/'+entry['word']+'/_update',urllib.urlencode(body), headers)
                #response = conn.getresponse()
                #print response.status, response.reason
                #data = response.read()
                #conn.close()
                r = requests.post('http://'+settings.ELASTIC_ADDRESS+'/xuan/wordcount/'+entry['word']+'/_update',json=body)
                #response = client.update(index='xuan', doc_type='wordcount',id=entry['word'],\
                #                script='ctx._source.count+='+str(entry['count']),\
                #                scripted_upsert=True,upsert={})
                      #upsert={"word":entry['word'],'count':entry['count']})          #upsert={"word":entry['word'],'count':entry['count']})            
                
                #print(response)
            print("bookInfo " + bookInfoId + " processed")
        
