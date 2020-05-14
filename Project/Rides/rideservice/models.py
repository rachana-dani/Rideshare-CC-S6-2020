from django.db import models
from django.utils import timezone
import datetime


class Ride(models.Model):
    ride_id = models.IntegerField(primary_key=True)
    created_by = models.CharField(max_length=50)
    timestamp = models.DateTimeField(max_length=30)
    source = models.IntegerField()
    destination = models.IntegerField()

    def __str__(self):
        return str(self.ride_id)

class User_rides(models.Model):
    username = models.CharField(max_length=50)
    ride_id = models.ForeignKey(Ride, on_delete=models.CASCADE)
    class Meta:
        unique_together = ['username', 'ride_id']
    def __str__(self):
        return str(self.username)+str(self.ride_id)
