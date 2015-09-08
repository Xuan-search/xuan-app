from django.shortcuts import render_to_response, render, redirect
from django.contrib.auth import authenticate, logout, login
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse, Http404
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.utils import timezone
from django.apps import apps
import datetime as dt
# Create your views here.

class XSSearchView(TemplateView):
	template_name = 'search/searchMain.html'
	def get(self,request,*args,**kwargs):
		return render(request,self.template_name)
