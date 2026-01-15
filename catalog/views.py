from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from .models import Product, Category


def home(request):
    """Главная страница"""
    return render(request, "catalog/home.html")


# Функция для контактов
def contacts(request):
    """Страница контактов"""
    return render(request, "catalog/contacts.html")


# Функция для каталога
def catalog(request):
    """Страница каталога товаров"""
    products = Product.objects.all().order_by('-created_at')

    # Пагинация
    paginator = Paginator(products, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'catalog/product-catalog.html', context)


# Функция для детальной страницы товара
def product_detail(request, pk):
    """Страница с подробной информацией о товаре"""
    product = get_object_or_404(Product, pk=pk)
    context = {
        'product': product,
    }
    return render(request, 'catalog/product_detail.html', context)


# Функция для добавления товара
def product_create(request):
    """Страница с формой для добавления нового товара"""

    # Получаем все категории для выпадающего списка
    categories = Category.objects.all()

    if request.method == 'POST':
        # Получаем данные из формы
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        category_id = request.POST.get('category')
        picture = request.FILES.get('picture')

        # Проверяем обязательные поля
        if not name or not price or not category_id:
            # Если не все обязательные поля заполнены
            error_message = "Заполните все обязательные поля: название, цена и категория"
            return render(request, 'catalog/product_form.html', {
                'categories': categories,
                'error': error_message,
                'form_data': {  # Сохраняем введенные данные для повторного показа
                    'name': name,
                    'description': description,
                    'price': price,
                    'category_id': category_id,
                }
            })

        try:
            # Пытаемся получить категорию
            category = Category.objects.get(id=category_id)

            # Создаем новый продукт
            product = Product.objects.create(
                name=name,
                description=description,
                price=price,
                category=category,
                picture=picture
            )

            # Успешное создание
            messages.success(request, f'Товар "{name}" успешно создан!')
            return redirect('catalog:catalog')  # Убедитесь, что используете правильное имя маршрута

        except Category.DoesNotExist:
            # Если категория не найдена
            error_message = "Выбранная категория не найдена"
            return render(request, 'catalog/product_form.html', {
                'categories': categories,
                'error': error_message,
                'form_data': {
                    'name': name,
                    'description': description,
                    'price': price,
                    'category_id': category_id,
                }
            })
        except ValueError as e:
            # Ошибка валидации (например, цена не число)
            error_message = f"Ошибка в данных: {str(e)}"
            return render(request, 'catalog/product_form.html', {
                'categories': categories,
                'error': error_message,
                'form_data': {
                    'name': name,
                    'description': description,
                    'price': price,
                    'category_id': category_id,
                }
            })

    else:
        # GET запрос - показываем пустую форму
        context = {
            'categories': categories,
        }
        return render(request, 'catalog/product_form.html', context)