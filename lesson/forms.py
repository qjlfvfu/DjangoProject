from black.cache import field
from django import forms
from django.core.exceptions import ValidationError
from .models import Lesson, Course


class LessonForm(forms.ModelForm):
    """Форма для создания Урока"""

    class Meta:
        model = Lesson
        fields = ["name", "description", "preview", "video_link"]
        labels = {
            "name": "Название урока",
            "description": "Описание урока",
            "preview": "Изображение урока",
            "video_link": "ссылка на видеоурок",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            css_class = "form-control"
            if field_name == "description":
                field.widget.attrs.update(
                    {
                        "class": css_class,
                        "placeholder": "Введите описание курса",
                        "rows": 4,
                    }
                )
            elif field_name == "video_link":
                field.widget.attrs.update(
                    {"class": "form-control", "accept": "video/*"}  # Только изображения
                )
            else:
                field.widget.attrs.update(
                    {
                        "class": css_class,
                        "placeholder": f"Введите {field.label.lower()}...",
                    }
                )

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        # Проверка на пустое название
        if name and len(name.strip()) == 0:
            self.add_error("name", "Название урока не может быть пустым")

        return cleaned_data


class CourseForm(forms.ModelForm):
    """Форма для создания Курса"""

    class Meta:
        model = Course
        fields = "__all__"
        labels = {
            "name": "Название Курса",
            "description": "Описание Курса",
            "preview": "Картинка Курса",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Стилизация всех полей
        for field_name, field in self.fields.items():
            # Базовые классы для всех полей
            css_class = "form-control"
            # Специальные классы для разных типов полей
            if field_name == "description":
                field.widget.attrs.update(
                    {
                        "class": css_class,
                        "placeholder": "Введите описание курса",
                        "rows": 4,
                    }
                )
            elif field_name == "preview":
                field.widget.attrs.update(
                    {"class": "form-control", "accept": "image/*"}  # Только изображения
                )
            else:
                field.widget.attrs.update(
                    {
                        "class": css_class,
                        "placeholder": f"Введите {field.label.lower()}...",
                    }
                )

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        # Проверка на пустое название
        if name and len(name.strip()) == 0:
            self.add_error("name", "Название курса не может быть пустым")

        return cleaned_data
