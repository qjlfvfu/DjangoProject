import stripe
from django.conf import settings
from .models import Course

stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """Сервис для работы со Stripe"""

    @staticmethod
    def create_product(course):
        """Создание продукта в Stripe"""
        try:
            product = stripe.Product.create(
                name=course.name,
                description=course.description[:500] if course.description else "",
                metadata={
                    'course_id': course.id
                }
            )
            return product
        except stripe.error.StripeError as e:
            print(f"Ошибка создания продукта: {e}")
            return None

    @staticmethod
    def create_price(product_id, amount=1000, currency='rub'):
        """Создание цены для продукта"""
        try:
            price = stripe.Price.create(
                product=product_id,
                unit_amount=amount,  # в копейках/центах
                currency=currency,
            )
            return price
        except stripe.error.StripeError as e:
            print(f"Ошибка создания цены: {e}")
            return None

    @staticmethod
    def create_checkout_session(price_id, success_url, cancel_url):
        """Создание сессии для оплаты"""
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price': price_id,
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
            )
            return checkout_session
        except stripe.error.StripeError as e:
            print(f"Ошибка создания сессии: {e}")
            return None

    @staticmethod
    def get_checkout_session(session_id):
        """Получение информации о сессии"""
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return session
        except stripe.error.StripeError as e:
            print(f"Ошибка получения сессии: {e}")
            return None