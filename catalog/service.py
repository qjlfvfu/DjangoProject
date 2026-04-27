from django.core.cache import cache
from django.conf import settings
from .models import Product, Category


class ProductService:
    @staticmethod
    def get_products_by_category(category_id):
        """
        Возвращает все продукты в указанной категории
        """
        try:
            category = Category.objects.get(id=category_id)
            products = Product.objects.filter(category=category, is_active=True)
            return products
        except Category.DoesNotExist:
            return Product.objects.none()

    @staticmethod
    def get_cached_catalog():
        """
        Возвращает список товаров для каталога с использованием кеширования
        """
        # Проверяем, включено ли кеширование
        cache_backend = settings.CACHES.get("default", {}).get("BACKEND", "")

        if "dummy" not in cache_backend.lower():
            # Кеширование включено (не DummyCache)
            cached_data = cache.get("catalog_products")

            if cached_data is None:
                # Данных нет в кеше - получаем из БД и сохраняем
                cached_data = Product.objects.filter(is_published=True).order_by(
                    "-created_at"
                )
                cache.set("catalog_products", cached_data, 60 * 15)  # 15 минут

            return cached_data
        else:
            # Кеширование выключено - просто возвращаем из БД
            return Product.objects.filter(is_published=True).order_by("-created_at")

    @staticmethod
    def get_cached_products_by_category(category_id):
        """
        Возвращает продукты категории с кешированием
        """
        cache_key = f"category_products_{category_id}"

        # Проверяем, включено ли кеширование
        cache_backend = settings.CACHES.get("default", {}).get("BACKEND", "")

        if "dummy" not in cache_backend.lower():
            # Кеширование включено
            cached_data = cache.get(cache_key)

            if cached_data is None:
                # Данных нет в кеше - получаем из БД и сохраняем
                cached_data = ProductService.get_products_by_category(category_id)
                cache.set(cache_key, cached_data, 60 * 30)  # 30 минут

            return cached_data
        else:
            # Кеширование выключено
            return ProductService.get_products_by_category(category_id)

    @staticmethod
    def clear_category_cache(category_id):
        """
        Очищает кеш для конкретной категории
        """
        cache_key = f"category_products_{category_id}"
        cache.delete(cache_key)

    @staticmethod
    def clear_catalog_cache():
        """
        Очищает кеш каталога
        """
        cache.delete("catalog_products")
