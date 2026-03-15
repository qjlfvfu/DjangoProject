# users/views.py
from rest_framework import generics, filters
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from .models import Payment
from .serializers import MyTokenObtainPairSerializer, PaymentSerializer
from rest_framework_simplejwt.views import TokenObtainPairView



class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer



class PaymentListAPIView(generics.ListAPIView):
    """API для списка платежей с фильтрацией прямо во вьюхе"""

    queryset = Payment.objects.select_related('user', 'course', 'lesson').all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend,OrderingFilter,]
    filterset_fields = {
        'payment_method': ['exact'],
        'course': ['exact'],
        'lesson': ['exact'],
        'user': ['exact'],
        'payment_date': ['year', 'month', 'day', 'gte', 'lte'],
        'amount': ['gte', 'lte', 'exact'],
    }

    ordering_fields = ['payment_date', 'amount']
    ordering = ['-payment_date']

    def get_queryset(self):
        """
        Переопределяем get_queryset для кастомной фильтрации
        """
        queryset = super().get_queryset()

        # Получаем параметры из запроса
        params = self.request.query_params

        # Фильтр по дате (диапазон)
        date_from = params.get('date_from')
        if date_from:
            queryset = queryset.filter(payment_date__gte=date_from)

        date_to = params.get('date_to')
        if date_to:
            queryset = queryset.filter(payment_date__lte=date_to)

        # Фильтр по курсу (можно по ID или части названия)
        course_id = params.get('course_id')
        if course_id:
            queryset = queryset.filter(course_id=course_id)

        course_name = params.get('course_name')
        if course_name:
            queryset = queryset.filter(course__name__icontains=course_name)

        # Фильтр по уроку
        lesson_id = params.get('lesson_id')
        if lesson_id:
            queryset = queryset.filter(lesson_id=lesson_id)

        lesson_title = params.get('lesson_title')
        if lesson_title:
            queryset = queryset.filter(lesson__title__icontains=lesson_title)

        # Фильтр по способу оплаты
        payment_method = params.get('payment_method')
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)

        # Фильтр по пользователю
        user_id = params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        user_email = params.get('user_email')
        if user_email:
            queryset = queryset.filter(user__email__icontains=user_email)

        # Фильтр по сумме
        min_amount = params.get('min_amount')
        if min_amount:
            queryset = queryset.filter(amount__gte=min_amount)

        max_amount = params.get('max_amount')
        if max_amount:
            queryset = queryset.filter(amount__lte=max_amount)

        # Фильтр по типу оплаченного объекта
        paid_type = params.get('paid_type')
        if paid_type == 'course':
            queryset = queryset.filter(course__isnull=False)
        elif paid_type == 'lesson':
            queryset = queryset.filter(lesson__isnull=False)

        return queryset

    def list(self, request, *args, **kwargs):
        """Добавляем информацию о примененных фильтрах в ответ"""
        response = super().list(request, *args, **kwargs)

        response.data = {
            'count': len(response.data) if isinstance(response.data, list) else response.data.get('count', 0),
            'filters_applied': dict(request.query_params),
            'results': response.data if isinstance(response.data, list) else response.data.get('results', [])
        }

        return response