from flask import jsonify, request, Flask
from flask_sqlalchemy import SQLAlchemy
import requests
import json
import re
import time
import pika
from datetime import datetime
import docker
import sys
import os
import subprocess
import uuid
from kazoo.client import KazooClient
from kazoo.client import KazooState
orchip = "54.164.169.162"
# Zookeeper connections-------------------------------------------------------------------------------------------
#in every slave worker
#create kazoo client
zk = KazooClient(hosts = "zoo1:2181",  timeout=5)
#initiate connection with zokeeper server


basedir = os.path.abspath(os.path.dirname(__file__))
if(len(sys.argv) > 1):
    db_uri = "sqlite:///"+ os.path.join(basedir, "slave"+sys.argv[1]+".db")
else:
    db_uri = "sqlite:///"+ os.path.join(basedir, "slave.db")
    
print(db_uri)
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
db = SQLAlchemy(app)

    
    

def listener_function(state):
    if(state == KazooState.LOST):
        print("Lost")
    elif state == KazooState.CONNECTED:
        #the whole slave.py code
        print("Connected to Zookeeper !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    else:
        #This is the suspended state
        print("Suspended State ++++++++++++++++++++++++++++++++++++++++")
        

zk.add_listener(listener_function)
zk.start()

#Ensure if the path exists, create if necessary
zk.ensure_path("/workers")
#create a node for slave workers with data
print(type(sys.argv[1]))
zk.create("/workers/slave"+str(sys.argv[1]), b"Slave node "+str.encode(str(sys.argv[1])),ephemeral=True)

if zk.exists("/workers/slave"+str(sys.argv[1])):
    print("znode created..................................................")
else:
    print("Did not create_____________________________________________________")


#children = zk.get_children("/worker")
#print("There are %s children with names %s" % (len(children), children))


#--------------------------------------------------------------------------------------------------------------
#database

def get_container_id():
    import subprocess
    bashCommand = """head -1 /proc/self/cgroup|cut -d/ -f3"""
    output = subprocess.check_output(['bash', '-c', bashCommand])
    return output

class User(db.Model):
    username = db.Column(db.String(length=50), nullable=False, primary_key=True)
    password = db.Column(db.String(length=40), nullable=False)
    def __init__(self, username, password):
        self.username = username
        self.password = password
    def get_obj(self):
        return self
    def __repr__(self):
        return '<User %r>' % self.id

class Ride(db.Model):
        id=db.Column(db.Integer, primary_key=True)
        created_by=db.Column(db.String(50),  nullable=False)
        timestamp=db.Column(db.String(50), default=datetime.now, nullable=False)
        source=db.Column(db.Integer,  nullable=False)
        destination=db.Column(db.Integer,  nullable=False)
        def __init__(self,id,created_by,timestamp,source,destination):
                self.id=id
                self.created_by=created_by
                self.source=source
                self.timestamp=timestamp
                self.destination=destination
        def __repr__(self):
                return '<Ride %r>' % self.id
        def get_obj(self):
            return self

class Share(db.Model):
        id=db.Column(db.Integer, primary_key=True)
        username=db.Column(db.String(50), primary_key=True)
        def __init__(self,id,username):
                self.id=id
                self.username=username
        def __repr__(self):
                return '<Share %r>' % self.id
        def get_obj(self):
            return self

db.create_all()

#-----------------------------------------------------------------------------------------------------------------------
# RabbitMQ setting
connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq', heartbeat=0))
channel = connection.channel()
channel.queue_declare(queue='rpc_queue')
channel.exchange_declare(exchange='logs', exchange_type='fanout')
result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue
channel.queue_bind(exchange='logs', queue=queue_name)

#-------------------------------------------------------------------------------------------------------------------------
#Read db
def get_data(body):
    output = get_container_id()
    print(output)
    body = body.decode("ASCII")
    body = json.loads(body)
    body = json.loads(body)
    table = body["table"]
    
    if(table == "user"):
        users = db.session.query(User).all()
        users_list  = []
        for user in users:
                obj = {"username" : user.username, "password": user.password}
                users_list.append(obj)
        response_body = json.dumps(users_list)
    elif(table == "ride"):
        rides = db.session.query(Ride).all()
        rides_list = []
        for ride in rides:
                obj = {"id":ride.id, "created_by":ride.created_by, "timestamp":ride.timestamp, "source": ride.source, "destination": ride.destination}
                rides_list.append(obj)
        response_body = json.dumps(rides_list)
    elif(table == "share"):
        shares = db.session.query(Share).all()
        shares_list = []
        for share in shares:
            obj = {"id":share.id, "username":share.username}
            shares_list.append(obj)
        response_body = json.dumps(shares_list)
    else:
        response_body = json.dumps(["Success"])
    print(response_body)
    return response_body

def on_request(ch, method, props, body):

    response = get_data(body)

    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id =props.correlation_id),body=response)
    time.sleep(5)
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='rpc_queue', on_message_callback=on_request)


#-------------------------------------------------------------------------------------------------------------------------
#sync db
def syncCallback(ch, method, properties, body):
    message=body
    body = body.decode("ASCII")
    body = json.loads(body)
    if(isinstance(body, str)):
        body = json.loads(body)    
    print(type(body), body)
    clear = body["clear"]
    if clear=="1":
        User.query.delete()
        Share.query.delete()
        Ride.query.delete()
        db.session.commit()
        return jsonify({}),200
    else:
        table = body["table"]
        op_type = body["type"]
        if op_type=="insert":
            content = body["data"]
            if(table == "user"):
                user = User(username=content["username"], password=content["password"])
                try:
                    db.session.add(user)
                    db.session.commit()
                    print("done")
                    return jsonify(["done"]), 200
                except:
                    return jsonify(["Not done"]), 400
            elif(table == "ride"):
                rides =  db.session.query(Ride).all()
                ride_id = 0
                for ride in rides:
                    if(ride_id < ride.id):
                        ride_id = ride.id
                ride_id += 1        
                ride = Ride( id=ride_id, created_by=content["created_by"], timestamp=content["timestamp"], source=content["source"], destination=content["destination"])
                try:
                    db.session.add(ride)
                    db.session.commit()
                    print("done")
                    return  jsonify(["done"]), 200
                except:
                    return jsonify(["Not done"]), 400
            elif(table == "share"):
                share = Share(id=content["id"], username=content["username"])
                try:
                    db.session.add(share)
                    db.session.commit()
                    print("done")
                    return jsonify(["Done"]), 200
                except:
                    return jsonify(["Not done"]), 400
            else:
                return jsonify(["Cant perform write"]), 400

        elif op_type=="delete":
            value = body["value"]
            if(table=="User"):
                #a=User(username=value)
                User.query.filter(User.username==value).delete()
                #db.session.add(a)
                db.session.commit()
                return "done",201
            elif(table=="ride"):
                Ride.query.filter(Ride.id==value).delete()
                db.session.commit()
                return "done",200
            elif(table=="share"):
                Share.query.filter(Share.id==value).delete()
                db.session.commit()
                return "done",200

    
channel.basic_consume(
    queue=queue_name, on_message_callback=syncCallback, auto_ack=True)
class CopyRpcClient(object):

    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='rabbitmq'))

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(queue='', exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_copy_response,
            auto_ack=True)

    def on_copy_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key='copy_master',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body="")
        while self.response is None:
            self.connection.process_data_events()
        return self.response


copy_rpc = CopyRpcClient()
print("in slave")
response = copy_rpc.call()
print("after call")
print(" [.] Got %r" % response.decode("ASCII"))
data = response.decode("ASCII")
data = json.loads(data)
users_data = list(map(lambda x: x.username, db.session.query(User).all()))
rides_data = list(map(lambda x: x.id, db.session.query(Ride).all()))
shares_data =  list(map(lambda x:(x.id, x.username), db.session.query(Share).all()))
for user in data["users"]:
    if(user["username"] not in users_data):
        u = User(username=user["username"], password=user["password"])
        db.session.add(u)
        db.session.commit()
for ride in data["rides"]:
    if(ride["id"] not in rides_data):
        r = Ride(id=ride["id"], created_by=ride["created_by"], timestamp = ride["timestamp"],source=ride["source"], destination=ride["destination"])
        db.session.add(r)
        db.session.commit()
for share in data["shares"]:
    if((share["id"], share["username"]) not in shares_data):
        s = Share(id=share["id"], username=share["username"])
        db.session.add(s)
        db.session.commit()




#--------------------------------------------------------------------------------------------------------------------------------
#consumption
with app.app_context():
    print(" [x] Awaiting RPC requests")
    channel.start_consuming()


