from django.db import models
from elasticsearch_dsl import DocType, String, Date, Integer
# Create your models here.

class Book(DocType):
	book_title = String()
	book_authors = Nested()
	book_authors.field('first_name',String())
	book_authors.field('middle_name',String())
	book_authors.field('last_name',String())
	html_body = String(analyzer='xuan_html_analyzer')
	date_created = Date()a
	


#class ESBook(indexes.SearchIndex, indexes.Indexable):
#	text  = indexes.TextField(document=True, use_template=True)
#	date_created = indexes.DateTimeField(model_attr='date_created')
