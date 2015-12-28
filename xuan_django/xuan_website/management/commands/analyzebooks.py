from django.core.management.base import BaseCommand, CommandError
from xuan_elastic.views import analyzeAll

class Command(BaseCommand):
    def handle(self, *args, **options):
        analyzeAll()
