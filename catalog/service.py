from .models import Product , Category

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