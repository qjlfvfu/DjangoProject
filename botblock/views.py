# botblock/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from .forms import (
    UserRegisterForm, UserLoginForm, UserProfileForm,
    ChangePasswordForm, AvatarUploadForm
)
from .utils import send_welcome_email
from .models import CustomUser
from catalog.models import Product


class RegisterView(CreateView):
    """Регистрация пользователя"""
    form_class = UserRegisterForm
    template_name = 'botblock/register.html'
    success_url = reverse_lazy('botblock:login')

    def form_valid(self, form):
        # ✅ Автоматически создаем username, если он не указан
        if not form.cleaned_data.get('username'):
            email = form.cleaned_data.get('email')
            # Берем часть email до @
            base_username = email.split('@')[0]
            username = base_username

            counter = 1
            while CustomUser.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            form.instance.username = username

        response = super().form_valid(form)
        user = form.save()

        # Отправка письма
        try:
            send_welcome_email(user)
            messages.success(
                self.request,_('Регистрация успешна! На ваш email отправлено приветственное письмо.'))
        except Exception as e:
            messages.warning(self.request,_('Регистрация успешна, но не удалось отправить приветственное письмо.'))

        return response

    def form_invalid(self, form):
        messages.error(self.request, _('Пожалуйста, исправьте ошибки в форме.'))
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Регистрация')
        return context


class LoginView(FormView):
    """Авторизация пользователя"""
    form_class = UserLoginForm
    template_name = 'botblock/login.html'
    success_url = reverse_lazy('catalog:home')

    def form_valid(self, form):
        email = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(self.request, username=email, password=password)

        if user is not None:
            login(self.request, user)

            # Обработка "Запомнить меня"
            if not form.cleaned_data.get('remember_me'):
                self.request.session.set_expiry(0)

            messages.success(self.request, _('Вы успешно вошли в систему!'))
            return super().form_valid(form)
        else:
            messages.error(self.request, _('Неверный email или пароль.'))
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Вход в систему')
        return context


@login_required
def logout_view(request):
    """Выход из системы"""
    logout(request)
    messages.success(request, _('Вы успешно вышли из системы.'))
    return redirect('catalog:home')


@login_required
def profile_view(request):
    """Профиль пользователя"""
    products = Product.objects.all().order_by('-created_at')[:3]  # Показываем все товары

    return render(request, 'botblock/profile.html', {
        'title': _('Мой профиль'),
        'user': request.user,
        'products': products
    })


@login_required
def profile_edit(request):
    """Редактирование профиля"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Профиль успешно обновлен!'))
            return redirect('botblock:profile')
        else:
            messages.error(request, _('Пожалуйста, исправьте ошибки в форме.'))
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'botblock/profile_edit.html', {
        'form': form,
        'title': _('Редактирование профиля')
    })


@login_required
def change_password(request):
    """Смена пароля"""
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            user = request.user
            old_password = form.cleaned_data.get('old_password')

            if user.check_password(old_password):
                user.set_password(form.cleaned_data.get('new_password'))
                user.save()
                update_session_auth_hash(request, user)  # Важно! Оставляет пользователя в системе
                messages.success(request, _('Пароль успешно изменен!'))
            else:
                messages.error(request, _('Неверный старый пароль'))
        else:
            for error in form.errors.values():
                messages.error(request, error)
    return redirect('botblock:profile')


@login_required
def change_email(request):
    """Смена email пользователя"""
    if request.method == 'POST':
        new_email = request.POST.get('new_email')
        confirm_email = request.POST.get('confirm_email')
        password = request.POST.get('password')

        # Проверка пароля
        if not request.user.check_password(password):
            messages.error(request, 'Неверный пароль')
            return redirect('botblock:profile')

        # Проверка совпадения email
        if new_email != confirm_email:
            messages.error(request, 'Email адреса не совпадают')
            return redirect('botblock:profile')

        # Проверка уникальности email
        if CustomUser.objects.filter(email=new_email).exclude(pk=request.user.pk).exists():
            messages.error(request, 'Пользователь с таким email уже существует')
            return redirect('botblock:profile')

        # Сохраняем новый email
        request.user.email = new_email
        request.user.save()
        messages.success(request, 'Email успешно изменен!')

    return redirect('botblock:profile')


@login_required
def upload_avatar(request):
    """Загрузка аватара"""
    if request.method == 'POST':
        form = AvatarUploadForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Аватар успешно обновлен!'))
        else:
            for error in form.errors.values():
                messages.error(request, error)
    return redirect('botblock:profile')


@login_required
def my_products(request):
    """Список товаров пользователя"""
    products = Product.objects.filter(owner=request.user).order_by('-created_at')
    paginator = Paginator(products, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'botblock/my_products.html', {
        'products': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'title': _('Мои товары')
    })


@login_required
def delete_account(request):
    """Удаление аккаунта пользователя"""
    if request.method == 'POST':
        password = request.POST.get('password')

        if request.user.check_password(password):
            # Удаляем пользователя
            user = request.user
            logout(request)
            user.delete()
            messages.success(request, _('Ваш аккаунт был успешно удален.'))
            return redirect('catalog:home')
        else:
            messages.error(request, _('Неверный пароль'))

    return redirect('botblock:profile')