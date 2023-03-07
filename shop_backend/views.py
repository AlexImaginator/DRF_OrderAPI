from collections import OrderedDict
from _decimal import Decimal
from requests import get as get_data
from yaml import load as load_yaml, Loader
from django.http import JsonResponse
from django.db.models import Q, F
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.validators import ValidationError
from rest_framework.response import Response
from .models import Shop, Category, ProductInShop, Product, Parameter, ProductParameter, BasketPosition, \
    Order, OrderPosition
from users.models import Contact
from .serializers import ShopSerializer, ShopListSerializer, CategorySerializer, ProductInShopSerializer, \
    BasketPositionSerializer, OrderSerializer, OrderPositionSerializer
from users.permissions import IsOwnerOrReadOnly
from .signals import new_order, orders_in_shop, order_status_change


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
        queryset = BasketPosition.objects.filter(
            user=self.request.user
            ).select_related(
            'user', 'position__shop', 'position__product'
            ).annotate(cost=F('quantity')*F('position__price'))
        serializer = BasketPositionSerializer(queryset, many=True)
        data_to_response = serializer.data
        total_sum = 0
        for item in data_to_response:
            total_sum += Decimal(item['cost'])
        basket_total_sum = [OrderedDict([('basket_total_sum', total_sum)])]
        data_to_response += basket_total_sum
        return Response(data_to_response)

    def patch(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in is required'}, status=403)
        if request.user.type != 'buyer':
            return JsonResponse({'Status': False, 'Error': 'Only for buyers'}, status=403)
        unsearched_positions = []
        for item in self.request.data:
            try:
                basket_position = BasketPosition.objects.get(id=item['position'])
                product_in_shop_obj = ProductInShop.objects.get(id=basket_position.position.id)
                quantity_available = product_in_shop_obj.quantity
                if item['quantity'] <= quantity_available:
                    basket_position.quantity = item['quantity']
                    basket_position.save()
                else:
                    error_msg = f'{item["position"]} position {quantity_available} is available'
                    unsearched_positions.append(error_msg)
            except:
                error_msg = f'No {item["position"]} position in your basket'
                unsearched_positions.append(error_msg)
        return JsonResponse({'Status': True,
                             'Message': 'Complete',
                             'Errors': unsearched_positions})

    def delete(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in is required'}, status=403)
        if request.user.type != 'buyer':
            return JsonResponse({'Status': False, 'Error': 'Only for buyers'}, status=403)
        unsearched_positions = []
        for item in self.request.data:
            try:
                basket_position = BasketPosition.objects.get(id=item['position'])
                basket_position.delete()
            except:
                error_msg = f'No {item["position"]} position in your basket'
                unsearched_positions.append(error_msg)
        return JsonResponse({'Status': True,
                                 'Message': 'Complete',
                                 'Errors': unsearched_positions})


class OrderView(APIView):

    def post(self, request):
        '''
        Только для покупателей.
        Заказать товары, которые находятся в корзине покупателя.
        '''
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in is required'}, status=403)
        if request.user.type != 'buyer':
            return JsonResponse({'Status': False, 'Error': 'Only for buyers'}, status=403)
        basket_queryset = BasketPosition.objects.filter(user=self.request.user).select_related('position')
        if basket_queryset:
            contact_obj = Contact.objects.filter(user=self.request.user).first()
            shop_list = []
            new_orders_msg_list = []
            for item in basket_queryset:
                if item.position.shop.id not in shop_list:
                    shop_list.append(item.position.shop.id)
            for shop in shop_list:
                order_obj = Order.objects.create(user=self.request.user,
                                                 state='new',
                                                 contact=contact_obj
                                                 )
                new_order_msg = {'Shop': getattr(Shop.objects.get(pk=shop), 'name'), 'Order ID': order_obj.id}
                new_orders_msg_list.append(new_order_msg)
                for basket_position in basket_queryset:
                    if basket_position.position.shop.id == shop:
                        OrderPosition.objects.create(order=order_obj,
                                                     position=basket_position.position,
                                                     quantity=basket_position.quantity
                                                     )
            basket_queryset.delete()
            new_order.send(sender=self.__class__, user_id=request.user.id, orders=new_orders_msg_list)
            return JsonResponse({'Status': True, 'Message': 'Order created', 'Content': new_orders_msg_list})
        else:
            return JsonResponse({'Status': False, 'Message': 'Your basket is empty.'})

    def get(self, request):
        '''
        Только для продавцов.
        Получить заказы из своих магазинов.
        Фильтрация по статусу заказа и по id магазина.
        '''
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in is required'}, status=403)
        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Only for shops'}, status=403)
        shop_list = list(Shop.objects.values_list('id', flat=True).filter(user=self.request.user))
        shop_id = request.query_params.get('shop_id')
        if shop_id is not None and int(shop_id) not in shop_list:
            return JsonResponse({'Status': False, 'Error': f'You have not shop with id = {shop_id}'}, status=403)
        elif shop_id is not None:
            shop_list = [int(shop_id), ]
        order_state = request.query_params.get('order_state')
        if order_state is None:
            order_state = 'new'
        context = []
        for shop in shop_list:
            orders = Order.objects.filter(state=order_state,
                                          order_positions__position__shop_id=shop
                                          ).distinct()
            for order in orders:
                order_positions = OrderPosition.objects.filter(order=order).prefetch_related()
                positions_list = []
                for position in order_positions:
                    product = position.position.product.name
                    model = position.position.model
                    price = position.position.price
                    quantity = position.position.quantity
                    position_description = {'product': product, 'model': model, 'price': price, 'quantity': quantity}
                    positions_list.append(position_description)
                order_description = {
                    'shop_id': shop,
                    'order_id': order.id,
                    'order_state': order.state,
                    'order_created_at': order.created_at,
                    'order_user': str(order.user),
                    'order_contact': str(order.contact),
                    'order_positions': positions_list
                    }
                context.append(order_description)
        orders_in_shop.send(sender=self.__class__, user_id=request.user.id, context=context)
        return JsonResponse({'Status': True, 'Message': 'Orders recieved', 'Content': context})

    def patch(self, request):
        '''
        Только для продавцов.
        Изменить статус заказа.
        '''
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in is required'}, status=403)
        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Only for shops'}, status=403)
        orders_list = list(Order.objects.values_list('id', flat=True).filter(
            order_positions__position__shop__user__id=request.user.id).distinct()
                           )
        try:
            order_to_patch = int(request.data['order_id'])
        except:
            return JsonResponse({'Status': False, 'Error': 'Order id is required'}, status=403)
        if order_to_patch not in orders_list:
            return JsonResponse({'Status': False,
                                 'Error': f'You have not order {request.data["order_id"]}'
                                 },
                                status=403
                                )
        try:
            new_state = request.data['state']
        except:
            return JsonResponse({'Status': False, 'Error': 'New state is required'}, status=403)
        states_choices = ['confirmed', 'assembled', 'sent', 'delivered', 'canceled']
        if new_state not in states_choices:
            return JsonResponse({'Status': False, 'Error': 'Forbidden new state'})
        order_obj = Order.objects.get(id=order_to_patch)
        if order_obj.state == 'new':
            order_obj.state = new_state
            order_obj.save()
            order_status_change.send(sender=self.__class__,
                                     user_id=order_obj.user.id,
                                     order_id=order_obj.id,
                                     new_state=new_state
                                     )
        elif order_obj.state == 'confirmed':
            if new_state in states_choices[1:]:
                order_obj.state = new_state
                order_obj.save()
                order_status_change.send(sender=self.__class__,
                                         user_id=order_obj.user.id,
                                         order_id=order_obj.id,
                                         new_state=new_state
                                         )
            else:
                return JsonResponse({'Status': False, 'Error': 'Forbidden new state'})
        elif order_obj.state == 'assembled':
            if new_state in states_choices[2:]:
                order_obj.state = new_state
                order_obj.save()
                order_status_change.send(sender=self.__class__,
                                         user_id=order_obj.user.id,
                                         order_id=order_obj.id,
                                         new_state=new_state
                                         )
            else:
                return JsonResponse({'Status': False, 'Error': 'Forbidden new state'})
        elif order_obj.state == 'sent':
            if new_state in states_choices[3:]:
                order_obj.state = new_state
                order_obj.save()
                order_status_change.send(sender=self.__class__,
                                         user_id=order_obj.user.id,
                                         order_id=order_obj.id,
                                         new_state=new_state
                                         )
            else:
                return JsonResponse({'Status': False, 'Error': 'Forbidden new state'})
        else:
            return JsonResponse({'Status': False, 'Error': 'Forbidden new state'})
        return JsonResponse({'Status': True, 'Message': f'Order {order_to_patch} is patched. State: {new_state}'})
