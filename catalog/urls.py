from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),  # Главная страница
    path("contacts/", views.ContactsView.as_view(), name="contacts"),  # Контакты
    path("catalog/", views.CatalogView.as_view(), name="catalog"),  # Каталог товаров
    path(
        "product/<int:pk>/", views.ProductDetailView.as_view(), name="product_detail"
    ),  # Детали товара
    path(
        "product/create/", views.ProductCreate.as_view(), name="product_create"
    ),  # Создание товара
    path("product/delete/", views.ProductDeleteView.as_view(), name="product_delete"),
]
