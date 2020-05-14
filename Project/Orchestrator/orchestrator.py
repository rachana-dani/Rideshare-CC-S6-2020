from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import requests
import json
import re
import time
from datetime import datetime
import pika
import os
import docker
import threading
import math

from kazoo.client import KazooClient
from kazoo.client import KazooState
orchip = "54.164.169.162"
# Zookeeper connections-------------------------------------------------------------------------------------------
#in every slave worker
#create kazoo client
zk = KazooClient(hosts = "zoo1:2181",  timeout=5)
zk.start()
client = docker.from_env()
#initiate connection with zokeeper server



def get_count():
	count_file = open("count.txt", "r")
	worker_count = int(count_file.read())
	count_file.close()
	return worker_count
def save_count(worker_count):
	fcount = open("count.txt", "w")
	fcount.write(str(worker_count))
	fcount.close()

def create_new_container():
	worker_count = get_count()
	worker_count += 1
	name = "worker_slave" + str(worker_count)
	save_count(worker_count)
	print("---------------------------------------------")
	print("worker_count: ", worker_count)
	CONTAINER = client.containers.run(
		'new_slave', 
		command="./create_worker.sh "+str(worker_count), 
		links={"rabbitmq":"rabbitmq"},
		network="new_default",
		name=name, 
		detach=True
	)
	print("createdd")
	print(CONTAINER.logs().decode("ASCII"))

def get_max_pid():
	max_pid = -1
	max_id = ""
	if(len(client.containers.list()) == 4):
		return (0, "0")
	for i in client.containers.list():
		if(i.name.startswith("worker_slave")):
			container = client.containers.get(i.id)
			print(i.name, i.id)
			if(container.attrs["State"]["Pid"] > max_pid):
				max_pid = container.attrs["State"]["Pid"]
				max_id = i.id
	return (max_pid, max_id)

def kill_max_pid_container(max_pid, max_cont_id):
	print(max_pid, max_cont_id)
	cont = client.containers.get(max_cont_id)
	print(cont)
	cont.stop(timeout=1)
	cont.remove(v=True, force=True)
	print("Crashed")



first_request=0
first_auto_scale=0

#function to stop container( for scale down), stops the container that has max pid
def stop():
	client = docker.from_env()
	max_pid = -1
	max_id = ""
	for i in client.containers.list():
		docker_client = docker.client.DockerClient()
		container = docker_client.containers.get(i.id)
		if(container.attrs["State"]["Pid"] > max_pid):
			max_pid = container.attrs["State"]["Pid"]
			max_id = i.id
	stop_container = docker_client.containers.get(str(max_id))
	try:
		stop_container.stop(timeout=1)
		stop_container.remove(v=Ture, force=True)
		print("stopped a container")

	except:
		print(" stop did not work")




def autoscale(): 
	threading.Timer(120.0, autoscale).start()                   #restarts this function after 2 minutes
	global first_auto_scale
	if(first_auto_scale==1):
		print(get_no_of_requests())
		n=get_no_of_requests()/20
		num=math.ceil(n)         #this is the required number of slaves
		if(num==0):
			num=1            #if there are 0 requests there should be 1 slave
		print("Required number of slaves: ",num)
		client = docker.from_env()
		no_of_current_cont=len(client.containers.list())-4   #excluding master,orches and rabbitmq
		print("number of current slaves : ",no_of_current_cont)
		if(num>no_of_current_cont):
			print("scaling up")
			#scale up: create num-no_of_current_cont
			for k in range(num-no_of_current_cont):
				requests.get("http://0.0.0.0:80/api/v1/create/container")
				print("created a new slave")

		if(num<no_of_current_cont):
			#scale down: kill no_of_current_cont-num containers
			print("scaling down")
			for k in range(no_of_current_cont-num):
				stop()
		#f = open("/code/request_count.txt", "w")
		#f.write('0')
	else:
		first_auto_scale=1														

  



def increment():
    f = open("/code/request_count.txt", "r")
    count = f.read()
    f.close()
    if(count == ""):
        count = str(1)
    else:
        count = str(int(count)+1)
    f = open("/code/request_count.txt", "w")
    f.write(count)
    print("incremented>>>>",count)
    f.close()

def get_no_of_requests():
    f = open("/code/request_count.txt", "r")
    count = f.read()
    f.close()
    if(count == ""):
        res = 0
    else:
        res = int(count)
    return res





connection = pika.BlockingConnection(
	pika.ConnectionParameters(host="rabbitmq", heartbeat=0)
)
channel  = connection.channel()
channel.queue_declare(queue='writeQ')

app = Flask(__name__)

import uuid

class OrchestratorRpcClient(object):

    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='rabbitmq'))

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(queue='', exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, body):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key='rpc_queue',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=body)
        while self.response is None:
            self.connection.process_data_events()
        return self.response

@app.route("/api/v1/db/read", methods=["POST"])
def read():
	increment()
	global first_request
	if(first_request==0):
		autoscale()
		first_request=1

	body = json.dumps(request.data.decode("ASCII"))
	orches_rpc = OrchestratorRpcClient()
	response = orches_rpc.call(body)
	return response, 200


@app.route("/", methods=["GET"])
def get_():
    return jsonify(["data"]), 200

@app.route("/api/v1/db/write", methods=["POST"])
def write():
	body = json.dumps(request.data.decode("ASCII"))
	print(body, "BOdy")
	print(request.form, "form data")
	print(request, "request")
	print(body, "body")

	channel.basic_publish(exchange="", routing_key="writeQ", body=body)
	return jsonify(["Wrote to Q"]), 200

@app.route("/api/v1/worker/list", methods=["GET"])
def worker_list():
	client = docker.from_env()
	pid_list  = []
	for i in client.containers.list():
		if(i.name.startswith("worker")):
			print(i, i.name, i.id)
			docker_client = docker.client.DockerClient()
			container = docker_client.containers.get(i.id)
			pid_list.append(container.attrs["State"]["Pid"])
			print(type(container.attrs["State"]["Pid"]))
	pid_list=sorted(pid_list)
	return jsonify(pid_list), 200
	

@app.route("/api/v1/create/container",methods=["GET"])
def create_container():
	#----------------------------------------------------------------
	create_new_container()
	return jsonify(["ok!!!"]), 200


def lost_function():
	create_new_container()
	print("New container created")

	
@app.route("/api/v1/crash/slave", methods=["POST"])
def crash_container():
	max_pid, max_cont_id = get_max_pid()
	kill_max_pid_container(max_pid, max_cont_id)
	zk.get_children("/workers", watch=lost_function())
	return jsonify([str(max_pid)]), 200
	


@app.route("/api/v1/master/crash", methods=["POST"])
def crash_master_container():
	client = docker.from_env()
	max_pid = -1
	max_id = ""
	for i in client.containers.list():
		if(i.name.startswith("worker_master")):
			docker_client = docker.client.DockerClient()
			container = docker_client.containers.get(i.id)
			if(container.attrs["State"]["Pid"] > max_pid):
				max_pid = container.attrs["State"]["Pid"]
				max_id = i.id
	crash_container = docker_client.containers.get(str(max_id))
	try:
		crash_container.kill()
		return jsonify([str(max_pid)]), 200
	except:
		return jsonify(["Not successful"]), 400

#--------------------------------------------------------------------------------------------------
# DB clear API
@app.route('/api/v1/db/clear',methods=["POST"])				
def clear_db_ride():
	body = json.dumps(request.data.decode("ASCII"))
	print(request.form, "form data")
	print(request, "request")
	print(body, "body")
	channel.basic_publish(exchange="", routing_key="writeQ", body='{"clear":"1"}')
	return jsonify({}),200




if __name__ == "__main__":
	port = int(os.environ.get('PORT', 80))
	app.run(host = "0.0.0.0", port = port, debug = True)
	channel.start_consuming()
	
	
	
"""{"table": "user","columns": ["username", "password"],"where": "username=rachana"
}"""
