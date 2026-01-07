from django.shortcuts import render


# Create your views here.
def home_open(request):
    return render(request, "catalog/home.html")


def contacts_open(
    request,
):
    context = {"title": "Контакты", "message": "ВЫ во вкладке контакты!"}
    return render(request, "catalog/contacts.html", context)


def catalog_open(request):
    return render(request, "catalog/product-catalog.html")
