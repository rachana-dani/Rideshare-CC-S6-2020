#Rideshare
The project is a distributed system of three instances
1. User
2. Ride
3. Project

###User instance has the User container running user service(Django project).
```
cd User
sudo docker-compose up --build
```
###Ride instance has the Ride container running ride service(Django project).
```
cd Rides
sudo docker-compose up --build
```
###Project instance has the New network running containers for Orhestrator(Flask application), Slave, Master, Rabbitmq and Zookeeper services.

To run the project run the following commands with the user who has sudo access in the root directory of the user(Ubuntu)

```
cd Project
cd NEW
sudo docker-compose up --build
```
