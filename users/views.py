from rest_framework import generics, status
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly,
    IsAuthenticated,
    AllowAny,
)
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from .models import Payment
from .serializers import (
    MyTokenObtainPairSerializer,
    PaymentSerializer,
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
)
from rest_framework_simplejwt.views import TokenObtainPairView

User = get_user_model()


# ========== JWT Токены ==========
class MyTokenObtainPairView(TokenObtainPairView):
    """Получение JWT токена"""

    serializer_class = MyTokenObtainPairSerializer


# ========== CRUD для пользователей ==========
class UserListAPIView(generics.ListAPIView):
    """Список всех пользователей (только для админов)"""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Админы видят всех, обычные пользователи - только себя
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)


class UserRetrieveAPIView(generics.RetrieveAPIView):
    """Детальная информация о пользователе"""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Если передан 'me', возвращаем текущего пользователя
        if self.kwargs.get("pk") == "me":
            return self.request.user
        return super().get_object()


class UserCreateAPIView(generics.CreateAPIView):
    """Регистрация нового пользователя"""

    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Генерируем токены для нового пользователя
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "user": UserSerializer(user).data,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_201_CREATED,
        )


class UserUpdateAPIView(generics.UpdateAPIView):
    """Обновление информации о пользователе"""

    queryset = User.objects.all()
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Пользователь может редактировать только свой профиль
        return User.objects.filter(id=self.request.user.id)


class UserDestroyAPIView(generics.DestroyAPIView):
    """Удаление пользователя"""

    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Пользователь может удалить только свой профиль
        return User.objects.filter(id=self.request.user.id)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "Пользователь успешно удален"},
            status=status.HTTP_204_NO_CONTENT,
        )


# ========== Платежи ==========
class PaymentListAPIView(generics.ListAPIView):
    """API для списка платежей с фильтрацией прямо во вьюхе"""

    queryset = Payment.objects.select_related("user", "course", "lesson").all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = {
        "payment_method": ["exact"],
        "course": ["exact"],
        "lesson": ["exact"],
        "user": ["exact"],
        "payment_date": ["year", "month", "day", "gte", "lte"],
        "amount": ["gte", "lte", "exact"],
    }

    ordering_fields = ["payment_date", "amount"]
    ordering = ["-payment_date"]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params

        # Фильтр по дате (диапазон)
        date_from = params.get("date_from")
        if date_from:
            queryset = queryset.filter(payment_date__gte=date_from)

        date_to = params.get("date_to")
        if date_to:
            queryset = queryset.filter(payment_date__lte=date_to)

        # Фильтр по курсу
        course_id = params.get("course_id")
        if course_id:
            queryset = queryset.filter(course_id=course_id)

        course_name = params.get("course_name")
        if course_name:
            queryset = queryset.filter(course__name__icontains=course_name)

        # Фильтр по уроку
        lesson_id = params.get("lesson_id")
        if lesson_id:
            queryset = queryset.filter(lesson_id=lesson_id)

        lesson_title = params.get("lesson_title")
        if lesson_title:
            queryset = queryset.filter(lesson__title__icontains=lesson_title)

        # Фильтр по способу оплаты
        payment_method = params.get("payment_method")
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)

        # Фильтр по пользователю
        user_id = params.get("user_id")
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        user_email = params.get("user_email")
        if user_email:
            queryset = queryset.filter(user__email__icontains=user_email)

        # Фильтр по сумме
        min_amount = params.get("min_amount")
        if min_amount:
            queryset = queryset.filter(amount__gte=min_amount)

        max_amount = params.get("max_amount")
        if max_amount:
            queryset = queryset.filter(amount__lte=max_amount)

        # Фильтр по типу оплаченного объекта
        paid_type = params.get("paid_type")
        if paid_type == "course":
            queryset = queryset.filter(course__isnull=False)
        elif paid_type == "lesson":
            queryset = queryset.filter(lesson__isnull=False)

        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)

        response.data = {
            "count": (
                len(response.data)
                if isinstance(response.data, list)
                else response.data.get("count", 0)
            ),
            "filters_applied": dict(request.query_params),
            "results": (
                response.data
                if isinstance(response.data, list)
                else response.data.get("results", [])
            ),
        }

        return response
