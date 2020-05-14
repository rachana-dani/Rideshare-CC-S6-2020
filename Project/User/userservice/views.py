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

ip_address="35.171.9.165"
user_port = "80"
ride_port = "80"
orchestrator_port = "80"
user_ip = "3.89.23.216"
ride_ip = "54.198.128.17"
orchestrator_ip_address = "54.196.45.48"
load_balancer = "rideservice-1928015168.us-east-1.elb.amazonaws.com"

def update_request_count():
    f = open("/rideshare/userservice/request_counts.txt", "r")
    request_count = f.read()
    f.close()
    if(request_count == ""):
        request_count = str(1)
    else:
        request_count = str(int(request_count)+1)
    f = open("/rideshare/userservice/request_counts.txt", "w")
    f.write(request_count)
    f.close()
    print(request_count, "done")

ALLOWED_METHODS_LIST = ["PUT", "POST", "GET", "HEAD", "DELETE", "CONNECT", "OPTIONS", "TRACE", "PATCH"]
   

class usersList(APIView):
    def get(self, request):
        update_request_count()
        users = requests.post("http://"+orchestrator_ip_address+":"+orchestrator_port+"/api/v1/db/read",json={"table":"user"})
        #users = requests.post("http://"+ip_address+":"+user_port+"/api/v1/db/read",json={"table":"User"}) 
        users = users.json()
        #print(users,type(users))
        print(users)
        if(len(users) < 1):
            return Response({}, status=status.HTTP_204_NO_CONTENT)
        users = [i["username"] for i in users]
        return Response(users, status=status.HTTP_200_OK)
    def put(self,request):
        update_request_count()
        print(request.data)
        if(re_password.match(request.data["password"])): 
            users_list = requests.get("http://"+load_balancer +":"+user_port+"/api/v1/users")
            if users_list.status_code!=200:
                users_list = []
            else:
                 users_list = users_list.json()
            print(request.data["username"])   
            user = request.data["username"]
            print(type(user),type(users_list))
            if user in users_list:
                print("in if") 
                return Response({}, status=status.HTTP_400_BAD_REQUEST)
            r=requests.post("http://"+orchestrator_ip_address+":"+orchestrator_port+"/api/v1/db/write",json={"table":"user","data":request.data,"type":"insert","clear":"0"})
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
        if len(user_)==0: 
            return Response({},status=status.HTTP_400_BAD_REQUEST)
        else:
            user_.delete()
            rides = requests.post("http://"+orchestrator_ip_address+":"+orchestrator_port+"/api/v1/delete_user", json={"username": user})
            if(rides.status_code == 200):
                return Response({},status=status.HTTP_200_OK)
        return Response({},status=status.HTTP_400_BAD_REQUEST)
    def options(self, request):
        update_request_count()
        return Response({}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    def trace(self, request):
        update_request_count()
        return Response({}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    def head(self, request):
        update_request_count()
        return Response({}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    def connect(self, request):
        update_request_count()
        return Response({}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    def patch(self, request):
        update_request_count()
        return Response({}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    def post(self, request):
        update_request_count()
        return Response({}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


class Db_clear(APIView):
    def post(self, request):
        update_request_count()
        #User_rides.objects.all().delete()
        #Ride.objects.all().delete()
        r1=requests.post("http://"+orchestrator_ip_address+":"+orchestrator_port+"/api/v1/db/clear",json={"clear":"1"})
        if r1.status_code ==200:
            return Response({}, status=status.HTTP_200_OK)
        else:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)

class table_list(APIView):
    def post(self, request):
        print(request.data)
        table = request.data["table"]
        if(table == "User"):
            users = User.objects.all()
            serializer = UserSerializer(users, many = True)
            users_list = list(map(lambda x: x, serializer.data))
            return Response(users_list, status = status.HTTP_200_OK)
        elif(table == "Ride"):
            rides = Ride.objects.all()
            serializer = RideSerializer(rides, many = True)
            return Response(serializer.data, status = status.HTTP_200_OK)
        elif(table == "User_rides"):
            user_rides = User_rides.objects.all()
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
        f = open("/rideshare/userservice/request_counts.txt", "r")
        count = f.read()
        if(count == ""):
            return Response([0], status = status.HTTP_200_OK)
        return Response([int(count)], status = status.HTTP_200_OK)
    def delete(self, request):
        f = open("/rideshare/userservice/request_counts.txt", 'w')
        f.write("")
        f.close()
        return Response({}, status = status.HTTP_200_OK)
    def post(self, request):
        update_request_count()
        return Response({}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    def options(self, request):
        update_request_count()
        return Response({}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    def trace(self, request):
        update_request_count()
        return Response({}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    def head(self, request):
        update_request_count()
        return Response({}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    def connect(self, request):
        update_request_count()
        return Response({}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    def patch(self, request):
        update_request_count()
        return Response({}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    def put(self, request):
        update_request_count()
        return Response({}, status=status.HTTP_405_METHOD_NOT_ALLOWED)