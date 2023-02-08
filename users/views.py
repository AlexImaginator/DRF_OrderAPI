from .models import Contact
from .serializers import ContactSerializer
from rest_framework.viewsets import ModelViewSet
from .permissions import IsOwnerOrReadOnly
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


class ContactViewSet(ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def list(self, request):
        queryset = Contact.objects.filter(user=self.request.user)
        serializer = ContactSerializer(queryset, many=True)
        return Response(serializer.data)
