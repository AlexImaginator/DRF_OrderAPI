from django.db import models
from users.models import User


class Parameter(models.Model):
    name = models.CharField(max_length=40, verbose_name='Название')

    class Meta:
        verbose_name = 'Название параметра'
        verbose_name_plural = 'Список названий параметров'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Shop(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь', on_delete=models.CASCADE, related_name='shops')
    name = models.CharField(max_length=50, verbose_name='Название')
    url = models.URLField(verbose_name='Ссылка update', blank=True, null=True)
    state = models.BooleanField(verbose_name='Статус приема заказов', default=True)

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = 'Список магазинов'
        ordering = ('name',)
        unique_together = ['user', 'name']

    def __str__(self):
        return f'{self.name} - {self.user}'
