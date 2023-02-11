from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from .models import Shop, Category
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
        shop = Shop.objects.filter(user=request.user, name=request.data['shop_to_update'])
        shop = shop[0]
        url = shop.url
        stream = get_data(url).content
        data = load_yaml(stream, Loader=Loader)
        for category in data['Categories']:
            category_object, _ = Category.objects.get_or_create(name=category['name'])
            category_object.shops.add(shop.id)
            category_object.save()
        print(data)
        return JsonResponse({'Status': True, })
