import re
from django.core.exceptions import ValidationError
from rest_framework import serializers


def validate_youtube_url(value):
    """
    Валидатор для проверки, что ссылка ведет на youtube.com
    """
    if not value:
        return value

    # Регулярное выражение для проверки YouTube ссылок
    youtube_patterns = [
        r"(https?://)?(www\.)?youtube\.com/watch\?v=[\w-]+",
        r"(https?://)?(www\.)?youtu\.be/[\w-]+",
        r"(https?://)?(www\.)?youtube\.com/embed/[\w-]+",
        r"(https?://)?(www\.)?youtube\.com/shorts/[\w-]+",
    ]

    for pattern in youtube_patterns:
        if re.match(pattern, value, re.IGNORECASE):
            return value

    raise ValidationError("Разрешены только ссылки на YouTube (youtube.com, youtu.be)")


class YouTubeURLValidator:
    """
    Класс-валидатор для проверки YouTube ссылок
    """

    def __init__(self, field="video_url"):
        self.field = field

    def __call__(self, attrs):
        value = attrs.get(self.field)
        if value:
            validate_youtube_url(value)
        return attrs
