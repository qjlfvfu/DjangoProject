from itertools import product

from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id","name")
    search_fields = ("name", "description")


#category=Category(name= "Мясо",description="Вкусное и сочное мясо")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id","name","price","category")
    list_filter = ("category",)
    search_fields = ("name","description")


# Мясо Вкусное и сочное мясо
# Рыба рыбная продукция
# Обезьяна почти как ребенок(на вкус)
# Бегемот all fine
# Крокодил невкусный но питательный крокодил