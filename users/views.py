from django.http import JsonResponse
from rest_framework.views import APIView

from .serializers import ContactSerializer


class ContactView(APIView):
    def get(self, request, *args, **kwargs):
        return JsonResponse({'Status': 'OK', 'Page': 'GetUserContacts'})

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        if {'country', 'city', 'street', 'phone'}.issubset(request.data):
            request.data._mutable = True
            request.data.update({'user': request.user.id})
            serializer = ContactSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({'Status': True})
            else:
                return JsonResponse({'Status': False, 'Errors': serializer.errors})
        else:
            return JsonResponse({'Status': False, 'Errors': 'Не указаны необходимые аргументы'})
