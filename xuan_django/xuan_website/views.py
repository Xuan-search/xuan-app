from django.shortcuts import render_to_response, render, redirect
from django.contrib.auth import authenticate, logout, login
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse, Http404
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.utils import timezone
from django.apps import apps
import xuan_elastic.views as xuan_es
import datetime as dt
# Create your views here.
#
#@login_required(login_url='/account/login/')

class XSLoginView(TemplateView):
	template_name = 'authentication/login.html'
	def post(self, request):
		state = "Log in below:"
		username = request.POST['username']
		password = request.POST['password']
		user = authenticate(username=username,password=password)
		if user is not None:
			login(request, user)
			return HttpResponseRedirect('/search')	
		else:
			return render_to_response(self.template_name,
					{'error':'Username/password incorrect'},
					context_instance=RequestContext(request))

class LoginRequiredMixin(object):
	@classmethod
	def as_view(cls):
		return login_required(super(LoginRequiredMixin,cls).as_view())

class XSSearchView(LoginRequiredMixin,TemplateView):
	template_name = 'search/searchMain.html'
	login_url='account/login'
	def get(self,request,*args,**kwargs):
		return render(request,self.template_name)

class XSBookView(TemplateView):
	template_name = 'search/searchBook.html'
	def get_context_data(self, **kwargs):
		context = super(XSBookView,self).get_context_data(**kwargs)
		
		result = xuan_es.searchFull(kwargs['book_id'],self.request.GET['q'])
		book_content = result['hits']['hits'][0]
		print(book_content['highlight'])
		book_content = book_content['highlight']['html_body'][0] if 'highlight' in book_content else 'not found'
		context['book_content'] = book_content
		return context

class XSLogoutView(LoginRequiredMixin, TemplateView):
	def get(self,request,*args, **kwargs):
		logout(request)
		return HttpResponseRedirect('/account/login')
