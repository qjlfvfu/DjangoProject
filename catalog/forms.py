from django import forms
from django.core.exceptions import ValidationError
from .models import Product, Category


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'picture', 'category']
        labels = {
            'name': 'Название товара',
            'description': 'Описание товара',
            'category': 'Категория',
            'price': 'Цена',
            'picture': 'Изображение',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    # Задание 1: Список запрещенных слов
    BAD_WORDS = ('казино', 'криптовалюта', 'крипта', 'биржа', 'дешево',
                 'бесплатно', 'обман', 'полиция', 'радар')

    # Задание 3: Стилизация форм
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name == 'description':
                field.widget.attrs.update({
                    'class': 'form-control',
                    'placeholder': 'Введите описание товара...'
                })
            elif field_name == 'picture':
                field.widget.attrs.update({
                    'class': 'form-control'
                })
            else:
                field.widget.attrs.update({
                    'class': 'form-control',
                    'placeholder': f'Введите {field.label.lower()}...'
                })

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            name_lower = name.lower()
            for bad_word in self.BAD_WORDS:
                if bad_word in name_lower:
                    raise ValidationError(
                        f'Название не должно содержать запрещенные слова! Обнаружено: "{bad_word}"'
                    )
        return name

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if description:
            desc_lower = description.lower()
            found_bad_words = []

            for bad_word in self.BAD_WORDS:
                if bad_word in desc_lower:
                    found_bad_words.append(bad_word)

            if found_bad_words:
                raise ValidationError(
                    f'Описание содержит запрещенные слова: {", ".join(found_bad_words)}'
                )
        return description

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None:
            if price < 0:
                raise ValidationError('Цена не может быть отрицательной!')
            if price == 0:
                raise ValidationError('Цена не может быть равна нулю!')
        return price

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        description = cleaned_data.get('description')

        # Проверка, что описание не совпадает с названием
        if name and description and description.lower() == name.lower():
            self.add_error('description', 'Описание не должно совпадать с названием')

        # Проверка на пустое название
        if name and len(name.strip()) == 0:
            self.add_error('name', 'Название не может быть пустым')

        return cleaned_data


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ('name', 'description')
        labels = {
            'name': 'Название категории',
            'description': 'Описание категории'
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    # Задание 3: Стилизация форм
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name == 'description':
                field.widget.attrs.update({
                    'class': 'form-control',
                    'placeholder': 'Введите описание категории...'
                })
            else:
                field.widget.attrs.update({
                    'class': 'form-control',
                    'placeholder': f'Введите {field.label.lower()}...'
                })

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            if len(name.strip()) < 2:
                raise ValidationError('Название категории должно содержать минимум 2 символа')
        return name