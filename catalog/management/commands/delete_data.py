from django.core.management.base import BaseCommand

from catalog.models import Category, Product


class Command(BaseCommand):
    help = "Delete all data in database"

    def handle(self, *args, **options):
        """Удаляем все существующие записи"""
        Product.objects.all().delete()
        Category.objects.all().delete()
