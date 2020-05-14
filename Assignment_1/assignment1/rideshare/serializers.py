from rest_framework import serializers,fields
from rest_framework.serializers import PrimaryKeyRelatedField
from .models import User, Ride, User_rides

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class RideSerializer(serializers.ModelSerializer):
    username = PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = Ride
        fields = "__all__"

class User_rideSerializer(serializers.ModelSerializer):
    username = PrimaryKeyRelatedField(queryset=User.objects.all())
    ride_id = PrimaryKeyRelatedField(queryset=Ride.objects.all())
    class Meta:
        model = User_rides
        fields = '__all__'


'''
class ItemSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    class Meta:
        model = Item
        fields = "__all__"
'''