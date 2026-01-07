from django.core.management.base import BaseCommand
from django.core.management import call_command
from catalog.models import Category,Product

class Command(BaseCommand):
    help= "load fixture in database"
    def handle(self, *args, **options):
        call_command("loaddata", "сategory_fixture.json")
        call_command("loaddata","product_fixture.json")
        self.stdout.write(self.style.SUCCESS("COMPLETE!✅"))
