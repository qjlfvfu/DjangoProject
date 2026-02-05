from django.contrib import messages
from django.core.paginator import Paginator
from django.urls import reverse_lazy, reverse
from django.views.generic import DetailView, ListView, TemplateView, UpdateView
from django.views.generic.edit import CreateView, DeleteView

from .forms import CategoryForm, ProductForm
from .models import Category, Product


class HomeView(TemplateView):
    """Главная страница"""
    template_name = "catalog/home.html"


class ContactsView(TemplateView):
    """Страница контактов"""
    template_name = "catalog/contacts.html"


class CatalogView(ListView):
    """Каталог товаров"""
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


class ProductDetailView(DetailView):
    """Страница с подробной информацией о товаре"""
    model = Product
    template_name = "catalog/product_detail.html"
    context_object_name = "product"


class ProductCreate(CreateView):
    """Страница с формой для добавления нового товара"""
    model = Product
    form_class = ProductForm
    template_name = "catalog/product_form.html"

    def get_success_url(self):
        return reverse_lazy("catalog:product_catalog")

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
        context["title"] = "Создание товара"
        return context


class ProductUpdateView(UpdateView):
    """Обновление товара"""
    model = Product
    form_class = ProductForm
    template_name = "catalog/product_form.html"

    def get_success_url(self):
        return reverse_lazy("catalog:product_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Товар "{form.instance.name}" успешно обновлен!')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Редактирование товара"
        return context


class ProductDeleteView(DeleteView):
    """Удаление товара"""
    model = Product
    template_name = "catalog/product_delete.html"

    def get_success_url(self):
        return reverse_lazy("catalog:product-catalog")

    def delete(self, request, *args, **kwargs):
        product = self.get_object()
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'Товар "{product.name}" успешно удален!')
        return response


class CategoryListView(ListView):
    """Список всех категорий"""
    model = Category
    template_name = "catalog/category_list.html"
    context_object_name = "categories"
    ordering = ["name"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Категории товаров"
        return context


class CategoryCreateView(CreateView):
    """Создание категории"""
    model = Category
    form_class = CategoryForm
    template_name = "catalog/category_form.html"
    success_url = reverse_lazy("catalog:category_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Категория "{form.instance.name}" успешно создана!')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Создание категории"
        return context


class CategoryUpdateView(UpdateView):
    """Обновление категории"""
    model = Category
    form_class = CategoryForm
    template_name = "catalog/category_form.html"
    success_url = reverse_lazy("catalog:category_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Категория "{form.instance.name}" успешно обновлена!')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Редактирование категории"
        return context


class CategoryDeleteView(DeleteView):
    """Удаление категории"""
    model = Category
    template_name = "catalog/category_delete.html"
    success_url = reverse_lazy("catalog:category_list")

    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'Категория "{category.name}" успешно удалена!')
        return response


class CategoryDetailView(DetailView):
    """Детали категории с товарами"""
    model = Category
    template_name = "catalog/category_detail.html"
    context_object_name = "category"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["products"] = self.object.product_set.all()
        context["title"] = f"Категория: {self.object.name}"
        return context