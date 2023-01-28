from djoser.serializers import UserSerializer
from .models import User
from djoser.conf import settings


class UserPatchSerializer(UserSerializer):
    class Meta:
        model = User
        fields = [settings.LOGIN_FIELD, 'username', 'first_name', 'last_name', 'company', 'position', 'type']
        read_only_fields = (settings.LOGIN_FIELD, 'type')
