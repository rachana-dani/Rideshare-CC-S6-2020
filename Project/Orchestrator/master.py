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

#--------------------------------------------------------------------------------------------------------------
#database


def get_container_id():
    import subprocess
    bashCommand = """head -1 /proc/self/cgroup|cut -d/ -f3"""
    output = subprocess.check_output(['bash', '-c', bashCommand])
    return output

basedir = os.path.abspath(os.path.dirname(__file__))
print(basedir)
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///master.db"
db = SQLAlchemy(app)



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
        id=db.Column(db.Integer, db.ForeignKey("ride.id", ondelete="CASCADE"), primary_key=True)
        username=db.Column(db.String(50), db.ForeignKey("user.username", ondelete="CASCADE"), primary_key=True)
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
channel.queue_declare(queue='writeQ')
channel.exchange_declare(exchange='logs', exchange_type='fanout')


#-------------------------------------------------------------------------------------------------------------------------
#Write to db

def writeCallback(ch, method, properties, body):
    message=body
    body = body.decode("utf-8")
    body = json.loads(body)
    print(type(body))
    print(body)
    if(body == ""):
        return
    if(isinstance(body, str)):
        body = json.loads(body)
    print(type(body))
    clear = body["clear"]
    if clear=="1":
        User.query.delete()
        Share.query.delete()
        Ride.query.delete()
        db.session.commit()
        channel.basic_publish(exchange='logs', routing_key='', body=message)
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
                    channel.basic_publish(exchange='logs', routing_key='', body=message)
                    print("done")
                    return jsonify(["done"]), 200
                except:
                    channel.basic_publish(exchange='logs', routing_key='', body=message)
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
                    channel.basic_publish(exchange='logs', routing_key='', body=message)
                    print("done")
                    return  jsonify(["done"]), 200
                except:
                    channel.basic_publish(exchange='logs', routing_key='', body=message)
                    return jsonify(["Not done"]), 400
            elif(table == "share"):
                share = Share(id=content["id"], username=content["username"])
                try:
                    db.session.add(share)
                    db.session.commit()
                    channel.basic_publish(exchange='logs', routing_key='', body=message)
                    print("done")
                    return jsonify(["Done"]), 200
                except:
                    channel.basic_publish(exchange='logs', routing_key='', body=message)
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
                channel.basic_publish(exchange='logs', routing_key='', body=message)
                return "done",201
            elif(table=="ride"):
                Ride.query.filter(Ride.id==value).delete()
                db.session.commit()
                channel.basic_publish(exchange='logs', routing_key='', body=message)
                return "done",200
            elif(table=="share"):
                Share.query.filter(Share.id==value).delete()
                db.session.commit()
                channel.basic_publish(exchange='logs', routing_key='', body=message)
                return "done",200
channel.queue_declare(queue="copy_master")

def copy_callback():
    print("I got called")
    data = {}
    users = db.session.query(User).all()
    data["users"] = []
    for user in users:
        data["users"].append({"username": user.username,
            "password":user.password
        })
    rides = db.session.query(Ride).all()
    data["rides"] = []
    for ride in rides:
        data["rides"].append({
            "id":ride.id,
            "created_by":ride.created_by,
            "timestamp":ride.timestamp,
            "source":ride.source,
            "destination":ride.destination
        })
    shares = db.session.query(Share).all()
    data["shares"] = []
    for share in shares:
        data["shares"].append({
            "id":share.id,
            "username":share.username
        })
    print(data)
    return json.dumps(data)

def on_copy_request(ch, method, props, body):
    response = copy_callback()
    ch.basic_publish(
        exchange='',
        routing_key=props.reply_to,
        properties=pika.BasicProperties(
            correlation_id = props.correlation_id
        ),
        body=response
    )
    ch.basic_ack(delivery_tag=method.delivery_tag)
channel.basic_consume(queue="copy_master", on_message_callback=on_copy_request)

channel.basic_consume(
    queue='writeQ', on_message_callback=writeCallback, auto_ack=True
)
#--------------------------------------------------------------------------------------------------------------------------------
#consumption
with app.app_context():
    print(" [x] Awaiting RPC requests")
    channel.start_consuming()
