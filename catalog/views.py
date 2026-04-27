from django.contrib import messages
from django.core.paginator import Paginator
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic import DetailView, ListView, TemplateView, UpdateView
from django.views.generic.edit import CreateView, DeleteView
from .forms import CategoryForm, ProductForm
from .models import Category, Product
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.core.cache import cache
from django.contrib.auth import get_user_model

from .service import ProductService

User = get_user_model()


class HomeView(TemplateView):
    """Главная страница"""

    template_name = "catalog/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        products = cache.get("home_products")
        if not products:
            products = Product.objects.filter(is_published=True)[:10]
            cache.set("home_products", products, 60 * 15)

        context["products"] = Product.objects.all().order_by("-created_at")[:8]
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

    def get_queryset(self):
        queryset = cache.get("qwerty")
        if not queryset:
            queryset = super().get_queryset()
            cache.set("qwerty", queryset, 60 * 15)  # Кешируем данные на 15 минут
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paginator = Paginator(self.get_queryset(), self.paginate_by)
        page_number = self.request.GET.get("page")
        context["page_obj"] = paginator.get_page(page_number)
        return context


@method_decorator(cache_page(60 * 30), name="dispatch")
class ProductDetailView(LoginRequiredMixin, DetailView):
    """Страница с подробной информацией о товаре - только для авторизованных"""

    model = Product
    template_name = "catalog/product_detail.html"
    context_object_name = "product"
    login_url = "/botblock/login/"
    redirect_field_name = "next"


class ProductCreate(LoginRequiredMixin, CreateView):
    """Создание товара - только для авторизованных"""

    model = Product
    form_class = ProductForm
    template_name = "catalog/product_form.html"
    success_url = reverse_lazy("catalog:product_catalog")
    login_url = "/botblock/login/"
    redirect_field_name = "next"

    def form_valid(self, form):
        """Действия при успешной валидации формы"""
        # Привязываем товар к текущему пользователю
        if hasattr(form.instance, "owner") and self.request.user.is_authenticated:
            form.instance.owner = self.request.user
            print(
                f"✅ Товар будет привязан к: {self.request.user.email}"
            )  # для отладки

        response = super().form_valid(form)
        messages.success(self.request, f'Товар "{form.instance.name}" успешно создан!')
        return response

    def form_invalid(self, form):
        """Действия при ошибке валидации"""
        messages.error(self.request, "Пожалуйста, исправьте ошибки в форме.")
        return super().form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        """Проверка авторизации перед созданием"""
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)


class ProductUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование товара - только для владельца или staff"""

    model = Product
    form_class = ProductForm
    template_name = "catalog/product_form.html"
    login_url = "/botblock/login/"
    redirect_field_name = "next"

    def get_success_url(self):
        return reverse_lazy("catalog:product_detail", kwargs={"pk": self.object.pk})

    def dispatch(self, request, *args, **kwargs):
        """Проверка прав доступа перед редактированием"""
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # Получаем объект для проверки прав
        self.object = self.get_object()

        # Проверяем права: владелец ИЛИ staff
        if (
            self.object.owner
            and self.object.owner != request.user
            and not request.user.is_staff
        ):
            messages.error(
                request, "❌ У вас нет прав для редактирования этого товара!"
            )
            return redirect("catalog:product_detail", pk=self.object.pk)

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request, f'Товар "{form.instance.name}" успешно обновлен!'
        )
        return response


class ProductDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление товара - только для владельца или staff"""

    model = Product
    template_name = "catalog/product_delete.html"
    login_url = "/botblock/login/"
    redirect_field_name = "next"

    def get_success_url(self):
        return reverse_lazy("catalog:product_catalog")

    def dispatch(self, request, *args, **kwargs):
        """Проверка прав доступа перед удалением"""
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # Получаем объект для проверки прав
        self.object = self.get_object()

        # Проверяем права: владелец ИЛИ staff
        if (
            self.object.owner
            and self.object.owner != request.user
            and not request.user.is_staff
        ):
            messages.error(request, "❌ У вас нет прав для удаления этого товара!")
            return redirect("catalog:product_detail", pk=self.object.pk)

        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        product = self.get_object()
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'Товар "{product.name}" успешно удален!')
        return response


# ===== КАТЕГОРИИ =====
@method_decorator(cache_page(60 * 120), name="dispatch")
class CategoryProductsView(ListView):
    """Список продуктов в указанной категории"""

    model = Product
    template_name = "catalog/category_products.html"
    context_object_name = "products"
    paginate_by = 6

    def get_queryset(self):
        # Получаем категорию и сохраняем её для использования в get_context_data
        self.category = get_object_or_404(Category, id=self.kwargs["category_id"])
        # Используем сервисный метод для получения продуктов именно этой категории
        return ProductService.get_products_by_category(self.kwargs["category_id"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = self.category
        return context


class CategoryListView(ListView):
    """Список категорий - доступен всем"""

    model = Category
    template_name = "catalog/category_list.html"
    context_object_name = "categories"
    ordering = ["name"]

    def get_context_data(self, **kwargs):
        # Сначала получаем базовый контекст
        context = super().get_context_data(**kwargs)

        # Создаем список статистики
        categories_stats = []

        # Проходим по всем категориям из контекста
        for category in context["categories"]:
            categories_stats.append(
                {
                    "category": category,
                    "total": category.products.count(),
                    "active": category.products.filter(is_active=True).count(),
                    "published": category.products.filter(is_published=True).count(),
                    "active_published": category.products.filter(
                        is_active=True, is_published=True
                    ).count(),
                }
            )

        # Добавляем статистику в контекст
        context["categories_stats"] = categories_stats

        return context


class CategoryDetailView(DetailView):
    """Детали категории - доступны всем"""

    model = Category
    template_name = "catalog/category_detail.html"
    context_object_name = "category"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Добавляем товары этой категории
        context["products"] = self.object.products.all()
        return context


class CategoryCreateView(LoginRequiredMixin, CreateView):
    """Создание категории - только для авторизованного пользователя"""

    model = Category
    form_class = CategoryForm
    template_name = "catalog/category_form.html"
    success_url = reverse_lazy("catalog:category_list")
    login_url = "/botblock/login/"
    redirect_field_name = "next"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request, f'Категория "{form.instance.name}" успешно создана!'
        )
        return response


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    """Обновление категории - только для авторизованного пользователя"""

    model = Category
    form_class = CategoryForm
    template_name = "catalog/category_form.html"
    success_url = reverse_lazy("catalog:category_list")
    login_url = "/botblock/login/"
    redirect_field_name = "next"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request, f'Категория "{form.instance.name}" успешно обновлена!'
        )
        return response


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление категории - только для авторизованного пользователя"""

    model = Category
    template_name = "catalog/category_delete.html"
    success_url = reverse_lazy("catalog:category_list")
    login_url = "/botblock/login/"
    redirect_field_name = "next"

    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'Категория "{category.name}" успешно удалена!')
        return response
