from django.core.management.base import BaseCommand, CommandError
from xuan_elastic.views import addDifficultyMetrics
class Command(BaseCommand):
    def handle(self, *args, **options):
        #fixBookInfo()
        addDifficultyMetrics()
