from rest_framework import serializers
from .models import Shop, Category, Product, ProductInShop, ProductParameter


class ShopSerializer(serializers.ModelSerializer):

    class Meta:
        model = Shop
        fields = ('id', 'name', 'url', 'state', 'user')
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


class ProductInShopSerializer(serializers.ModelSerializer):
    shop = ShopSerializer(read_only=True)
    product = ProductSerializer(read_only=True)

    class Meta:
        model = ProductInShop
        fields = ['id', 'shop', 'product', 'model', 'price', 'quantity']
        read_only_fields = ('id', )


class ProductParameterSerializer(serializers.ModelSerializer):
    parameter = serializers.StringRelatedField()

    class Meta:
        model = ProductParameter
        fields = ['parameter', 'value']
