from django.core.management.base import BaseCommand, CommandError
from xuan_elastic.views import analyzeAll, addMissingBookInfo

class Command(BaseCommand):
    def handle(self, *args, **options):
        analyzeAll()
