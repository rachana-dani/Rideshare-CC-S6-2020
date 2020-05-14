from django.shortcuts import render

from django.http import HttpResponse
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.decorators import api_view
from .models import  User
from .serializers import UserSerializer
from rest_framework.response import Response
import requests
import json
import datetime
from rest_framework.decorators import api_view
import re
import pandas as pd
from django.core.serializers import serialize
import os
re_password = re.compile("^[0-9A-Fa-f]{40}$")

ip_address="172.17.0.1"
user_port = "8080"
ride_port = "8000"

def update_request_count():
    f = open("/home/ubuntu/User/userservice/request_counts.txt", "r")
    request_count = f.read()
    f.close()
    if(request_count == ""):
        request_count = str(1)
    else:
        request_count = str(int(request_count)+1)
    f = open("/home/ubuntu/User/userservice/request_counts.txt", "w")
    f.write(request_count)
    f.close()

ALLOWED_METHODS_LIST = ["PUT", "POST", "GET", "HEAD", "DELETE", "CONNECT", "OPTIONS", "TRACE", "PATCH"]
   

class usersList(APIView):
    def get(self, request):
        update_request_count()
        users = User.objects.all()
        serializer = UserSerializer(users, many = True)
        users_list = list(map(lambda x: x["username"], serializer.data))
        print(__file__)
        if(len(users_list) < 1):
            return Response( status=status.HTTP_204_NO_CONTENT)
        return Response(users_list, status=status.HTTP_200_OK)
    def put(self,request):
        update_request_count()
        print(request.data)
        if(re_password.match(request.data["password"])):
            r=requests.post("http://"+ip_address+":"+user_port+"/api/v1/db/write",json={"table":"User","insert":request.data})
            if (r.status_code==200):
                return Response({},status=status.HTTP_201_CREATED)
            else:
                return Response({},status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({},status=status.HTTP_400_BAD_REQUEST)
    def delete(self,request,user,format=None):
        update_request_count()
        print(user)
        user_ = User.objects.filter(username=user)
        rides = requests.post("http://"+ip_address+":"+ride_port+"/api/v1/delete_user", json={"username": user})
        if len(user_)==0 or rides.status_code!=200: 
            return Response({},status=status.HTTP_400_BAD_REQUEST)
        else:
            user_.delete()
            return Response({},status=status.HTTP_200_OK)
    def options(self, request):
        update_request_count()
        return Response({}, status=status.HTTP_METHOD_NOT_ALLOWED)
    def trace(self, request):
        update_request_count()
        return Response({}, status=status.HTTP_METHOD_NOT_ALLOWED)
    def head(self, request):
        update_request_count()
        return Response({}, status=status.HTTP_METHOD_NOT_ALLOWED)
    def connect(self, request):
        update_request_count()
        return Response({}, status=status.HTTP_METHOD_NOT_ALLOWED)
    def patch(self, request):
        update_request_count()
        return Response({}, status=status.HTTP_METHOD_NOT_ALLOWED)
    def post(self, request):
        update_request_count()
        return Response({}, status=status.HTTP_METHOD_NOT_ALLOWED)


class Db_clear(APIView):
    def post(self, request):
        update_request_count()
        User.objects.all().delete()
        r = requests.post("http://"+ip_address+":"+ride_port+"/api/v1/db/clear")
        return Response({}, status=status.HTTP_200_OK)
    def get(self, request):
        update_request_count()
        return Response({}, status=status.HTTP_METHOD_NOT_ALLOWED)
    def options(self, request):
        update_request_count()
        return Response({}, status=status.HTTP_METHOD_NOT_ALLOWED)
    def trace(self, request):
        update_request_count()
        return Response({}, status=status.HTTP_METHOD_NOT_ALLOWED)
    def head(self, request):
        update_request_count()
        return Response({}, status=status.HTTP_METHOD_NOT_ALLOWED)
    def connect(self, request):
        update_request_count()
        return Response({}, status=status.HTTP_METHOD_NOT_ALLOWED)
    def patch(self, request):
        update_request_count()
        return Response({}, status=status.HTTP_METHOD_NOT_ALLOWED)
    def put(self, request):
        update_request_count()
        return Response({}, status=status.HTTP_METHOD_NOT_ALLOWED)
    def delete(self, request):
        update_request_count()
        return Response({}, status=status.HTTP_METHOD_NOT_ALLOWED)

class table_list(APIView):
    def post(self, request):
        print(request.data)
        table = request.data["table"]
        columns = ", ".join(request.data["columns"])
        where = request.data["where"].split("=")
        where = where[0]+" = '"+ where[1] +"';"
        query = "SELECT "+ columns +" FROM "+ "userservice_"+table + " WHERE " + where
        if(table == "User"):
            users = User.objects.raw(query)
            serializer = UserSerializer(users, many = True)
            return Response(serializer.data, status = status.HTTP_200_OK)
        elif(table == "Ride"):
            rides = Ride.objects.raw(query)
            serializer = RideSerializer(rides, many = True)
            return Response(serializer.data, status = status.HTTP_200_OK)
        elif(table == "User_rides"):
            user_rides = User_rides.objects.raw(query)
            serializer = User_rideSerializer(user_rides, many = True)
            return Response(serializer.data, status = status.HTTP_200_OK)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)


class table_write(APIView):
    def post(self, request):
        print(request.data)
        table = request.data["table"]
        if(table == "User"):
            serializer = UserSerializer(data = request.data["insert"])
            if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status = status.HTTP_200_OK)
        elif(table == "Ride"):
            serializer = RideSerializer(data = request.data["insert"])
            if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status = status.HTTP_200_OK)
            print(serializer.validated_data)
            
        elif(table == "User_rides"):
            serializer = User_rideSerializer(data = request.data["insert"])
            if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status = status.HTTP_200_OK)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

class count_requests(APIView):
    def get(self, request):
        f = open("/home/ubuntu/User/userservice/request_counts.txt", 'r')
        counts_r = f.read()
        if(counts_r == ""):
            counts_r = 0
        else:
            counts_r = int(counts_r)
        f.close()
        return Response([counts_r], status = status.HTTP_200_OK)
    def delete(self, request):
        f = open("/home/ubuntu/User/userservice/request_counts.txt", 'w')
        f.write("")
        f.close()
        return Response({}, status = status.HTTP_200_OK)
    def post(self, request):
        update_request_count()
        return Response({}, status=status.HTTP_METHOD_NOT_ALLOWED)
    def options(self, request):
        update_request_count()
        return Response({}, status=status.HTTP_METHOD_NOT_ALLOWED)
    def trace(self, request):
        update_request_count()
        return Response({}, status=status.HTTP_METHOD_NOT_ALLOWED)
    def head(self, request):
        update_request_count()
        return Response({}, status=status.HTTP_METHOD_NOT_ALLOWED)
    def connect(self, request):
        update_request_count()
        return Response({}, status=status.HTTP_METHOD_NOT_ALLOWED)
    def patch(self, request):
        update_request_count()
        return Response({}, status=status.HTTP_METHOD_NOT_ALLOWED)
    def put(self, request):
        update_request_count()
        return Response({}, status=status.HTTP_METHOD_NOT_ALLOWED)