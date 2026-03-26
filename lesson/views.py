from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, generics, status
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from .paginators import CoursePagination, LessonPagination

from .serializers import CourseSerializer, LessonListSerializer, LessonDetailSerializer
from .models import Course, Lesson, Subscription
from users.permissions import (
    IsModerator,
    IsOwner,
    IsOwnerOrModerator,
    CanCreateCourseLesson,
    CanDeleteCourseLesson,
)


class CourseViewSet(viewsets.ModelViewSet):
    """ViewSet для курсов с разграничением прав"""

    queryset = Course.objects.all().prefetch_related("lessons")
    serializer_class = CourseSerializer
    pagination_class = CoursePagination

    def get_permissions(self):
        """
        Динамическое определение прав в зависимости от действия
        """
        if self.action in ["list", "retrieve"]:
            permission_classes = [IsAuthenticated]
        elif self.action == "create":
            permission_classes = [IsAuthenticated, CanCreateCourseLesson]
        elif self.action in ["update", "partial_update"]:
            permission_classes = [IsAuthenticated, IsOwnerOrModerator]
        elif self.action == "destroy":
            permission_classes = [IsAuthenticated, CanDeleteCourseLesson]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """При создании автоматически привязываем владельца"""
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        """
        Модераторы видят все курсы, обычные пользователи - только свои
        """
        user = self.request.user
        if not user.is_authenticated:
            return Course.objects.none()

        if user.groups.filter(name="moderators").exists():
            return Course.objects.all().prefetch_related("lessons")
        return Course.objects.filter(owner=user).prefetch_related("lessons")


class LessonListAPIView(generics.ListAPIView):
    """Список уроков"""

    serializer_class = LessonListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    pagination_class = LessonPagination
    filterset_fields = ["course"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name="moderators").exists():
            return Lesson.objects.all()
        return Lesson.objects.filter(owner=user)


class LessonRetrieveAPIView(generics.RetrieveAPIView):
    """Детальный просмотр урока"""

    queryset = Lesson.objects.all()
    serializer_class = LessonDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name="moderators").exists():
            return Lesson.objects.all()
        return Lesson.objects.filter(owner=user)


class LessonCreateAPIView(generics.CreateAPIView):
    """Создание урока"""

    queryset = Lesson.objects.all()
    serializer_class = LessonDetailSerializer
    permission_classes = [IsAuthenticated, CanCreateCourseLesson]

    def perform_create(self, serializer):
        """При создании автоматически привязываем владельца"""
        serializer.save(owner=self.request.user)


class LessonUpdateAPIView(generics.UpdateAPIView):
    """Обновление урока"""

    queryset = Lesson.objects.all()
    serializer_class = LessonDetailSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrModerator]

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name="moderators").exists():
            return Lesson.objects.all()
        return Lesson.objects.filter(owner=user)


class LessonDestroyAPIView(generics.DestroyAPIView):
    """Удаление урока"""

    queryset = Lesson.objects.all()
    serializer_class = LessonDetailSerializer
    permission_classes = [IsAuthenticated, CanDeleteCourseLesson]

    def get_queryset(self):
        """Только владелец может видеть свои уроки для удаления"""
        user = self.request.user
        return Lesson.objects.filter(owner=user)

    def destroy(self, request, *args, **kwargs):
        """Дополнительная проверка при удалении"""
        instance = self.get_object()
        self.check_object_permissions(self.request, instance)
        self.perform_destroy(instance)
        # ИИшка говорит так лучше
        return Response(
            {"message": "Урок успешно удален"}, status=status.HTTP_204_NO_CONTENT
        )


class SubscriptionView(APIView):
    """API для управления подписками на курс"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        course_id = request.data.get("course_id")

        if not course_id:
            return Response(
                {"error": "course_id обязателен"}, status=status.HTTP_400_BAD_REQUEST
            )

        course = get_object_or_404(Course, id=course_id)

        # Проверяем, существует ли подписка
        subscription = Subscription.objects.filter(user=user, course=course)

        if subscription.exists():
            # Если подписка есть - удаляем
            subscription.delete()
            message = "Подписка удалена"
            subscribed = False
        else:
            # Если подписки нет - создаем
            Subscription.objects.create(user=user, course=course)
            message = "Подписка добавлена"
            subscribed = True

        return Response(
            {
                "message": message,
                "subscribed": subscribed,
                "course_id": course.id,
                "course_name": course.name,
            }
        )
