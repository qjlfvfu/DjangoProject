from django.db import models

class Category(models.Model):
    objects = None
    name=models.CharField(max_length=40,verbose_name="Категория")
    description = models.TextField(null=True, verbose_name="Описание",help_text="Введите описание категории")
    def __str__(self):
        return f"{self.name} "
    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['name']  # Сортировка по имени



class Product(models.Model):
    objects = None
    name=models.CharField(max_length=100,verbose_name="Наименование товара",unique=True)
    description=models.TextField(null=True,verbose_name="Описание")
    picture=models.ImageField(upload_to="image/",verbose_name="изображение",null=True)
    category=models.ForeignKey(Category,on_delete=models.PROTECT,related_name="Товар")
    price=models.IntegerField(verbose_name="цена")
    created_at=models.DateTimeField(auto_now_add=True,verbose_name="дата создания")
    updated_at=models.DateTimeField(auto_now=True,verbose_name="дата последнего изменения")
    def __str__(self):
        return f"""
        {self.id}
        {self.name} {self.category}
        {self.description} 
        {self.price}
        """

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ['category'] # Сортировка по категории

