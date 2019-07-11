
from django.core.management.base import BaseCommand

from init_mysqldata.init_tag import init_tag


class Command(BaseCommand):
    def handle(self, *args, **options):
        init_tag()