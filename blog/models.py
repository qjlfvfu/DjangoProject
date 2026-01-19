from django.db import models
from django.db.models import CharField


# Create your models here.
from django.db import models
from django.template.defaultfilters import slugify
from django.urls import reverse


class Blog(models.Model):
    """Модель блоговой записи"""

    # Обязательные поля по заданию
    name = models.CharField(
        max_length=50,
        verbose_name="Заголовок",
        help_text="Введите заголовок статьи"
    )

    description = models.TextField(
        verbose_name="Содержимое",
        help_text="Введите содержимое статьи"
    )

    preview = models.ImageField(
        upload_to='blog/previews/%Y/%m/%d/',
        verbose_name="Превью",
        null=True,
        blank=True,
        help_text="Загрузите изображение для превью"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )

    is_published = models.BooleanField(
        default=False,
        verbose_name="Признак публикации",
        help_text="Отметьте для публикации статьи"
    )

    views_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Количество просмотров",
        help_text="Количество просмотров статьи",
        editable=False  # Не редактируется вручную
    )

    slug = models.SlugField(
        max_length=250,
        unique=True,
        blank=True,
        verbose_name="URL",
        help_text="Автоматически заполняется из заголовка"
    )


class Meta:
    verbose_name = "Блоговая запись"
    verbose_name_plural = "Блоговые записи"
    ordering = ['-created_at']
    indexes = [
        models.Index(fields=['slug']),
        models.Index(fields=['created_at']),
        models.Index(fields=['is_published']),
    ]

def __str__(self):
    return f'{self.name} ({self.created_at.strftime("%d.%m.%Y")})'

def save(self, *args, **kwargs):
    """Автоматическое создание slug и проверка достижения 100 просмотров"""
    if not self.slug:
        self.slug = slugify(self.name)[:250]

    # Проверяем, достигнуто ли 100 просмотров
    if self.pk:  # Если запись уже существует
        old_views = Blog.objects.get(pk=self.pk).views_count
        if old_views < 100 and self.views_count >= 100:
            self.send_congratulation_email()

    super().save(*args, **kwargs)

def get_absolute_url(self):
    """URL для детального просмотра"""
    return reverse('blog:blog_detail', kwargs={'slug': self.slug})

def increment_views(self):
    """Увеличивает счетчик просмотров на 1"""
    self.views_count += 1
    self.save(update_fields=['views_count'])

def send_congratulation_email(self):
    """Отправляет email при достижении 100 просмотров (дополнительное задание)"""
    from django.core.mail import send_mail
    from django.conf import settings

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
            recipient_list=[settings.DEFAULT_FROM_EMAIL],  # Отправляем Достижение
            fail_silently=True,
        )
    except Exception as e:
        # Логируем ошибку, но не прерываем выполнение
        print(f"Ошибка отправки email: {e}")

@property
def reading_time(self):
    """Возвращает примерное время чтения в минутах"""
    words_per_minute = 200
    word_count = len(self.description.split())
    reading_time = max(1, word_count // words_per_minute)
    return f"{reading_time} мин."