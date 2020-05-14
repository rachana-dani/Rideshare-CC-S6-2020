from django.db import models
from django.utils import timezone
import datetime

class User(models.Model):
    username = models.CharField(max_length=50, primary_key=True)
    password = models.CharField(max_length=40)
    def __str__(self):
        return self.username
