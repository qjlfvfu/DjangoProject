from django.conf import settings
from django.core.mail import send_mail
from django.db import models
from django.template.defaultfilters import slugify
from django.urls import reverse


class Blog(models.Model):
    """Модель блоговой записи"""

    # Обязательные поля по заданию
    name = models.CharField(
        max_length=50, verbose_name="Заголовок", help_text="Введите заголовок статьи"
    )

    description = models.TextField(
        verbose_name="Содержимое", help_text="Введите содержимое статьи"
    )

    preview = models.ImageField(
        upload_to="blog/previews/%Y/%m/%d/",
        verbose_name="Превью",
        null=True,
        blank=True,
        help_text="Загрузите изображение для превью",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    is_published = models.BooleanField(
        default=False,
        verbose_name="Признак публикации",
        help_text="Отметьте для публикации статьи",
    )

    views_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Количество просмотров",
        help_text="Количество просмотров статьи",
        editable=False,
    )

    slug = models.SlugField(
        max_length=250,
        unique=True,
        blank=True,
        verbose_name="URL",
        help_text="Автоматически заполняется из заголовка",
    )

    class Meta:
        verbose_name = "Блоговая запись"
        verbose_name_plural = "Блоговые записи"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["is_published"]),
        ]

    def __str__(self):
        return f'{self.name} ({self.created_at.strftime("%d.%m.%Y")})'

    def save(self, *args, **kwargs):
        """Автоматическое создание slug"""
        if not self.slug:
            # Генерируем уникальный slug
            base_slug = slugify(self.name)[:250]
            self.slug = base_slug

            # Делаем slug уникальным, если нужно
            counter = 1
            while Blog.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """URL для детального просмотра"""
        return reverse("blog:blog_detail", kwargs={"slug": self.slug})

    def increment_views(self):
        """Увеличивает счетчик просмотров на 1 и проверяет достижение 100 просмотров"""
        old_views = self.views_count
        self.views_count += 1

        # Сохраняем и проверяем достижение 100 просмотров
        self.save(update_fields=["views_count"])

        # Отправляем email при достижении 100 просмотров
        if old_views < 100 and self.views_count >= 100:
            self.send_congratulation_email()

    def send_congratulation_email(self):
        """Отправляет email при достижении 100 просмотров"""
        subject = f'🎉 Поздравление! Статья "{self.name}" достигла 100 просмотров!'
        message = f"""
        Поздравляем!

        Ваша статья "{self.name}" достигла 100 просмотров!

        URL статьи: http://127.0.0.1:8000{self.get_absolute_url()}
        Количество просмотров: {self.views_count}
        Дата создания: {self.created_at.strftime("%d.%m.%Y %H:%M")}

        Продолжайте в том же духе!
        """

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.DEFAULT_FROM_EMAIL],
                fail_silently=True,
            )
        except Exception as e:
            # Логируем ошибку, но не прерываем выполнение
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Ошибка отправки email: {e}")

    @property
    def reading_time(self):
        """Возвращает примерное время чтения в минутах"""
        words_per_minute = 200
        word_count = len(self.description.split())
        reading_time = max(1, word_count // words_per_minute)
        return f"{reading_time} мин."

    @property
    def short_description(self):
        """Возвращает укороченное описание (первые 100 символов)"""
        if len(self.description) > 100:
            return self.description[:100] + "..."
        return self.descriptio
