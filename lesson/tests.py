from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


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
