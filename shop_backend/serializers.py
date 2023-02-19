from rest_framework import serializers
from .models import Shop, Category, Product, ProductInShop, ProductParameter, BasketPosition, Order, OrderPosition
from users.serializers import ContactSerializer


class ShopSerializer(serializers.ModelSerializer):

    class Meta:
        model = Shop
        fields = ('id', 'name', 'url', 'state', 'user')
        read_only_fields = ('user',)


class ShopListSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = Shop
        fields = ('id', 'name', 'user')
        read_only_fields = ('user',)


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ['id', 'name']
        read_only_fields = ['id', ]


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = ['name', 'category']


class ProductParameterSerializer(serializers.ModelSerializer):
    parameter = serializers.StringRelatedField()

    class Meta:
        model = ProductParameter
        fields = ['parameter', 'value']


class ProductInShopSerializer(serializers.ModelSerializer):
    shop = ShopListSerializer(read_only=True)
    product = ProductSerializer(read_only=True)
    product_parameters = ProductParameterSerializer(read_only=True, many=True)

    class Meta:
        model = ProductInShop
        fields = ['id', 'shop', 'product', 'model', 'price', 'quantity', 'product_parameters']
        read_only_fields = ('id', )


class PositionSerializer(serializers.ModelSerializer):
    shop = ShopListSerializer(read_only=True)
    product = ProductSerializer(read_only=True)

    class Meta:
        model = ProductInShop
        fields = ['id', 'shop', 'product', 'model', 'price']
        read_only_fields = ('id', )


class BasketPositionSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    position = PositionSerializer(read_only=True)
    cost = serializers.DecimalField(max_digits=11, decimal_places=2)

    class Meta:
        model = BasketPosition
        fields = ['id', 'user', 'position', 'quantity', 'cost']
        read_only_fields = ('id', )


class OrderSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    contact = ContactSerializer(read_only=True, many=True)
    class Meta:
        model = Order
        fields = ['id', 'user', 'created_at', 'state', 'contact']
        read_only_fields = ('id',)


class OrderPositionSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)
    position = PositionSerializer(read_only=True)
    cost = serializers.DecimalField(max_digits=11, decimal_places=2)

    class Meta:
        model = BasketPosition
        fields = ['id', 'order', 'position', 'quantity', 'cost']
        read_only_fields = ('id', )
