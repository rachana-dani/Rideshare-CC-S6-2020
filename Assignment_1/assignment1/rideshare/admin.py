from django.contrib import admin

from .models import  User, User_rides, Ride
admin.site.register(User)
admin.site.register(User_rides)
admin.site.register(Ride)

