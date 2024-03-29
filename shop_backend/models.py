from django.db import models
from users.models import User, Contact
from django.core.validators import MinValueValidator
from _decimal import Decimal


STATE_CHOICES = (
    ('new', 'Новый'),
    ('confirmed', 'Подтвержден'),
    ('assembled', 'Собран'),
    ('sent', 'Отправлен'),
    ('delivered', 'Доставлен'),
    ('canceled', 'Отменен'),

)


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


class Category(models.Model):
    shops = models.ManyToManyField(Shop, verbose_name='Магазины', related_name='categories')
    name = models.CharField(max_length=80, verbose_name='Название')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Список категорий'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name='Категория')
    name = models.CharField(max_length=80, verbose_name='Название')

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Список товаров'
        ordering = ('name',)

    def __str__(self):
        return self.name


class ProductInShop(models.Model):
    product = models.ForeignKey(Product,
                                on_delete=models.CASCADE,
                                related_name='products_in_shops',
                                verbose_name='Товар'
                                )
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='products_in_shops', verbose_name='Магазин')
    model = models.CharField(max_length=80, blank=True, verbose_name='Модель')
    price = models.DecimalField(max_digits=11,
                                decimal_places=2,
                                verbose_name='Цена',
                                validators=[MinValueValidator(Decimal('0.01'))]
                                )
    quantity = models.PositiveIntegerField(verbose_name='Количество')

    class Meta:
        verbose_name = 'Товар магазина'
        verbose_name_plural = 'Список товаров магазина'
        constraints = [
            models.UniqueConstraint(fields=['shop', 'product', 'model'], name='unique_product_in_shop'),
        ]


class ProductParameter(models.Model):
    product_in_shop = models.ForeignKey(ProductInShop,
                                        on_delete=models.CASCADE,
                                        related_name='product_parameters',
                                        verbose_name='Товар магазина'
                                        )
    parameter = models.ForeignKey(Parameter,
                                  on_delete=models.CASCADE,
                                  related_name='product_parameters',
                                  verbose_name='Параметр'
                                  )
    value = models.CharField(max_length=100, verbose_name='Значение')

    class Meta:
        verbose_name = 'Параметр товара'
        verbose_name_plural = 'Список параметров товара'
        constraints = [
            models.UniqueConstraint(fields=['product_in_shop', 'parameter'], name='unique_product_parameter')
        ]


class BasketPosition(models.Model):
    user = models.ForeignKey(User,
                             verbose_name='Покупатель',
                             on_delete=models.CASCADE,
                             related_name='basket_positions'
                             )
    position = models.ForeignKey(ProductInShop,
                                 on_delete=models.CASCADE,
                                 related_name='basket_positions',
                                 verbose_name='Позиция к заказу'
                                 )
    quantity = models.PositiveIntegerField(verbose_name='Количество')

    class Meta:
        verbose_name = 'Позиция корзины для заказа'
        verbose_name_plural = 'Список позиций корзины для заказа'
        constraints = [
            models.UniqueConstraint(fields=['user', 'position'], name='unique_basket_position')
        ]


class Order(models.Model):
    user = models.ForeignKey(User,
                             verbose_name='Покупатель',
                             on_delete=models.CASCADE,
                             related_name='orders'
                             )
    created_at = models.DateTimeField(auto_now_add=True)
    state = models.CharField(max_length=20, verbose_name='Статус', choices=STATE_CHOICES)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, blank=True, null=True, verbose_name='Контакт')

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Список заказов'
        ordering = ('-created_at', )


class OrderPosition(models.Model):
    order = models.ForeignKey(Order,
                             verbose_name='Заказ',
                             on_delete=models.CASCADE,
                             related_name='order_positions'
                             )
    position = models.ForeignKey(ProductInShop,
                                 on_delete=models.CASCADE,
                                 related_name='order_positions',
                                 verbose_name='Позиция заказа'
                                 )
    quantity = models.PositiveIntegerField(verbose_name='Количество')

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Список позиций заказа'
        constraints = [
            models.UniqueConstraint(fields=['order', 'position'], name='unique_order_position')
        ]
