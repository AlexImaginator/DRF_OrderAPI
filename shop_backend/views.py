from rest_framework.viewsets import ModelViewSet
from .models import Shop
from .serializers import ShopSerializer
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsOwnerOrReadOnly
from rest_framework.validators import ValidationError


class ShopViewSet(ModelViewSet):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        if self.request.user.type == 'shop':
            serializer.save(user=self.request.user)
        else:
            raise ValidationError('Only shop_users can create shops')
