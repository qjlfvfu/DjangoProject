from django import forms
from django.contrib.auth.forms import (
    UserCreationForm,
    AuthenticationForm,
    PasswordChangeForm,
)
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from .models import CustomUser


class UserRegisterForm(UserCreationForm):
    """Форма регистрации пользователя"""

    email = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "example@mail.com",
                "autocomplete": "email",
            }
        ),
    )
    username = forms.CharField(
        label=_("Имя пользователя"),
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ваш логин (необязательно)",
                "autocomplete": "username",
            }
        ),
    )
    first_name = forms.CharField(
        label=_("Имя"),
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Ваше имя"}
        ),
    )
    last_name = forms.CharField(
        label=_("Фамилия"),
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Ваша фамилия"}
        ),
    )
    phone = forms.CharField(
        label=_("Телефон"),
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "+7 (999) 123-45-67"}
        ),
    )
    password1 = forms.CharField(
        label=_("Пароль"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Введите пароль",
                "autocomplete": "new-password",
            }
        ),
    )
    password2 = forms.CharField(
        label=_("Подтверждение пароля"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Повторите пароль",
                "autocomplete": "new-password",
            }
        ),
    )

    class Meta:
        model = CustomUser
        fields = (
            "email",
            "username",
            "first_name",
            "last_name",
            "phone",
            "password1",
            "password2",
        )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError(_("Пользователь с таким email уже существует."))
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        if phone:
            # Очищаем номер от лишних символов
            cleaned_phone = "".join(filter(str.isdigit, phone))
            if len(cleaned_phone) < 10:
                raise ValidationError(
                    _("Номер телефона должен содержать минимум 10 цифр")
                )
        return phone


class UserLoginForm(AuthenticationForm):
    """Форма авторизации пользователя"""

    username = forms.CharField(
        label=_("Email"),
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "example@mail.com",
                "autocomplete": "email",
            }
        ),
    )
    password = forms.CharField(
        label=_("Пароль"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Введите пароль",
                "autocomplete": "current-password",
            }
        ),
    )
    remember_me = forms.BooleanField(
        label=_("Запомнить меня"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    error_messages = {
        "invalid_login": _(
            "Пожалуйста, введите правильные email и пароль. "
            "Оба поля могут быть чувствительны к регистру."
        ),
        "inactive": _("Этот аккаунт неактивен."),
    }


class UserProfileForm(forms.ModelForm):
    """Форма для редактирования профиля пользователя"""

    class Meta:
        model = CustomUser
        fields = ("username", "email", "phone_number")
        widgets = {
            "username": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ваш логин"}
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ваша почта",
                    "readonly": "readonly",
                }
            ),
            "phone_number": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "+7 (999) 123-45-67"}
            ),
        }
        labels = {
            "username": _("Логин"),
            "email": _("Почта"),
            "phone_number": _("Телефон"),
        }


class ChangePasswordForm(forms.Form):
    """Форма для смены пароля"""

    old_password = forms.CharField(
        label=_("Старый пароль"),
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Введите старый пароль"}
        ),
    )
    new_password = forms.CharField(
        label=_("Новый пароль"),
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Введите новый пароль"}
        ),
        help_text=_("Пароль должен содержать минимум 8 символов"),
    )
    confirm_password = forms.CharField(
        label=_("Подтверждение пароля"),
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Повторите новый пароль"}
        ),
    )

    def clean_new_password(self):
        new_password = self.cleaned_data.get("new_password")
        if len(new_password) < 8:
            raise ValidationError(_("Пароль должен содержать минимум 8 символов"))
        return new_password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password and confirm_password and new_password != confirm_password:
            raise ValidationError(_("Пароли не совпадают"))

        return cleaned_data


class AvatarUploadForm(forms.ModelForm):
    """Форма для загрузки аватара"""

    class Meta:
        model = CustomUser
        fields = ("avatar",)
        widgets = {
            "avatar": forms.FileInput(
                attrs={"class": "form-control", "accept": "image/*"}
            )
        }
        labels = {"avatar": _("Выберите изображение для аватара")}

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")
        if avatar:
            # Проверка размера файла (макс 2MB)
            if avatar.size > 2 * 1024 * 1024:
                raise ValidationError(_("Размер файла не должен превышать 2MB"))

            # Проверка расширения файла
            allowed_extensions = ["jpg", "jpeg", "png", "gif"]
            ext = avatar.name.split(".")[-1].lower()
            if ext not in allowed_extensions:
                raise ValidationError(_("Допустимые форматы: JPG, JPEG, PNG, GIF"))

        return avatar


class DeleteAccountForm(forms.Form):
    """Форма для подтверждения удаления аккаунта"""

    password = forms.CharField(
        label=_("Пароль для подтверждения"),
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Введите ваш пароль"}
        ),
    )
    confirm = forms.BooleanField(
        label=_("Я понимаю, что это действие нельзя отменить"),
        required=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )


class PasswordResetRequestForm(forms.Form):
    """Форма для запроса сброса пароля"""

    email = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "example@mail.com"}
        ),
    )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not CustomUser.objects.filter(email=email).exists():
            raise ValidationError(_("Пользователь с таким email не найден"))
        return email


class SetNewPasswordForm(forms.Form):
    """Форма для установки нового пароля"""

    new_password = forms.CharField(
        label=_("Новый пароль"),
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Введите новый пароль"}
        ),
    )
    confirm_password = forms.CharField(
        label=_("Подтверждение пароля"),
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Повторите новый пароль"}
        ),
    )

    def clean_new_password(self):
        new_password = self.cleaned_data.get("new_password")
        if len(new_password) < 8:
            raise ValidationError(_("Пароль должен содержать минимум 8 символов"))
        return new_password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password and confirm_password and new_password != confirm_password:
            raise ValidationError(_("Пароли не совпадают"))

        return cleaned_data
