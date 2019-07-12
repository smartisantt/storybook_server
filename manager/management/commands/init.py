
from django.core.management.base import BaseCommand

from init_mysqldata.init_data import init_tag, init_admin


class Command(BaseCommand):
    def handle(self, *args, **options):
        init_tag()
        init_admin()