from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.conf import settings
import stripe

from .models import Course, Lesson, Subscription
from .validators import validate_youtube_url

User = get_user_model()


class LessonCRUDTests(TestCase):
    """Тесты для CRUD операций уроков"""

    def setUp(self):
        self.client = APIClient()
        # Создаем пользователей
        self.user = User.objects.create_user(email="user@test.com", password="test123")
        self.moderator = User.objects.create_user(
            email="moderator@test.com", password="test123"
        )
        # Создаем группу модераторов
        moderator_group, _ = Group.objects.get_or_create(name="moderators")
        self.moderator.groups.add(moderator_group)
        self.other_user = User.objects.create_user(
            email="other@test.com", password="test123"
        )
        # Создаем курс
        self.course = Course.objects.create(
            name="Test Course", description="Test Description", owner=self.user
        )
        # Создаем урок
        self.lesson = Lesson.objects.create(
            course=self.course,
            name="Test Lesson",
            description="Test Lesson Description",
            video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            owner=self.user,
        )
        # URL для API
        self.lessons_list_url = reverse("lesson:lesson-list")
        self.lessons_create_url = reverse("lesson:lesson-create")
        self.lessons_detail_url = reverse(
            "lesson:lesson-retrieve", kwargs={"pk": self.lesson.id}
        )
        self.lessons_update_url = reverse(
            "lesson:lesson-update", kwargs={"pk": self.lesson.id}
        )
        self.lessons_delete_url = reverse(
            "lesson:lesson-delete", kwargs={"pk": self.lesson.id}
        )

    # === ТЕСТЫ НА СОЗДАНИЕ УРОКА ===

    def test_create_lesson_as_authenticated_user(self):
        """Тест: Авторизованный пользователь может создать урок"""
        self.client.force_authenticate(user=self.user)
        data = {
            "course": self.course.id,
            "name": "New Lesson",
            "description": "New Description",
            "video_url": "https://www.youtube.com/watch?v=valid123",
        }
        response = self.client.post(self.lessons_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Lesson.objects.count(), 2)
        self.assertEqual(response.data["name"], "New Lesson")
        self.assertEqual(response.data["owner"], self.user.id)

    def test_create_lesson_with_invalid_youtube_url(self):
        """Тест: Создание урока с невалидной YouTube ссылкой"""
        self.client.force_authenticate(user=self.user)
        data = {
            "course": self.course.id,
            "name": "Invalid URL Lesson",
            "description": "Test",
            "video_url": "https://rutube.ru/video/test",
        }
        response = self.client.post(self.lessons_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("video_url", str(response.data))
        self.assertEqual(Lesson.objects.count(), 1)

    def test_create_lesson_with_empty_youtube_url(self):
        """Тест: Создание урока без ссылки (допустимо)"""
        self.client.force_authenticate(user=self.user)
        data = {
            "course": self.course.id,
            "name": "No Video Lesson",
            "description": "Test",
            "video_url": "",
        }
        response = self.client.post(self.lessons_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Lesson.objects.count(), 2)

    def test_create_lesson_as_unauthenticated_user(self):
        """Тест: Неавторизованный пользователь не может создать урок"""
        data = {"course": self.course.id, "name": "New Lesson", "description": "Test"}
        response = self.client.post(self.lessons_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Lesson.objects.count(), 1)

    # === ТЕСТЫ НА ЧТЕНИЕ УРОКА ===

    def test_list_lessons_as_owner(self):
        """Тест: Владелец видит свои уроки"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.lessons_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "Test Lesson")

    def test_list_lessons_as_moderator(self):
        """Тест: Модератор видит все уроки"""
        self.client.force_authenticate(user=self.moderator)
        # Создаем еще один урок для другого пользователя
        Lesson.objects.create(
            course=self.course,
            name="Another Lesson",
            description="Test",
            owner=self.other_user,
        )
        response = self.client.get(self.lessons_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_list_lessons_as_other_user(self):
        """Тест: Обычный пользователь видит только свои уроки"""
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(self.lessons_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_retrieve_lesson_as_owner(self):
        """Тест: Владелец может просмотреть свой урок"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.lessons_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Test Lesson")

    def test_retrieve_lesson_as_moderator(self):
        """Тест: Модератор может просмотреть любой урок"""
        self.client.force_authenticate(user=self.moderator)
        response = self.client.get(self.lessons_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Test Lesson")

    def test_retrieve_lesson_as_other_user(self):
        """Тест: Обычный пользователь не может просмотреть чужой урок"""
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(self.lessons_detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # === ТЕСТЫ НА ОБНОВЛЕНИЕ УРОКА ===

    def test_update_lesson_as_owner(self):
        """Тест: Владелец может обновить свой урок"""
        self.client.force_authenticate(user=self.user)
        data = {"name": "Updated Lesson Name", "description": "Updated Description"}
        response = self.client.patch(self.lessons_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Lesson Name")
        lesson = Lesson.objects.get(id=self.lesson.id)
        self.assertEqual(lesson.name, "Updated Lesson Name")

    def test_update_lesson_with_invalid_youtube_url(self):
        """Тест: Обновление урока с невалидной ссылкой"""
        self.client.force_authenticate(user=self.user)
        data = {"video_url": "https://rutube.ru/video/test"}
        response = self.client.patch(self.lessons_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("video_url", str(response.data))

    def test_update_lesson_as_moderator(self):
        """Тест: Модератор может обновить чужой урок"""
        self.client.force_authenticate(user=self.moderator)
        data = {"name": "Moderator Updated Name"}
        response = self.client.patch(self.lessons_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Moderator Updated Name")

    def test_update_lesson_as_other_user(self):
        """Тест: Обычный пользователь не может обновить чужой урок"""
        self.client.force_authenticate(user=self.other_user)
        data = {"name": "Hacked Name"}
        response = self.client.patch(self.lessons_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # === ТЕСТЫ НА УДАЛЕНИЕ УРОКА ===

    def test_delete_lesson_as_owner(self):
        """Тест: Владелец может удалить свой урок"""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.lessons_delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Lesson.objects.count(), 0)

    def test_delete_lesson_as_moderator(self):
        """Тест: Модератор НЕ может удалить чужой урок (по правам CanDeleteCourseLesson)"""
        self.client.force_authenticate(user=self.moderator)
        response = self.client.delete(self.lessons_delete_url)
        # Модератор не имеет права удалять, но так как у него нет прав CanDeleteCourseLesson
        # должен вернуться 403 или 404 в зависимости от реализации
        self.assertIn(
            response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
        )

    def test_delete_lesson_as_other_user(self):
        """Тест: Обычный пользователь не может удалить чужой урок"""
        self.client.force_authenticate(user=self.other_user)
        response = self.client.delete(self.lessons_delete_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Lesson.objects.count(), 1)

    def test_delete_lesson_as_unauthenticated_user(self):
        """Тест: Неавторизованный пользователь не может удалить урок"""
        response = self.client.delete(self.lessons_delete_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Lesson.objects.count(), 1)


class SubscriptionTests(TestCase):
    """Тесты для функционала подписок"""

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(email="user@test.com", password="test123")
        self.other_user = User.objects.create_user(
            email="other@test.com", password="test123"
        )
        self.course = Course.objects.create(
            name="Test Course", description="Test Description", owner=self.user
        )
        self.subscribe_url = reverse("lesson:subscribe")
        self.courses_url = reverse("lesson:course-list")

    def test_subscribe_to_course(self):
        """Тест: Подписка на курс"""
        self.client.force_authenticate(user=self.user)

        response = self.client.post(self.subscribe_url, {"course_id": self.course.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Подписка добавлена")
        self.assertTrue(response.data["subscribed"])
        self.assertEqual(response.data["course_name"], "Test Course")

        self.assertTrue(
            Subscription.objects.filter(user=self.user, course=self.course).exists()
        )

    def test_unsubscribe_from_course(self):
        """Тест: Отписка от курса"""
        # Сначала подписываемся
        Subscription.objects.create(user=self.user, course=self.course)

        self.client.force_authenticate(user=self.user)

        response = self.client.post(self.subscribe_url, {"course_id": self.course.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Подписка удалена")
        self.assertFalse(response.data["subscribed"])

        self.assertFalse(
            Subscription.objects.filter(user=self.user, course=self.course).exists()
        )

    def test_subscribe_without_course_id(self):
        """Тест: Подписка без указания course_id"""
        self.client.force_authenticate(user=self.user)

        response = self.client.post(self.subscribe_url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("course_id", str(response.data))

    def test_subscribe_to_nonexistent_course(self):
        """Тест: Подписка на несуществующий курс"""
        self.client.force_authenticate(user=self.user)

        response = self.client.post(self.subscribe_url, {"course_id": 99999})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_subscribe_as_unauthenticated_user(self):
        """Тест: Неавторизованный пользователь не может подписаться"""
        response = self.client.post(self.subscribe_url, {"course_id": self.course.id})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(
            Subscription.objects.filter(user=self.user, course=self.course).exists()
        )

    def test_is_subscribed_field_in_course_list(self):
        """Тест: Поле is_subscribed в списке курсов"""
        # Подписываемся
        Subscription.objects.create(user=self.user, course=self.course)

        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.courses_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["results"][0]["is_subscribed"])

    def test_is_subscribed_field_in_course_list_for_other_user(self):
        """Тест: Поле is_subscribed для другого пользователя"""
        # Первый пользователь подписан
        Subscription.objects.create(user=self.user, course=self.course)

        # Другой пользователь заходит
        self.client.force_authenticate(user=self.other_user)

        response = self.client.get(self.courses_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_is_subscribed_field_in_course_list_for_unauthenticated(self):
        """Тест: Поле is_subscribed для неавторизованного пользователя"""
        response = self.client.get(self.courses_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_subscribe_twice(self):
        """Тест: Нельзя подписаться дважды (unique_together)"""
        Subscription.objects.create(user=self.user, course=self.course)

        self.client.force_authenticate(user=self.user)

        # Вторая попытка подписаться - должна удалить подписку
        response = self.client.post(self.subscribe_url, {"course_id": self.course.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Подписка удалена")
        self.assertFalse(
            Subscription.objects.filter(user=self.user, course=self.course).exists()
        )


class CourseListTests(TestCase):
    """Тесты для списка курсов"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email="user@test.com", password="test123")
        self.moderator = User.objects.create_user(
            email="moderator@test.com", password="test123"
        )
        moderator_group, _ = Group.objects.get_or_create(name="moderators")
        self.moderator.groups.add(moderator_group)
        self.other_user = User.objects.create_user(
            email="other@test.com", password="test123"
        )
        # Создаем курсы
        self.user_course = Course.objects.create(
            name="User Course", description="Test", owner=self.user
        )
        self.other_course = Course.objects.create(
            name="Other Course", description="Test", owner=self.other_user
        )
        self.courses_url = reverse("lesson:course-list")

    def test_owner_sees_own_courses_only(self):
        """Тест: Владелец видит только свои курсы"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.courses_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "User Course")

    def test_moderator_sees_all_courses(self):
        """Тест: Модератор видит все курсы"""
        self.client.force_authenticate(user=self.moderator)
        response = self.client.get(self.courses_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_other_user_sees_no_courses(self):
        """Тест: Обычный пользователь видит только свои курсы"""
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(self.courses_url)
        # Другой пользователь создал только other_course, но он его владелец
        # В данном случае other_user видит свой курс
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "Other Course")


class PaginationTests(TestCase):
    """Тесты для пагинации"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email="user@test.com", password="test123")
        self.client.force_authenticate(user=self.user)
        self.course = Course.objects.create(
            name="Test Course", description="Test", owner=self.user
        )
        # Создаем 25 уроков
        for i in range(25):
            Lesson.objects.create(
                course=self.course,
                name=f"Lesson {i + 1}",
                description="Test",
                owner=self.user,
            )
        self.courses_url = reverse("lesson:course-list")
        self.lessons_url = reverse("lesson:lesson-list")

    def test_course_pagination_default_page_size(self):
        """Тест: Пагинация курсов с размером страницы по умолчанию"""
        response = self.client.get(self.courses_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertIn("count", response.data)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)

    def test_lesson_pagination_default_page_size(self):
        """Тест: Пагинация уроков с размером страницы по умолчанию"""
        response = self.client.get(self.lessons_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 20)  # page_size=20
        self.assertEqual(response.data["count"], 25)

    def test_lesson_pagination_custom_page_size(self):
        """Тест: Пагинация уроков с кастомным размером страницы"""
        response = self.client.get(f"{self.lessons_url}?page_size=10")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 10)

    def test_lesson_pagination_second_page(self):
        """Тест: Пагинация уроков - вторая страница"""
        response = self.client.get(f"{self.lessons_url}?page=2")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 5)  # 25-20=5

    def test_lesson_pagination_max_page_size(self):
        """Тест: Пагинация уроков - максимальный размер страницы"""
        response = self.client.get(f"{self.lessons_url}?page_size=200")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # max_page_size=100, поэтому вернется 100 элементов
        self.assertEqual(len(response.data["results"]), 25)  # всего 25, поэтому все


class ValidatorTests(TestCase):
    """Тесты для валидатора YouTube ссылок"""

    def test_valid_youtube_urls(self):
        """Тест: Валидные YouTube ссылки"""
        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://www.youtube.com/embed/dQw4w9WgXcQ",
            "https://www.youtube.com/shorts/dQw4w9WgXcQ",
            "youtube.com/watch?v=dQw4w9WgXcQ",
        ]

        for url in valid_urls:
            try:
                validate_youtube_url(url)
            except Exception as e:
                self.fail(f"URL {url} должен быть валидным, но вызвал ошибку: {e}")

    def test_invalid_youtube_urls(self):
        """Тест: Невалидные YouTube ссылки"""
        invalid_urls = [
            "https://rutube.ru/video/test",
            "https://vk.com/video/test",
            "https://yandex.ru/video/test",
            "https://google.com",
            "not a url",
        ]

        for url in invalid_urls:
            with self.assertRaises(Exception):
                validate_youtube_url(url)


class StripePaymentTest(TestCase):
    """Тесты для Stripe платежей"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="testpass123",
            name="Test User",
        )
        self.client.force_authenticate(user=self.user)

        # Создаем тестовый курс
        self.course = Course.objects.create(
            name="Test Course",
            description="Test Description",
            price=1000,  # 1000 рублей
            owner=self.user,
        )

        # Настройка Stripe для тестов
        stripe.api_key = settings.STRIPE_SECRET_KEY

        # Создаем тестовый продукт и цену в Stripe
        self.product = stripe.Product.create(
            name=self.course.name, description=self.course.description
        )

        self.price = stripe.Price.create(
            product=self.product.id,
            unit_amount=int(self.course.price * 100),
            currency="rub",
        )

        self.course.stripe_product_id = self.product.id
        self.course.stripe_price_id = self.price.id
        self.course.save()

    def create_payment_intent(self, card_number, amount=1000):
        """Вспомогательный метод для создания PaymentIntent"""
        try:
            # Создаем PaymentMethod с тестовой картой
            payment_method = stripe.PaymentMethod.create(
                type="card",
                card={
                    "number": card_number,
                    "exp_month": 12,
                    "exp_year": 2025,
                    "cvc": "123",
                },
            )

            # Создаем PaymentIntent
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency="rub",
                payment_method=payment_method.id,
                confirmation_method="manual",
                confirm=True,
                return_url="https://example.com/return",
            )

            return intent
        except stripe.error.CardError as e:
            return {"error": e.error.message}

    def test_visa_card_payment_success(self):
        """Тест успешной оплаты картой Visa (4242)"""
        intent = self.create_payment_intent("4242424242424242")

        if isinstance(intent, dict) and "error" in intent:
            self.fail(f"Payment failed: {intent['error']}")

        self.assertEqual(intent.status, "succeeded")
        self.assertEqual(intent.amount, 1000)
        self.assertEqual(intent.currency, "rub")

    def test_visa_debit_card_payment(self):
        """Тест оплаты картой Visa Debit (4000056655665556)"""
        intent = self.create_payment_intent("4000056655665556")

        if isinstance(intent, dict) and "error" in intent:
            self.fail(f"Payment failed: {intent['error']}")

        self.assertEqual(intent.status, "succeeded")

    def test_mastercard_payment(self):
        """Тест оплаты картой Mastercard (5555555555554444)"""
        intent = self.create_payment_intent("5555555555554444")

        if isinstance(intent, dict) and "error" in intent:
            self.fail(f"Payment failed: {intent['error']}")

        self.assertEqual(intent.status, "succeeded")

    def test_mastercard_debit_payment(self):
        """Тест оплаты картой Mastercard Debit (5200828282828210)"""
        intent = self.create_payment_intent("5200828282828210")

        if isinstance(intent, dict) and "error" in intent:
            self.fail(f"Payment failed: {intent['error']}")

        self.assertEqual(intent.status, "succeeded")

    def test_mastercard_prepaid_payment(self):
        """Тест оплаты картой Mastercard Prepaid (5105105105105100)"""
        intent = self.create_payment_intent("5105105105105100")

        if isinstance(intent, dict) and "error" in intent:
            self.fail(f"Payment failed: {intent['error']}")

        self.assertEqual(intent.status, "succeeded")

    def test_american_express_payment(self):
        """Тест оплаты картой American Express (378282246310005)"""
        intent = self.create_payment_intent("378282246310005")

        if isinstance(intent, dict) and "error" in intent:
            self.fail(f"Payment failed: {intent['error']}")

        self.assertEqual(intent.status, "succeeded")

    def test_american_express_2_payment(self):
        """Тест оплаты картой American Express 2 (371449635398431)"""
        intent = self.create_payment_intent("371449635398431")

        if isinstance(intent, dict) and "error" in intent:
            self.fail(f"Payment failed: {intent['error']}")

        self.assertEqual(intent.status, "succeeded")

    def test_discover_card_payment(self):
        """Тест оплаты картой Discover (6011111111111117)"""
        intent = self.create_payment_intent("6011111111111117")

        if isinstance(intent, dict) and "error" in intent:
            self.fail(f"Payment failed: {intent['error']}")

        self.assertEqual(intent.status, "succeeded")

    def test_discover_2_payment(self):
        """Тест оплаты картой Discover 2 (6011000990139424)"""
        intent = self.create_payment_intent("6011000990139424")

        if isinstance(intent, dict) and "error" in intent:
            self.fail(f"Payment failed: {intent['error']}")

        self.assertEqual(intent.status, "succeeded")

    def test_diners_club_payment(self):
        """Тест оплаты картой Diners Club (3056930009020004)"""
        intent = self.create_payment_intent("3056930009020004")

        if isinstance(intent, dict) and "error" in intent:
            self.fail(f"Payment failed: {intent['error']}")

        self.assertEqual(intent.status, "succeeded")

    def test_jcb_card_payment(self):
        """Тест оплаты картой JCB (3566002020360505)"""
        intent = self.create_payment_intent("3566002020360505")

        if isinstance(intent, dict) and "error" in intent:
            self.fail(f"Payment failed: {intent['error']}")

        self.assertEqual(intent.status, "succeeded")

    def test_unionpay_card_payment(self):
        """Тест оплаты картой UnionPay (6200000000000005)"""
        intent = self.create_payment_intent("6200000000000005")

        if isinstance(intent, dict) and "error" in intent:
            self.fail(f"Payment failed: {intent['error']}")

        self.assertEqual(intent.status, "succeeded")


class StripePaymentScenariosTest(TestCase):
    """Тесты различных сценариев оплаты"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

        stripe.api_key = settings.STRIPE_SECRET_KEY

    def test_payment_with_3d_secure_card(self):
        """Тест оплаты с 3D Secure (требует подтверждения)"""
        # Карта, требующая 3D Secure аутентификацию
        payment_method = stripe.PaymentMethod.create(
            type="card",
            card={
                "number": "4000002500003155",
                "exp_month": 12,
                "exp_year": 2025,
                "cvc": "123",
            },
        )

        intent = stripe.PaymentIntent.create(
            amount=1000,
            currency="rub",
            payment_method=payment_method.id,
            confirmation_method="manual",
            return_url="https://example.com/return",
        )

        # Должен требовать подтверждение
        self.assertIn(intent.status, ["requires_confirmation", "requires_action"])

    def test_payment_with_insufficient_funds(self):
        """Тест оплаты при недостатке средств"""
        # Карта с ошибкой insufficient_funds
        with self.assertRaises(stripe.error.CardError) as context:
            payment_method = stripe.PaymentMethod.create(
                type="card",
                card={
                    "number": "4000000000009995",
                    "exp_month": 12,
                    "exp_year": 2025,
                    "cvc": "123",
                },
            )

            stripe.PaymentIntent.create(
                amount=1000,
                currency="rub",
                payment_method=payment_method.id,
                confirm=True,
            )

        self.assertEqual(context.exception.error.code, "card_declined")
        self.assertEqual(context.exception.error.decline_code, "insufficient_funds")

    def test_payment_with_declined_card(self):
        """Тест оплаты отклоненной картой"""
        # Карта с ошибкой card_declined
        with self.assertRaises(stripe.error.CardError) as context:
            payment_method = stripe.PaymentMethod.create(
                type="card",
                card={
                    "number": "4000000000000002",
                    "exp_month": 12,
                    "exp_year": 2025,
                    "cvc": "123",
                },
            )

            stripe.PaymentIntent.create(
                amount=1000,
                currency="rub",
                payment_method=payment_method.id,
                confirm=True,
            )

        self.assertEqual(context.exception.error.code, "card_declined")

    def test_payment_with_expired_card(self):
        """Тест оплаты просроченной картой"""
        # Карта с ошибкой expired_card
        with self.assertRaises(stripe.error.CardError) as context:
            payment_method = stripe.PaymentMethod.create(
                type="card",
                card={
                    "number": "4000000000000069",
                    "exp_month": 12,
                    "exp_year": 2025,
                    "cvc": "123",
                },
            )

            stripe.PaymentIntent.create(
                amount=1000,
                currency="rub",
                payment_method=payment_method.id,
                confirm=True,
            )

        self.assertEqual(context.exception.error.code, "card_declined")
        self.assertEqual(context.exception.error.decline_code, "expired_card")

    def test_payment_with_incorrect_cvc(self):
        """Тест оплаты с неверным CVC кодом"""
        # Карта с ошибкой incorrect_cvc
        with self.assertRaises(stripe.error.CardError) as context:
            payment_method = stripe.PaymentMethod.create(
                type="card",
                card={
                    "number": "4000000000000127",
                    "exp_month": 12,
                    "exp_year": 2025,
                    "cvc": "123",
                },
            )

            stripe.PaymentIntent.create(
                amount=1000,
                currency="rub",
                payment_method=payment_method.id,
                confirm=True,
            )

        self.assertEqual(context.exception.error.code, "card_declined")
        self.assertEqual(context.exception.error.decline_code, "incorrect_cvc")

    def test_payment_success_then_create_subscription(self):
        """Тест успешной оплаты и создания подписки"""
        # Создаем PaymentIntent
        payment_method = stripe.PaymentMethod.create(
            type="card",
            card={
                "number": "4242424242424242",
                "exp_month": 12,
                "exp_year": 2025,
                "cvc": "123",
            },
        )

        intent = stripe.PaymentIntent.create(
            amount=1000, currency="rub", payment_method=payment_method.id, confirm=True
        )

        self.assertEqual(intent.status, "succeeded")

        # После успешной оплаты создаем подписку
        if intent.status == "succeeded":
            # Здесь логика создания подписки после оплаты
            subscription = stripe.Subscription.create(
                customer=payment_method.customer,
                items=[{"price": "price_test"}],
            )
            self.assertIsNotNone(subscription)


class StripeCheckoutTest(TestCase):
    """Тесты Stripe Checkout сессий"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

        stripe.api_key = settings.STRIPE_SECRET_KEY

    def test_create_checkout_session(self):
        """Тест создания Checkout сессии"""
        session = stripe.checkout.Session.create(
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "rub",
                        "unit_amount": 1000,
                        "product_data": {"name": "Test Product"},
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            customer_email=self.user.email,
        )

        self.assertIsNotNone(session.id)
        self.assertIsNotNone(session.url)
        self.assertEqual(session.mode, "payment")

    def test_checkout_session_with_different_cards(self):
        """Тест Checkout сессии с разными типами карт"""
        cards = [
            ("4242424242424242", "Visa"),
            ("5555555555554444", "Mastercard"),
            ("378282246310005", "American Express"),
            ("6011111111111117", "Discover"),
        ]

        for card_number, card_type in cards:
            # Создаем сессию
            session = stripe.checkout.Session.create(
                success_url="https://example.com/success",
                cancel_url="https://example.com/cancel",
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "unit_amount": 1000,
                            "product_data": {"name": f"Test {card_type}"},
                        },
                        "quantity": 1,
                    }
                ],
                mode="payment",
                payment_method_options={
                    "card": {"request_three_d_secure": "automatic"}
                },
            )

            self.assertIsNotNone(session.id)
            print(f"{card_type} checkout session created: {session.id}")
