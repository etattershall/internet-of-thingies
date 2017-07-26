## Cloud MQTT Broker

The cloud runds the **MQTT Broker**, along with any diagnostics/control and frontend webapps. Our cloud broker is a VM service provided by our organisation (Scientific Computing, STFC). Specifics can be found at https://cloud.stfc.ac.uk/.

## Setting up the cloud

**Basic installation**

Run the commands:
- sudo apt-get update
- sudo apt-get upgrade
- sudo apt-get install mosquitto mosquitto-clients

Edit the config file in /etc/mosquitto/mosquitto.conf, adding the lines:
- persistence true
- persistence_location /var/lib/mosquitto/
- persistence_file mosquitto.db
- log_dest syslog
- log_dest stdout
- log_dest topic
- log_type error
- log_type warning
- log_type notice
- log_type information
- connection_messages true
- log_timestamp true
- allow_anonymous true

And run
- /sbin/ldconfig


You can listen in on the status of the broker using
- mosquitto_sub -t '$SYS/#' -v

At this point, it is possible to publish/subscribe using
- mosquitto_sub -h localhost -p 1883 -t test
- mosquitto_pub -h localhost -p 1883 -t test -m 'Hello World'

**Python**

Run the commands:
- sudo apt-get install python3-pip
- sudo pip3 install paho-mqtt

Paho-MQTT will not work out of the box because our VM is only able to run Ubuntu 14.04. The only available version of mosquitto for this distro uses MQTT version 3.1. rather than the current 3.1.1.

Therefore, whenever you want to create a new MQTT Client, you will need to specify the protocol using:

```python
import paho.mqtt.client as mqtt

def on_connect(client, userdata, rc):
    print('connected')
    client.subscribe("$SYS/#")

def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.payload))

client = mqtt.Client(protocol=mqtt.MQTTv31)
client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883, 60)

client.loop_forever()
```

**Web frontend**

Because I am a lazy person, we are going to use the Flask-MQTT module (https://github.com/MrLeeh/Flask-MQTT).

Run the commands:
- sudo pip3 install Flask-MQTT
- sudo pip3 install eventlet
- sudo pip3 install flask
- sudo pip3 install typing
- sudo pip3 install flask_socketio
- sudo pip3 install flask_bootstrap
- sudo pip3 install flask_socketio

To make the example file work, we need to modify it to match the older protocol
```python

# Finally, need this so that we can change the protocol
from paho.mqtt.client import Client, MQTTv31

# Initialise the client WITHOUT the app
mqtt = Mqtt()

# Perform open heart surgery on the brand new object, setting the protocol to the old version
mqtt.client = Client(protocol=MQTTv31)

# Now we initialise it with the app
mqtt.init_app(app)
```

The app can be run with
- python3 app.py

Point your browser to e.g.
- http://<name of your host machine>:5000/
to see the app in action.
