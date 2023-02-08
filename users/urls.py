from django.urls import path, include
from .views import ContactViewSet
from rest_framework.routers import DefaultRouter


router_contacts = DefaultRouter()
router_contacts.register('user/contacts', ContactViewSet)

urlpatterns = [
    path('', include('djoser.urls')),
    path('', include('djoser.urls.authtoken')),
] + router_contacts.urls
