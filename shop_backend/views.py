from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from .models import Shop, Category, ProductInShop, Product
from .serializers import ShopSerializer
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsOwnerOrReadOnly
from rest_framework.validators import ValidationError
from rest_framework.response import Response
from django.http import JsonResponse
from requests import get as get_data
from yaml import load as load_yaml, Loader


class ShopViewSet(ModelViewSet):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        if self.request.user.type == 'shop':
            shop_names = Shop.objects.filter(user=self.request.user).values_list('name')
            shop_names_list = [shop_name[0] for shop_name in shop_names]
            if self.request.data['name'] in shop_names_list:
                raise ValidationError('The Shop is already exists')
            serializer.save(user=self.request.user)
        else:
            raise ValidationError('Only shop_users can create shops')

    def list(self, request):
        queryset = Shop.objects.filter(user=self.request.user)
        serializer = ShopSerializer(queryset, many=True)
        return Response(serializer.data)


class ShopPricelistUpdate(APIView):
    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in is required'}, status=403)
        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Only for sellers'}, status=403)
        shop = Shop.objects.get(user=request.user, name=request.data['shop_to_update'])
        url = shop.url
        stream = get_data(url).content
        data = load_yaml(stream, Loader=Loader)
        category_list = [category['name'] for category in data['Categories']]
        categories_to_remove = Category.objects.filter(shops=shop.id).exclude(name__in=category_list)
        if categories_to_remove:
            for category in categories_to_remove:
                category.shops.remove(shop.id)
                category.save()
        Category.objects.filter(shops__isnull=True).delete()
        for category in data['Categories']:
            category_object, _ = Category.objects.get_or_create(name=category['name'])
            category_object.shops.add(shop.id)
            category_object.save()
        ProductInShop.objects.filter(shop=shop).delete()
        for item in data['Products']:
            product_object, _ = Product.objects.get_or_create(name=item['name'],
                                                              category=Category.objects.get(name=item['category']))
            product_in_shop_object = ProductInShop.objects.create(product=product_object,
                                                                     shop=shop,
                                                                     model=item['model'],
                                                                     price=item['price'],
                                                                     quantity=item['quantity'])
        return JsonResponse({'Status': True, })
