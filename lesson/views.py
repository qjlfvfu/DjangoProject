import stripe
from django.conf import settings
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
from .serializers import (
    CourseSerializer,
    LessonListSerializer,
    LessonDetailSerializer,
    StripeSessionSerializer,
)
from django.utils import timezone
from datetime import timedelta
from users.tasks import notify_course_subscribers
from .models import Course, Lesson, Subscription
from users.permissions import (
    IsOwnerOrModerator,
    CanCreateCourseLesson,
    CanDeleteCourseLesson,
)


class CourseViewSet(viewsets.ModelViewSet):
    """ViewSet для курсов с разграничением прав"""

    queryset = Course.objects.all().prefetch_related("lessons")
    serializer_class = CourseSerializer
    pagination_class = CoursePagination

    def get_serializer_context(self):
        """Передаем request в контекст для поля is_subscribed"""
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    @swagger_auto_schema(
        operation_description="Получить список всех курсов",
        responses={200: CourseSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Создать новый курс", request_body=CourseSerializer
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

    def update(self, request, *args, **kwargs):
        """
        Обновление курса с отправкой уведомлений подписчикам
        """
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        # Сохраняем старые значения для сравнения
        old_name = instance.name
        old_description = instance.description

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Проверяем, были ли изменения
        has_changes = (
            old_name != instance.name or old_description != instance.description
        )

        if has_changes:
            # Дополнительное задание: проверка времени с последнего уведомления
            now = timezone.now()
            four_hours_ago = now - timedelta(hours=4)

            # Отправляем уведомление, если прошло более 4 часов или уведомление не отправлялось
            if (
                instance.last_notification_sent is None
                or instance.last_notification_sent < four_hours_ago
            ):
                # Асинхронная отправка уведомлений подписчикам
                notify_course_subscribers.delay(
                    course_id=instance.id,
                    course_name=instance.name,
                    updated_fields=["name", "description"] if has_changes else None,
                )

                # Обновляем время последнего уведомления
                instance.last_notification_sent = now
                instance.save(update_fields=["last_notification_sent"])

        return Response(serializer.data)

    def perform_update(self, serializer):
        """Обновление курса"""
        serializer.save()


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
        if getattr(self, "swagger_fake_view", False):
            return Lesson.objects.none()
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
        # Добавьте проверку для Swagger
        if getattr(self, "swagger_fake_view", False):
            return Lesson.objects.none()

        user = self.request.user
        if not user.is_authenticated:
            return Lesson.objects.none()

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
        # Добавьте проверку для Swagger
        if getattr(self, "swagger_fake_view", False):
            return Lesson.objects.none()

        user = self.request.user
        if not user.is_authenticated:
            return Lesson.objects.none()

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
        # Добавьте проверку для Swagger
        if getattr(self, "swagger_fake_view", False):
            return Lesson.objects.none()

        user = self.request.user
        if not user.is_authenticated:
            return Lesson.objects.none()

        return Lesson.objects.filter(owner=user)


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

    @swagger_auto_schema(
        request_body=StripeSessionSerializer, responses={201: StripeSessionSerializer()}
    )
    def post(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        # Проверяем, не купил ли уже пользователь курс
        if Subscription.objects.filter(
            user=request.user, course=course, is_paid=True
        ).exists():
            return Response(
                {"error": "Вы уже приобрели этот курс"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Создаем продукт и цену, если их нет
        if not course.stripe_price_id:
            product = StripeService.create_product(course)
            if product:
                course.stripe_product_id = product.id
                # Используем цену из курса или значение по умолчанию
                amount = (
                    int(course.price * 100) if course.price else 100000
                )  # 1000 руб по умолчанию
                price = StripeService.create_price(
                    product_id=product.id, amount=amount, currency="rub"
                )
                if price:
                    course.stripe_price_id = price.id
                    course.save()
                else:
                    return Response(
                        {"error": "Не удалось создать цену в Stripe"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                return Response(
                    {"error": "Не удалось создать продукт в Stripe"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Формируем URL для успешной оплаты и отмены
        success_url = request.data.get(
            "success_url", request.build_absolute_uri("/payment/success/")
        )
        cancel_url = request.data.get(
            "cancel_url", request.build_absolute_uri("/payment/cancel/")
        )

        # Создаем сессию с metadata
        session = StripeService.create_checkout_session(
            price_id=course.stripe_price_id,
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "course_id": course.id,
                "user_id": request.user.id,
                "course_name": course.name,
            },
        )

        if session:
            return Response(
                {
                    "session_id": session.id,
                    "url": session.url,
                    "course_id": course.id,
                    "course_name": course.name,
                    "amount": float(course.price) if course.price else 1000,
                },
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                {"error": "Не удалось создать сессию оплаты"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class CheckoutSessionStatusView(APIView):
    """Получение статуса оплаты"""

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(responses={200: StripeSessionSerializer()})
    def get(self, request, session_id):
        session = StripeService.get_checkout_session(session_id)
        if session:
            return Response(
                {
                    "session_id": session.id,
                    "status": session.payment_status,
                    "customer_email": (
                        session.customer_details.email
                        if session.customer_details
                        else None
                    ),
                    "amount_total": (
                        session.amount_total / 100 if session.amount_total else 0
                    ),
                    "currency": session.currency,
                }
            )
        return Response(
            {"error": "Сессия не найдена"}, status=status.HTTP_404_NOT_FOUND
        )


class CreateStripeProductPriceView(APIView):
    """Создание продукта и цены в Stripe"""

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(responses={201: "Продукт создан"})
    def post(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)

        # Проверка прав
        if not request.user.is_staff and course.owner != request.user:
            return Response(
                {"error": "У вас нет прав на это действие"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Создаем продукт
        product = StripeService.create_product(course)
        if not product:
            return Response(
                {"error": "Не удалось создать продукт в Stripe"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        course.stripe_product_id = product.id

        # Создаем цену (если есть цена)
        if course.price:
            price = StripeService.create_price(
                product_id=product.id,
                amount=int(course.price * 100),  # переводим в копейки
                currency="rub",
            )
            if price:
                course.stripe_price_id = price.id

        course.save()

        return Response(
            {
                "success": True,
                "product_id": course.stripe_product_id,
                "price_id": course.stripe_price_id,
                "course_id": course.id,
                "course_name": course.name,
                "price": float(course.price) if course.price else None,
            },
            status=status.HTTP_201_CREATED,
        )


class SimpleCheckoutSessionView(APIView):
    """Простое создание Stripe Checkout сессии"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY

            # Получаем данные из запроса
            price_id = request.data.get("price_id")
            quantity = request.data.get("quantity", 1)
            success_url = request.data.get("success_url", "https://example.com/success")
            cancel_url = request.data.get("cancel_url", "https://example.com/cancel")

            if not price_id:
                return Response(
                    {"error": "price_id обязателен"}, status=status.HTTP_400_BAD_REQUEST
                )

            # Создаем сессию (как в PHP)
            session = stripe.checkout.Session.create(
                success_url=success_url,
                cancel_url=cancel_url,
                line_items=[
                    {
                        "price": price_id,
                        "quantity": quantity,
                    },
                ],
                mode="payment",  # 'payment', 'subscription', или 'setup'
                metadata={"user_id": request.user.id, "user_email": request.user.email},
            )

            return Response(
                {
                    "session_id": session.id,
                    "url": session.url,
                    "status": session.status,
                },
                status=status.HTTP_201_CREATED,
            )

        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CreateCheckoutForSubscriptionView(APIView):
    """Создание Checkout сессии для подписки"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Создаем цену подписки
            price = stripe.Price.create(
                currency="usd",
                unit_amount=1000,
                recurring={"interval": "month"},
                product_data={"name": "Gold Plan"},
            )

            # Создаем Checkout сессию
            checkout_session = stripe.checkout.Session.create(
                success_url="https://example.com/success",
                cancel_url="https://example.com/cancel",
                payment_method_types=["card"],
                line_items=[
                    {
                        "price": price.id,
                        "quantity": 1,
                    },
                ],
                mode="subscription",  # Важно: mode = subscription
                customer_email=request.user.email,
                metadata={"user_id": request.user.id, "plan": "gold"},
            )

            return Response(
                {
                    "session_id": checkout_session.id,
                    "url": checkout_session.url,
                    "price_id": price.id,
                },
                status=status.HTTP_201_CREATED,
            )

        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BADDRESS)


class DeleteStripeProductView(APIView):
    """Удаление продукта в Stripe"""

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(responses={200: "Продукт удален"})
    def delete(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)

        # Проверка прав
        if not request.user.is_staff and course.owner != request.user:
            return Response(
                {"error": "У вас нет прав на это действие"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            if course.stripe_product_id:
                # Деактивируем продукт (не удаляем полностью, чтобы не сломать историю)
                stripe.Product.modify(course.stripe_product_id, active=False)

            if course.stripe_price_id:
                # Деактивируем цену
                stripe.Price.modify(course.stripe_price_id, active=False)

            course.stripe_product_id = None
            course.stripe_price_id = None
            course.save()

            return Response(
                {"success": True, "message": "Продукт деактивирован в Stripe"},
                status=status.HTTP_200_OK,
            )

        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class WebhookStripeView(APIView):
    """Вебхук для обработки событий Stripe"""

    permission_classes = []

    @swagger_auto_schema(auto_schema=None)  # Отключаем для вебхука
    def post(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            return Response(
                {"error": "Invalid payload"}, status=status.HTTP_400_BAD_REQUEST
            )
        except stripe.error.SignatureVerificationError:
            return Response(
                {"error": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Обработка события успешной оплаты
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]

            # Получаем информацию о курсе из metadata
            course_id = session.get("metadata", {}).get("course_id")
            user_id = session.get("metadata", {}).get("user_id")

            if course_id and user_id:
                # Создаем запись о покупке или активируем доступ
                from users.models import User

                try:
                    course = Course.objects.get(id=course_id)
                    user = User.objects.get(id=user_id)

                    # Создаем подписку на курс после оплаты
                    Subscription.objects.get_or_create(
                        user=user, course=course, defaults={"is_paid": True}
                    )

                    print(
                        f"Курс {course.name} успешно куплен пользователем {user.email}"
                    )
                except (Course.DoesNotExist, User.DoesNotExist):
                    print(f"Не найден курс {course_id} или пользователь {user_id}")
        return Response({"status": "success"}, status=status.HTTP_200_OK)


class CreateSubscriptionPriceView(APIView):
    """Создание цены для подписки в Stripe"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Создаем цену для подписки (как в PHP)
            price = stripe.Price.create(
                currency="usd",
                unit_amount=1000,  # 1000 центов = $10.00
                recurring={
                    "interval": "month",  # 'month', 'year', 'week', 'day'
                },
                product_data={
                    "name": "Gold Plan",
                    "description": "Премиум подписка на Gold Plan",
                },
            )

            return Response(
                {
                    "success": True,
                    "price_id": price.id,
                    "currency": price.currency,
                    "unit_amount": price.unit_amount,
                    "recurring_interval": price.recurring["interval"],
                    "product_name": price.product_data["name"],
                },
                status=status.HTTP_201_CREATED,
            )

        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CreateSubscriptionPriceWithProductView(APIView):
    """Создание продукта и цены для подписки"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Сначала создаем продукт
            product = stripe.Product.create(
                name="Gold Plan",
                description="Премиум подписка",
                metadata={"type": "subscription", "tier": "gold"},
            )

            # Затем создаем цену для продукта
            price = stripe.Price.create(
                product=product.id,
                currency="usd",
                unit_amount=1000,  # $10.00
                recurring={
                    "interval": "month",
                },
                metadata={"plan_type": "premium"},
            )

            return Response(
                {
                    "success": True,
                    "product_id": product.id,
                    "product_name": product.name,
                    "price_id": price.id,
                    "amount": price.unit_amount / 100,  # переводим в доллары
                    "currency": price.currency,
                    "interval": price.recurring["interval"],
                },
                status=status.HTTP_201_CREATED,
            )

        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
