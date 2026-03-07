from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),  # Главная страница
    path("contacts/", views.ContactsView.as_view(), name="contacts"),  # Контакты
    path(
        "catalog/", views.CatalogView.as_view(), name="product_catalog"
    ),  # Каталог товаров
    path(
        "product/<int:pk>/", views.ProductDetailView.as_view(), name="product_detail"
    ),  # Детали товара
    path(
        "product/create/", views.ProductCreate.as_view(), name="product_create"
    ),  # Создание товара
    path(
        "product/<int:pk>/delete/",
        views.ProductDeleteView.as_view(),
        name="product_delete",
    ),
    path(
        "product/update/int:pk/update",
        views.ProductUpdateView.as_view(),
        name="product_form",
    ),
    path(
        "category/create/", views.CategoryCreateView.as_view(), name="category_create"
    ),  # Создание категорий
    path(
        "category/list/", views.CategoryListView.as_view(), name="category_list"
    ),  # Список категорий
    path(
        "category/<int:pk>/", views.CategoryDetailView.as_view(), name="category_detail"
    ),
    path(
        "category/<int:pk>/delete/",
        views.CategoryDeleteView.as_view(),
        name="category_delete",
    ),
    path(
        "category/<int:category_id>/products/",
        views.CategoryProductsView.as_view(),
        name="category_products",
    ),
]
