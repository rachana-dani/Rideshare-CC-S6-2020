from django.db import models
from django.utils import timezone
import datetime

class User(models.Model):
    username = models.CharField(max_length=50, primary_key=True)
    password = models.CharField(max_length=40)
    def __str__(self):
        return self.username

class Ride(models.Model):
    ride_id = models.IntegerField(primary_key = True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    timestamp = models.DateTimeField(max_length=30)
    source = models.IntegerField()
    destination = models.IntegerField()

    def __str__(self):
        return str(self.ride_id)

class User_rides(models.Model):
    username = models.ForeignKey(User, on_delete=models.CASCADE)
    ride_id = models.ForeignKey(Ride, on_delete=models.CASCADE)
    class Meta:
        unique_together = ['username', 'ride_id']
    def __str__(self):
        return str(self.username)+str(self.ride_id)




""""
{
	"insert":{
        "ride_id": 101,
        "created_by": "u2",
        "timestamp": "2022-01-15 06:35:34",
        "source": 10,
        "destination": 15
    },
    "table": "Ride"
	
}


{
	"insert":{
        "username": "u1",
        "password":"u1"
    },
    "table": "User"
	
}
"""