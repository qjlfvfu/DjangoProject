from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
# Register your models here.


class UserAdmin(UserAdmin):
    # Поля, отображаемые в списке пользователей
    list_display = ['id', 'email', 'first_name', 'last_name', 'is_staff', 'is_active']

    # Поля для поиска
    search_fields = ['email', 'first_name', 'last_name']

    # Фильтры справа
    list_filter = ['is_staff', 'is_active', 'country']

    # Поля, которые можно редактировать прямо в списке
    list_editable = ['is_staff', 'is_active']

    # Сортировка
    ordering = ['email']

    # Разбивка на страницы
    list_per_page = 20

    # Поля для формы редактирования пользователя
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Персональная информация', {
            'fields': ('first_name', 'last_name', 'avatar', 'country', 'phone_number')
        }),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )

    # Поля для формы создания нового пользователя
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )


admin.site.register(CustomUser, UserAdmin)