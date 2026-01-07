from django.urls import path
from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.home_open, name="home"),  # Главная: /
    path("contacts/", views.contacts_open, name="contacts"),  # Контакты: /contacts/
    path("catalog/", views.catalog_open, name="catalog"),
]
