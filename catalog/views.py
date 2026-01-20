from django.contrib import messages
from django.core.paginator import Paginator
from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView, TemplateView, UpdateView
from django.views.generic.edit import CreateView, DeleteView

from .models import Category, Product


class HomeView(TemplateView):
    """Главная страница"""

    template_name = "catalog/home.html"


class ContactsView(TemplateView):
    """Страница контактов"""

    template_name = "catalog/contacts.html"


# Функция для каталога
class CatalogView(ListView):
    model = Product
    paginate_by = 6
    template_name = "catalog/product-catalog.html"
    context_object_name = "products"
    ordering = ["-created_at"]  # Сортировка по дате создания

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Добавляем пагинатор в контекст
        paginator = Paginator(self.get_queryset(), self.paginate_by)
        page_number = self.request.GET.get("page")
        context["page_obj"] = paginator.get_page(page_number)
        return context


# Функция для детальной страницы товара
class ProductDetailView(DetailView):
    """Страница с подробной информацией о товаре"""

    model = Product
    template_name = "catalog/product_detail.html"
    context_object_name = "products"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


# Функция для добавления товара
class ProductCreate(CreateView):
    """Страница с формой для добавления нового товара"""

    model = Product
    fields = [
        "name",
        "description",
    ]
    template_name = "catalog/product_form.html"
    success_url = reverse_lazy("catalog")

    def form_valid(self, form):
        """Действия при успешной валидации формы"""
        response = super().form_valid(form)
        messages.success(self.request, f'Товар "{form.instance.name}" успешно создан!')
        return response

    def form_invalid(self, form):
        """Действия при ошибке валидации"""
        messages.error(self.request, "Пожалуйста, исправьте ошибки в форме.")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Добавляем категории для выпадающего списка
        context["categories"] = Category.objects.all()
        return context


class ProductUpdateView(UpdateView):
    model = Product
    template_name = "catalog/product_form.html"


class ProductDeleteView(DeleteView):
    """Удаление товара"""

    model = Product
    template_name = "catalog/product_delete.html"
    success_url = reverse_lazy("catalog")

    def delete(self, request, *args, **kwargs):
        messages.success(request, f" Товар успешно удален! ")
        return super().delete(request, *args, **kwargs)


class CategoryListView(ListView):
    """Список всех категорий"""

    model = Category
    template_name = "catalog/category_list.html"
    context_object_name = "categories"
    ordering = ["name"]


class CategoryDetailView(DetailView):
    """Детали категории с товарами"""

    model = Category
    template_name = "catalog/category_detail.html"
    context_object_name = "category"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Добавляем товары этой категории
        context["products"] = self.object.product_set.all()
        return context
