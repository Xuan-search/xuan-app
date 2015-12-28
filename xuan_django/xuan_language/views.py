from __future__ import division
from django.shortcuts import render
from django.template import RequestContext
from django.http import JsonResponse
from django.apps import apps
import nltk, re, pprint
from nltk import word_tokenize
from bs4 import BeautifulSoup
def tokenize(request):
    tokens =tokensForString(request.GET['text']) #nltk.word_tokenize(request.GET['text'])
    response = {}
    response['chart'] = tokens
    return JsonResponse(response, safe=False)

def tokensForString(rawdoc):
    cleantext = BeautifulSoup(rawdoc,"html.parser").get_text()
    tokens = word_tokenize(cleantext)
    frequencycounts = {}
    for token in tokens:
        if not is_number(token):
            if token in frequencycounts:
                frequencycounts[token]+=1
            else:
                frequencycounts[token]=1

    frequencyarray = []
    for frequency in frequencycounts:
        entry = {"word":frequency, "count":frequencycounts[frequency],}
        frequencyarray.append(entry) 
    return frequencyarray

    
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
