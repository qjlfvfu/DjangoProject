from rest_framework import serializers
import models
from .models import Payment, CustomUser
from lesson.models import Course, Lesson
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer



class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Добавление пользовательских полей в токен
        token['username'] = user.username
        token['email'] = user.email

        return token


class PaymentSerializer(serializers.ModelSerializer):
    """Сериализатор для платежа"""

    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    paid_object = serializers.SerializerMethodField()
    payment_method_display = serializers.CharField(
        source='get_payment_method_display',
        read_only=True
    )

    class Meta:
        model = Payment
        fields = [
            'id',
            'user',
            'user_email',
            'user_name',
            'payment_date',
            'course',
            'lesson',
            'amount',
            'payment_method',
            'payment_method_display',
            'paid_object'
        ]
        read_only_fields = ['payment_date']

    def get_user_name(self, obj):
        """Полное имя пользователя"""
        if obj.user.first_name and obj.user.last_name:
            return f"{obj.user.first_name} {obj.user.last_name}"
        return obj.user.email

    def get_paid_object(self, obj):
        """Детальная информация об оплаченном объекте"""
        if obj.course:
            return {
                'type': 'course',
                'id': obj.course.id,
                'name': obj.course.name,
                'url': f"/lesson/courses/{obj.course.id}/"
            }
        elif obj.lesson:
            return {
                'type': 'lesson',
                'id': obj.lesson.id,
                'name': obj.lesson.title,
                'course_id': obj.lesson.course.id if obj.lesson.course else None,
                'url': f"/lesson/lessons/{obj.lesson.id}/"
            }
        return None


class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор профиля пользователя с историей платежей"""

    payments = PaymentSerializer(many=True, read_only=True)
    payments_count = serializers.IntegerField(source='payments.count', read_only=True)
    total_spent = serializers.SerializerMethodField()
    last_payment = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'city',
            'phone_number',
            'avatar',
            'date_joined',
            'payments_count',
            'total_spent',
            'last_payment',
            'payments'
        ]

    def get_total_spent(self, obj):
        """Общая сумма потраченная пользователем"""
        total = obj.payments.aggregate(total=models.Sum('amount'))['total']
        return float(total) if total else 0

    def get_last_payment(self, obj):
        """Последний платеж пользователя"""
        last = obj.payments.order_by('-payment_date').first()
        if last:
            return {
                'date': last.payment_date,
                'amount': float(last.amount),
                'method': last.get_payment_method_display()
            }
        return None