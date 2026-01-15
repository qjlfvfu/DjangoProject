**# Django Project 
##### Проект простейшего сайта для домашки
## Установка и запуск

Установите зависимости:
` bash
pip install -r requirements.txt `

Запустите сервер:
`bash
python manage.py runserver `
Или для Mac
`bash
python3 manage.py runserver `

## Функциональность
Она есть , перейти на страницы возможно и уже хорошо 
## Структура проекта
Домашка с веб-дизайном/
│   └── [catalog](catalog)                        # приложение
│      ├── [templates](catalog/templates)         # папка без которой почему то нихрена не работает
│      └── [catalog](catalog/templates/catalog)   # папка где все страницы 
│           ├──[management](catalog/management)   # папка МЭЭЭнеджмента
│           │      └── [commands](catalog/management/commands) # папка c командами
│           │              └── [add_data.py](catalog/management/commands/add_data.py)      # команда добавления 
│           │              └──[delete_data.py](catalog/management/commands/delete_data.py) # команда удаления
│           │              └── [load_data.py](catalog/management/commands/load_data.py)    # команда загрузки через фикстуры
│           ├── [contacts.html](catalog/templates/catalog/contacts.html)               # страница контактов
│           ├── [home.html](catalog/templates/catalog/home.html)                       # страница Главная
│           └── [product-catalog.html](catalog/templates/catalog/product-catalog.html) # страница Каталога товаров
├── [config](config) # папка конфигурации приложения
│   ├── [urls.py](config/urls.py) маршруты
├── [manage.py](manage.py)                          # сервер
├── [requirements.txt](requirements.txt)           # Зависимости
└── [ReadMe.md](ReadMe.md)                         # Этот файл**

# Требования
### Python 3.8+
### Django 6.0+





~~говно а не ОРМ через шэлл~~