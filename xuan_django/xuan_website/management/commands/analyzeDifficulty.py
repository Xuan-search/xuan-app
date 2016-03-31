from django.core.management.base import BaseCommand, CommandError
from xuan_elastic.views import addDifficultyMetrics,rankWordCount
class Command(BaseCommand):
    def handle(self, *args, **options):
        #fixBookInfo()
        #getWordCount()
        #rankWordCount()
        addDifficultyMetrics()
