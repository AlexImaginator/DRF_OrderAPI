from django.urls import path, include
from .views import ContactView

urlpatterns = [
    path('', include('djoser.urls')),
    path('', include('djoser.urls.authtoken')),
    path('user/contacts/', ContactView.as_view()),
]
