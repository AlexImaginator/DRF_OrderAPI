from djoser.serializers import UserSerializer
from .models import User, Contact
from djoser.conf import settings
from rest_framework import serializers


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ('id', 'country', 'city', 'street', 'house', 'structure', 'building', 'apartment', 'phone', 'user')
        read_only_fields = ('user',)


class UserPatchSerializer(UserSerializer):
    contacts = ContactSerializer(read_only=True, many=True)

    class Meta:
        model = User
        fields = [settings.LOGIN_FIELD, 'username', 'first_name', 'last_name',
                  'company', 'position', 'type', 'contacts']
        read_only_fields = (settings.LOGIN_FIELD, 'type')
