# -*- coding: utf-8 -*-
"""
Created on Wed May 24 10:43:37 2017

http://www.hivemq.com/blog/mqtt-client-library-paho-python

@author: Emma Tattershall
"""

import paho.mqtt.client as mqtt
import random
import time

# Callback for when the client receives a CONNACK reponse back from the broker
def on_connect(client, userdata, rc):
    print("Connected to broker with result code " + str(rc))
    
    # We should make our subscriptions on connect
    client.subscribe("test")
    
# Callback for when the client receives a PUBLISH message from the broker
def on_message(client, userdata, message):
    print(message.topic + " " + str(message.payload))
 
def on_publish(client, userdata, mid):
    print("Message sent! Message ID is " + str(mid))

def imaginary_sensor():
    return random.randint(-10, 40)
    
broker_name = "vm219.nubes.stfc.ac.uk"
broker_port = 1883

# If we are serving MQTT on the SCD cloud on Ubuntu 14.04, we are constrained 
# to using this older protocol
protocol = mqtt.MQTTv31

client = mqtt.Client(protocol=protocol)
client.on_connect = on_connect
client.on_message = on_message
client.on_publish = on_publish
 
client.connect(broker_name, broker_port, 60)

# Start a new thread to process network traffic.
client.loop_start()

while True:
    sensor_reading = imaginary_sensor()
    (rc, mid) = client.publish("test/sensor", str(sensor_reading), qos=1)
    time.sleep(30)