from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Payment, CustomUser
from lesson.models import Course, Lesson
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.db import models

User = get_user_model()


# ========== JWT ==========
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Кастомный сериализатор для JWT токена"""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Добавление пользовательских полей в токен
        token['username'] = user.username
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['is_moderator'] = user.groups.filter(name='moderators').exists()

        return token


# ========== Базовые сериализаторы пользователя ==========
class UserSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для пользователя"""

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'city', 'phone_number', 'avatar']
        read_only_fields = ['id']


class UserDetailSerializer(serializers.ModelSerializer):
    """Детальный сериализатор пользователя"""
    is_moderator = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'city', 'phone_number', 'avatar', 'date_joined', 'is_moderator'
        ]
        read_only_fields = ['id', 'date_joined']

    def get_is_moderator(self, obj):
        return obj.groups.filter(name='moderators').exists()

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.email


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации пользователя"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'password2', 'first_name', 'last_name', 'city', 'phone_number']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        # Создаем username из email (если нет username в модели)
        validated_data['username'] = validated_data['email'].split('@')[0]
        user = User.objects.create_user(**validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления профиля"""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'city', 'phone_number', 'avatar']


# ========== Платежи ==========
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


# ========== Профиль пользователя с платежами ==========
class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор профиля пользователя с историей платежей"""
    payments = PaymentSerializer(many=True, read_only=True)
    payments_count = serializers.IntegerField(source='payments.count', read_only=True)
    total_spent = serializers.SerializerMethodField()
    last_payment = serializers.SerializerMethodField()
    is_moderator = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id',
            'email',
            'full_name',
            'first_name',
            'last_name',
            'city',
            'phone_number',
            'avatar',
            'date_joined',
            'is_moderator',
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

    def get_is_moderator(self, obj):
        return obj.groups.filter(name='moderators').exists()

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.email


class PublicUserProfileSerializer(serializers.ModelSerializer):
    """
    Публичный сериализатор для просмотра чужих профилей
    (без конфиденциальной информации)
    """
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'full_name', 'city', 'avatar']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.email