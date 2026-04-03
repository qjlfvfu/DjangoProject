from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, generics, status
from rest_framework.filters import OrderingFilter
from .paginators import CoursePagination, LessonPagination
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .services import StripeService
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
    queryset = Course.objects.all().prefetch_related('lessons')
    serializer_class = CourseSerializer
    pagination_class = CoursePagination

    def get_serializer_context(self):
        """Передаем request в контекст для поля is_subscribed"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    @swagger_auto_schema(
        operation_description="Получить список всех курсов",
        responses={200: CourseSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Создать новый курс",
        request_body=CourseSerializer
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


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


class CreateCheckoutSessionView(APIView):
    """Создание сессии для оплаты курса"""
    permission_classes = [IsAuthenticated]

    def post(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)

        if not course.stripe_price_id:
            product = StripeService.create_product(course)
            if product:
                course.stripe_product_id = product.id
                price = StripeService.create_price(
                    product_id=product.id,
                    amount=int(course.price * 100)
                )
                if price:
                    course.stripe_price_id = price.id
                    course.save()

        if not course.stripe_price_id:
            return Response(
                {"error": "Не удалось создать продукт в Stripe"},
                status=status.HTTP_400_BAD_REQUEST
            )

        success_url = request.data.get('success_url', 'http://localhost:8000/success/')
        cancel_url = request.data.get('cancel_url', 'http://localhost:8000/cancel/')

        session = StripeService.create_checkout_session(
            price_id=course.stripe_price_id,
            success_url=success_url,
            cancel_url=cancel_url
        )

        if session:
            return Response({
                'session_id': session.id,
                'url': session.url
            })
        else:
            return Response(
                {"error": "Не удалось создать сессию оплаты"},
                status=status.HTTP_400_BAD_REQUEST
            )


class CheckoutSessionStatusView(APIView):
    """Получение статуса оплаты"""
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        session = StripeService.get_checkout_session(session_id)
        if session:
            return Response({
                'session_id': session.id,
                'status': session.payment_status,
                'customer_email': session.customer_details.email if session.customer_details else None,
                'amount_total': session.amount_total / 100 if session.amount_total else 0,
                'currency': session.currency,
            })
        return Response(
            {"error": "Сессия не найдена"},
            status=status.HTTP_404_NOT_FOUND
        )