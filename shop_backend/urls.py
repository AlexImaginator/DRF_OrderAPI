from rest_framework.routers import DefaultRouter
from .views import ShopViewSet


router_shops = DefaultRouter()
router_shops.register('', ShopViewSet)
urlpatterns = router_shops.urls
