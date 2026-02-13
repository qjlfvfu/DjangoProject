from django.contrib import messages
from django.core.paginator import Paginator
from django.urls import reverse_lazy, reverse
from django.views.generic import DetailView, ListView, TemplateView, UpdateView
from django.views.generic.edit import CreateView, DeleteView
from .forms import CategoryForm, ProductForm
from .models import Category, Product
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

# Импортируем модель пользователя
from django.contrib.auth import get_user_model

User = get_user_model()


class HomeView(TemplateView):
    """Главная страница"""
    template_name = "catalog/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Получаем первые 8 товаров для главной страницы
        context['products'] = Product.objects.all().order_by('-created_at')[:8]
        return context


class ContactsView(TemplateView):
    """Страница контактов - доступна всем"""
    template_name = "catalog/contacts.html"


class CatalogView(ListView):
    """Каталог товаров - доступен всем"""
    model = Product
    paginate_by = 6
    template_name = "catalog/product_catalog.html"
    context_object_name = "products"
    ordering = ["-created_at"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paginator = Paginator(self.get_queryset(), self.paginate_by)
        page_number = self.request.GET.get("page")
        context["page_obj"] = paginator.get_page(page_number)
        return context


class ProductDetailView(LoginRequiredMixin, DetailView):
    """Страница с подробной информацией о товаре - только для авторизованных"""
    model = Product
    template_name = "catalog/product_detail.html"
    context_object_name = "product"
    login_url = '/botblock/login/'
    redirect_field_name = 'next'


class ProductCreate(LoginRequiredMixin, CreateView):
    """Создание товара - только для авторизованных"""
    model = Product
    form_class = ProductForm
    template_name = "catalog/product_form.html"
    success_url = reverse_lazy("catalog:product_catalog")
    login_url = '/botblock/login/'
    redirect_field_name = 'next'

    def form_valid(self, form):
        """Действия при успешной валидации формы"""
        if hasattr(form.instance, 'owner') and self.request.user.is_authenticated:
            form.instance.owner = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'Товар "{form.instance.name}" успешно создан!')
        return response

    def form_invalid(self, form):
        """Действия при ошибке валидации"""
        messages.error(self.request, "Пожалуйста, исправьте ошибки в форме.")
        return super().form_invalid(form)


class ProductUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование товара - только для авторизованного пользователя"""
    model = Product
    form_class = ProductForm
    template_name = "catalog/product_form.html"
    login_url = '/botblock/login/'
    redirect_field_name = 'next'

    def get_success_url(self):
        return reverse_lazy("catalog:product_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Товар "{form.instance.name}" успешно обновлен!')
        return response


class ProductDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление товара - только для авторизованного пользователя"""
    model = Product
    template_name = "catalog/product_delete.html"
    login_url = '/botblock/login/'
    redirect_field_name = 'next'

    def get_success_url(self):
        return reverse_lazy("catalog:product_catalog")

    def delete(self, request, *args, **kwargs):
        product = self.get_object()
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'Товар "{product.name}" успешно удален!')
        return response


# ===== КАТЕГОРИИ =====

class CategoryListView(ListView):
    """Список категорий - доступен всем"""
    model = Category
    template_name = "catalog/category_list.html"
    context_object_name = "categories"
    ordering = ["name"]


class CategoryDetailView(DetailView):
    """Детали категории - доступны всем"""
    model = Category
    template_name = "catalog/category_detail.html"
    context_object_name = "category"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Добавляем товары этой категории
        context["products"] = self.object.product_set.all()
        return context


class CategoryCreateView(LoginRequiredMixin, CreateView):
    """Создание категории - только для авторизованного пользователя"""
    model = Category
    form_class = CategoryForm
    template_name = "catalog/category_form.html"
    success_url = reverse_lazy("catalog:category_list")
    login_url = '/botblock/login/'
    redirect_field_name = 'next'

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Категория "{form.instance.name}" успешно создана!')
        return response


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    """Обновление категории - только для авторизованного пользователя"""
    model = Category
    form_class = CategoryForm
    template_name = "catalog/category_form.html"
    success_url = reverse_lazy("catalog:category_list")
    login_url = '/botblock/login/'
    redirect_field_name = 'next'

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Категория "{form.instance.name}" успешно обновлена!')
        return response


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление категории - только для авторизованного пользователя"""
    model = Category
    template_name = "catalog/category_delete.html"
    success_url = reverse_lazy("catalog:category_list")
    login_url = '/botblock/login/'
    redirect_field_name = 'next'


    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'Категория "{category.name}" успешно удалена!')
        return response