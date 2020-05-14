from rest_framework import serializers,fields
from rest_framework.serializers import PrimaryKeyRelatedField
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

