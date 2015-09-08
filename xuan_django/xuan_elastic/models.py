from django.db import models

# Create your models here.
class ESBook(indexes.SearchIndex, indexes.Indexable):
	text  = indexes.TextField(document=True, use_template=True)
	date_created = indexes.DateTimeField(model_attr='date_created')
