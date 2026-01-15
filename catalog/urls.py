from django.urls import path
from . import views

app_name = "catalog"

urlpatterns = [
    path('', views.home, name='home'),  # Главная страница
    path('contacts/', views.contacts, name='contacts'),  # Контакты
    path('catalog/', views.catalog, name='catalog'),  # Каталог товаров
    path('product/<int:pk>/', views.product_detail, name='product_detail'),  # Детали товара
    path('product/create/', views.product_create, name='product_create'),  # Создание товара
]