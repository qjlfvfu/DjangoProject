from django.core.management.base import BaseCommand
from catalog.models import Category, Product


class Command(BaseCommand):
    help = "Заполнить базу тестовыми данными"

    def handle(self, *args, **options):
        # Создаем категории
        categories = [
            Category(name="Мясо", description="Мясные продукты"),
            Category(name="Рыба", description="Рыбные продукты"),
            Category(name="Овощи", description="Свежие овощи"),
            Category(name="Фрукты", description="Свежие фрукты"),
        ]

        Category.objects.bulk_create(categories)

        # Получаем созданные категории
        meat = Category.objects.get(name="Мясо")
        fish = Category.objects.get(name="Рыба")

        # Создаем продукты
        products = [
            Product(name="Говядина", price=500, category=meat),
            Product(name="Свинина", price=450, category=meat),
            Product(name="Лосось", price=800, category=fish),
            Product(name="Форель", price=600, category=fish),
        ]

        Product.objects.bulk_create(products)

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Создано {Category.objects.count()} категорий "
                f"и {Product.objects.count()} продуктов"
            )
        )