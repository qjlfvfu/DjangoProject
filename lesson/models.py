from django.db import models
from django.conf import settings

from lesson.validators import validate_youtube_url


class Course(models.Model):
    """Модель курсов"""

    objects = None
    name = models.CharField(max_length=255, verbose_name="Название")
    preview = models.ImageField(
        upload_to="courses/", blank=True, null=True, verbose_name="Превью"
    )
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        verbose_name="Создатель курса",
        null=True,
        blank=True,
        related_name="courses",
    )
    price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Цена (в рублях)"
    )
    stripe_product_id = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Stripe Product ID"
    )
    stripe_price_id = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Stripe Price ID"
    )
    last_notification_sent = models.DateTimeField(
        null=True, blank=True, verbose_name="Последнее уведомление отправлено"
    )

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"

    def __str__(self):
        return self.name


class Lesson(models.Model):
    """Модель уроков"""

    objects = None
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    name = models.CharField(max_length=200, verbose_name="Название урока")
    description = models.TextField(verbose_name="Описание", blank=True)
    video_url = models.URLField(
        verbose_name="Ссылка на видео",
        blank=True,
        null=True,
        validators=[validate_youtube_url],  # Добавляем валидатор
    )
    owner = models.ForeignKey(
        "users.CustomUser", on_delete=models.CASCADE, related_name="lessons"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    preview = models.ImageField(
        upload_to="lessons/", blank=True, null=True, verbose_name="Превью"
    )
    video_link = models.URLField(blank=True, null=True, verbose_name="Ссылка на видео")

    class Meta:
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"

    def __str__(self):
        return self.name


class Subscription(models.Model):
    """Модель подписки на обновления курса"""

    objects = None
    user = models.ForeignKey(
        "users.CustomUser",
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name="subscriptions",
    )
    course = models.ForeignKey(
        "Course",
        on_delete=models.CASCADE,
        verbose_name="Курс",
        related_name="subscribers",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата подписки")
    is_paid = models.BooleanField(default=False)

    class Meta:
        unique_together = ["user", "course"]
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"

    def __str__(self):
        return f"{self.user.email} -> {self.course.name}"
