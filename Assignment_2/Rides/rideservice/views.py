from django.shortcuts import render

from django.http import HttpResponse
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.decorators import api_view
from .models import  User_rides, Ride
from .serializers import User_rideSerializer, RideSerializer
from rest_framework.response import Response
import requests
import json
import datetime
from rest_framework.decorators import api_view
import re
import pandas as pd
from django.core.serializers import serialize
import os

ip_address="172.17.0.1"
user_port = "8080"
ride_port = "8000"
container="users"

def update_request_count():
    f = open("/home/ubuntu/Rides/rideservice/request_counts.txt", "r")
    request_count = f.read()
    f.close()
    if(request_count == ""):
        request_count = str(1)
    else:
        request_count = str(int(request_count)+1)
    f = open("/home/ubuntu/Rides/rideservice/request_counts.txt", "w")
    f.write(request_count)
    f.close()

ALLOWED_METHODS_LIST = ["PUT", "POST", "GET", "HEAD", "DELETE", "CONNECT", "OPTIONS", "TRACE", "PATCH"]
   

re_password = re.compile("^[0-9A-Fa-f]{40}$")

def string_convert(old_date):
    old_date = old_date.split(":")
    d, m, y = old_date[0].split("-")
    s, mi, h = old_date[1].split("-")
    print(y+"-"+m+"-"+d+" "+h+":"+mi+":"+s)
    return y+"-"+m+"-"+d+" "+h+":"+mi+":"+s

def string_convert_reverse(new_date):
    new_date = new_date.split("T")
    y, m, d = new_date[0].split("-")
    h, mi, s = new_date[1].split(":")
    return d+"-"+m+"-"+y+":"+s[:len(s)-1]+"-"+mi+"-"+h

class count_rides(APIView):
    def get(self, request):
        update_request_count()
        counts_r = len(Ride.objects.all())
        return Response([counts_r], status = status.HTTP_200_OK)
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
    def delete(self, request):
        update_request_count()
        return Response({}, status=status.HTTP_METHOD_NOT_ALLOWED)

class ridesList(APIView):
    def get(self, request):
        update_request_count()
        source = int(request.GET['source'])
        print(__file__)
        destination = int(request.GET['destination'])
        data = pd.read_csv("/rideshare/rideservice/AreaNameEnum.csv")
        print(type(source))
        if (source != destination):
            if(source in data["Area No"]) and (destination in data["Area No"]):
                rides = Ride.objects.filter(source=source, destination=destination, timestamp__gte=datetime.datetime.now())
          
                if(len(rides)==0):
                    return Response({}, status=status.HTTP_204_NO_CONTENT)
                serializer = RideSerializer(rides, many = True)
                for i in range(len(rides)):
                    serializer.data[i]["username"] = serializer.data[i]["created_by"]
                    serializer.data[i]["timestamp"] = string_convert_reverse(serializer.data[i]["timestamp"])
                    serializer.data[i]["rideId"] = serializer.data[i]["ride_id"]
                    del serializer.data[i]["created_by"], serializer.data[i]["source"], serializer.data[i]["destination"], serializer.data[i]["ride_id"]
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({},status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({},status=status.HTTP_400_BAD_REQUEST)
    def post(self,request):
        update_request_count()
        user = request.data["created_by"]
        print(request.data)
        print(__file__)
        data = pd.read_csv("/rideshare/rideservice/AreaNameEnum.csv")
        print(os.getcwd())
        source = int(request.data["source"])
        destination = int(request.data["destination"])
        users_list = requests.get("http://"+ip_address+":"+user_port+"/api/v1/users")
        print("hii",users_list.json())
        if(user not in users_list.json()):
            return Response({}, status=status.HTTP_400_BAD_REQUEST)
        if (source != destination):
            if(source in data["Area No"]) and (destination in data["Area No"]): 
                rides = Ride.objects.all()
                if(len(rides) == 0):
                    count = 1
                else:
                    count = 1 + rides[len(rides)-1].ride_id
                request.data["ride_id"] = count
                request.data["timestamp"] = string_convert(request.data["timestamp"])        
                r=requests.post("http://"+ip_address+":"+ride_port+"/api/v1/db/write",json={"table":"Ride","insert":request.data})
                json_data = {"username":request.data['created_by'], "ride_id":count}
                r2=requests.post("http://"+ip_address+":"+ride_port+"/api/v1/db/write",json={"table":"User_rides","insert":json_data})
                if (r.status_code==200 and r2.status_code==200):
                    return Response({"rideid": count},status=status.HTTP_201_CREATED)
                else:
                    return Response({},status=status.HTTP_400_BAD_REQUEST)
            else:
                    return Response({},status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)
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


class user_ridesList(APIView):
    def get(self,request,ride,format=None):
        update_request_count()
        ride_ = Ride.objects.filter(ride_id=ride)
        if len(ride_)==0:
            return Response({},status=status.HTTP_204_NO_CONTENT)
        else:
            ride_=[i.__dict__ for i in ride_][0]
            # print(ride_)
            user_list = User_rides.objects.filter(ride_id_id=ride)
            user_list=[i.__dict__["username"] for i in user_list]
            user_list.remove(ride_["created_by"])
            # print(user_list)
            x = {"ride_id":ride_["ride_id"],"created_by":ride_["created_by"],"users":user_list
            , "source":ride_["source"],"destination":ride_["destination"],"timestamp":ride_["timestamp"]}
            return Response(x,status=status.HTTP_200_OK)
    def post(self, request, ride):
        update_request_count()
        print("vhjvhgv",request.data)
        ride_id = ride
        username = request.data['username']
        users_list = requests.get("http://"+ip_address+":"+user_port+"/api/v1/users")
        print("hii",users_list.json())
        if(username not in users_list.json()):
            return Response({}, status=status.HTTP_400_BAD_REQUEST)
        json_data = {"username":username, "ride_id":ride_id}
        r1=requests.post("http://"+ip_address+":"+ride_port+"/api/v1/db/write",json={"table":"User_rides","insert":json_data})
        if (r1.status_code==200 ):
            return Response({},status=status.HTTP_201_CREATED)
        else:
            return Response({},status=status.HTTP_400_BAD_REQUEST)
    def delete(self,request,ride,format=None):
        update_request_count()
        ride_ = Ride.objects.filter(ride_id=ride)
        if len(ride_)==0:
            return Response({},status=status.HTTP_204_NO_CONTENT)
        else:
            ride_.delete()
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
    def put(self, request):
        update_request_count()
        return Response({}, status=status.HTTP_METHOD_NOT_ALLOWED)

class delete_ride(APIView):
    def post(self, request):
        update_request_count()
        username = request.data["username"]
        rides = Ride.objects.filter(created_by=username).delete()
        user_rides = User_rides.objects.filter(username=username).delete()
        return Response({},status=status.HTTP_200_OK)
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
        query = "SELECT "+ columns +" FROM "+ "rideservice_"+table + " WHERE " + where
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

class Db_clear(APIView):
    def post(self, request):
        update_request_count()
        User_rides.objects.all().delete()
        Ride.objects.all().delete()
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
        f = open("/home/ubuntu/Rides/rideservice/request_counts.txt", "r")
        count = f.read()
        if(count == ""):
            return Response([0], status = status.HTTP_200_OK)
        return Response([int(count)], status = status.HTTP_200_OK)
    def delete(self, request):
        f = open("/home/ubuntu/Rides/rideservice/request_counts.txt", 'w')
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