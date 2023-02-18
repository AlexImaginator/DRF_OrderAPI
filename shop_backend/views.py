from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from .models import Shop, Category, ProductInShop, Product, Parameter, ProductParameter, BasketPosition
from .serializers import ShopSerializer, ShopListSerializer, CategorySerializer, ProductInShopSerializer, \
    BasketPositionSerializer
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsOwnerOrReadOnly
from rest_framework.validators import ValidationError
from rest_framework.response import Response
from django.http import JsonResponse
from django.db.models import Q
from requests import get as get_data
from yaml import load as load_yaml, Loader
from django.core.exceptions import ObjectDoesNotExist


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


class ShopsListView(ListAPIView):

    queryset = Shop.objects.all()
    serializer_class = ShopListSerializer


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
        Product.objects.filter(products_in_shops__isnull=True).delete()
        Parameter.objects.filter(product_parameters__isnull=True).delete()
        for item in data['Products']:
            product_object, _ = Product.objects.get_or_create(name=item['name'],
                                                              category=Category.objects.get(name=item['category']))
            product_in_shop_object = ProductInShop.objects.create(product=product_object,
                                                                     shop=shop,
                                                                     model=item['model'],
                                                                     price=item['price'],
                                                                     quantity=item['quantity'])
            for name, value in item['parameters'].items():
                parameter_object, _ = Parameter.objects.get_or_create(name=name)
                ProductParameter.objects.create(product_in_shop=product_in_shop_object,
                                                parameter=parameter_object,
                                                value=value
                                                )
        return JsonResponse({'Status': True, 'Message': 'Pricelist updated'})


class CategoryView(ListAPIView):

    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ProductInShopView(APIView):

    def get(self, request):
        query = Q(shop__state=True)
        shop_id = request.query_params.get('shop_id')
        category_id = request.query_params.get('category_id')
        if shop_id:
            query = query & Q(shop_id=shop_id)
        if category_id:
            query = query & Q(product__category_id=category_id)
        queryset = ProductInShop.objects.filter(query).select_related(
            'shop', 'product__category').prefetch_related(
            'product_parameters__parameter').distinct()
        serializer = ProductInShopSerializer(queryset, many=True)
        return Response(serializer.data)


class BasketView(APIView):

    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in is required'}, status=403)
        if request.user.type != 'buyer':
            return JsonResponse({'Status': False, 'Error': 'Only for buyers'}, status=403)
        positions_to_add_list = []
        for item in self.request.data:
            try:
                position = ProductInShop.objects.get(id=item['position'])
            except:
                return JsonResponse({'Status': False, 'Error': f'No such position id = {item["position"]}'})
            quantity = item['quantity']
            if quantity > position.quantity:
                return JsonResponse({'Status': False, 'Error': f'Quantity of {position.product} is '
                                                               f'{quantity}, {position.quantity} is available'})
            basket_position_object = BasketPosition.objects.filter(user=self.request.user, position=position).first()
            if not basket_position_object:
                position_to_add = BasketPosition(user=self.request.user, position=position, quantity=quantity)
                positions_to_add_list.append(position_to_add)
            elif basket_position_object.quantity + quantity <= position.quantity:
                basket_position_object.quantity += quantity
                basket_position_object.save()
            else:
                return JsonResponse({'Status': False,
                                     'Error': f'Can not add {quantity} {position.product} in your basket, '
                                              f'{position.quantity - basket_position_object.quantity} is available'})
        for position_object in positions_to_add_list:
            position_object.save()
        return JsonResponse({'Status': True, 'Message': 'Added to Basket'})

    def get(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in is required'}, status=403)
        if request.user.type != 'buyer':
            return JsonResponse({'Status': False, 'Error': 'Only for buyers'}, status=403)
        queryset = BasketPosition.objects.filter(user=self.request.user)
        serializer = BasketPositionSerializer(queryset, many=True)
        return Response(serializer.data)

    def patch(self, request):
        pass

    def delete(self, request):
        pass
