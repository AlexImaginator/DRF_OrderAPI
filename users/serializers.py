from djoser.serializers import UserSerializer
from .models import User, Contact
import shop_backend.serializers as sh_bck
from djoser.conf import settings
from rest_framework import serializers


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ('id', 'country', 'city', 'street', 'house', 'structure', 'building', 'apartment', 'phone', 'user')
        read_only_fields = ('id',)
        extra_kwargs = {
            'user': {'write_only': True}
        }


class UserPatchSerializer(UserSerializer):
    contacts = ContactSerializer(read_only=True, many=True)

    class Meta:
        model = User
        fields = [settings.LOGIN_FIELD, 'username', 'first_name', 'last_name',
                  'company', 'position', 'type', 'contacts']
        read_only_fields = (settings.LOGIN_FIELD, 'type')
