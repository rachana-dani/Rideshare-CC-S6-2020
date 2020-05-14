from rest_framework import serializers,fields
from rest_framework.serializers import PrimaryKeyRelatedField
from .models import Ride, User_rides

class RideSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ride
        fields = "__all__"

class User_rideSerializer(serializers.ModelSerializer):
    ride_id = PrimaryKeyRelatedField(queryset=Ride.objects.all())
    class Meta:
        model = User_rides
        fields = '__all__'
