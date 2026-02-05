from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=40,verbose_name="Категория",unique=True )
    description = models.TextField(verbose_name="Описание",
                                   help_text="Введите описание категории",
                                   blank=True, null=False )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ["name"]


class Product(models.Model):
    name = models.CharField(max_length=100,verbose_name="Наименование товара",unique=True)
    description = models.TextField(verbose_name="Описание",blank=True, null=False)
    picture = models.ImageField(upload_to="products/",verbose_name="Изображение",blank=True,null=True)
    category = models.ForeignKey(Category,on_delete=models.PROTECT,verbose_name="Категория",related_name="products" )
    price = models.DecimalField(max_digits=10,decimal_places=2,verbose_name="Цена")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True,verbose_name="Дата последнего изменения")
    is_active = models.BooleanField(default=True,verbose_name="Активный")

    def __str__(self):
        return f"{self.name} ({self.price} руб.)"

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ["-category"]
