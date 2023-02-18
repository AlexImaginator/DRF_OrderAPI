from rest_framework.routers import DefaultRouter
from .views import ShopViewSet, ShopPricelistUpdate, CategoryView, ShopsListView, ProductInShopView, BasketView
from django.urls import path


router_shops = DefaultRouter()
router_shops.register('shopsmanage', ShopViewSet)
urlpatterns = [
    path('pricelistupdate/', ShopPricelistUpdate.as_view()),
    path('categories/', CategoryView.as_view()),
    path('shops/', ShopsListView.as_view()),
    path('products/', ProductInShopView.as_view()),
    path('basket/', BasketView.as_view())
              ] + router_shops.urls
