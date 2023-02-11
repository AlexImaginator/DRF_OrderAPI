from rest_framework.routers import DefaultRouter
from .views import ShopViewSet, ShopPricelistUpdate
from django.urls import path


router_shops = DefaultRouter()
router_shops.register('', ShopViewSet)
urlpatterns = [
    path('pricelistupdate/', ShopPricelistUpdate.as_view())
              ] + router_shops.urls
