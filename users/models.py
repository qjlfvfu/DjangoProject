from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models

from lesson.models import Course, Lesson


# Create your models here.
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)

        # АВТОМАТИЧЕСКИ СОЗДАЕМ USERNAME из email больше никак не вышло
        if "username" not in extra_fields or not extra_fields.get("username"):
            # Берем часть email до @ и убираем спецсимволы
            username = email.split("@")[0]
            # Убираем точки, дефисы и т.д.
            username = "".join(c for c in username if c.isalnum())
            if not username:
                username = f"user_{email[:8].replace('@', '')}"
            extra_fields["username"] = username

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    country = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Страна"
    )
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


class Payment(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH = "cash", "Наличные"
        TRANSFER = "transfer", "Перевод на счет"
        CARD = "card", "Банковская карта"

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="плательщик",
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
        verbose_name="оплаченный курс",
    )

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
        verbose_name="оплаченный урок",
    )

    amount = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="сумма оплаты"
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
        verbose_name="способ оплаты",
    )

    payment_date = models.DateTimeField(auto_now_add=True, verbose_name="дата оплаты")

    class Meta:
        verbose_name = "платеж"
        verbose_name_plural = "платежи"
        ordering = ["-payment_date"]  # сначала новые

    def __str__(self):
        return f'{self.user} - {self.amount} руб. ({self.payment_date.strftime("%d.%m.%Y")})'

    def get_paid_object(self):
        """Возвращает объект, за который произведена оплата (курс или урок)"""
        if self.course:
            return self.course
        elif self.lesson:
            return self.lesson
        return None

    def get_paid_object_name(self):
        """Возвращает название оплаченного объекта"""
        obj = self.get_paid_object()
        return str(obj) if obj else "Не указано"
