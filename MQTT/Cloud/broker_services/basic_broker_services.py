import time
import logging
import paho.mqtt.client as Mqtt
from collections import defaultdict
from sys import version_info

assert version_info >= (3, 0)

HOSTNAME = "vm219.nubes.stfc.ac.uk"
PORT = 1883
AGENTNAME = 'broker-services'

# If we are serving MQTT on the SCD cloud on Ubuntu 14.04, we are constrained 
# to using this older protocol
PROTOCOL = '3.1'

STATUS_CONNECTED = "C"
STATUS_DISCONNECTED_GRACE = "DG"
STATUS_DISCONNECTED_UNGRACE = "DU"

logging.basicConfig(level=logging.INFO)

LOGGING = True
VERBOSE = True

def share(info, error=False, message=False):
    global VERBOSE
    global LOGGING
    global MODE
    global statusbox
    global messagebox
    if VERBOSE:
        if error:
            print("ERROR: " + info)
        else:
            print(info)
    if LOGGING:
        if error:
            logging.error(info)
        else:
            logging.info(info)

            
'''
BROKER THREADS:
    The threads below are called to handle the smart agents connections with the 
    cloud
'''
def handle_connect(mqttClient, userdata, rc):
    """After connection with MQTT broker established, check for errors and
    subscribe to topics."""
    global connected
    global shouldBeConnected
    if rc != 0:
        share("Connection returned result: " + Mqtt.connack_string(rc), error=True)
        connected = False
    else:
        share("Connection to MQTT broker succeeded.")
        mqttClient.publish(TOPIC_STATUS, str(int(time.time())) + ' ' + STATUS_CONNECTED, qos=1)
        connected = True
        shouldBeConnected = True
        
        # Subscribe to anything posted in the Hello topic
        mqttClient.subscribe(TOPIC_HELLO + '/#', qos=1)

    

def handle_message(mqttClient, userdata, message):
    """Maintain the network map
    """
    global connectedDevices
    print(message.topic, message.payload.decode())
    if message.topic.startswith(TOPIC_HELLO):
        agentname = ''
        try:
            agentname = message.topic.split('/')[2]
        except:
            share(message.topic + ': ' + message.payload.decode())
        # Check if it is a new device
        if agentname != '':
            if agentname not in connectedDevices.keys():
                connectedDevices[agentname] = []
            # When an agent wants to talk about its status, it publishes to:
            # broker-services/hello/[agentname]
            # with the message 'timestamp connectionstatus'
            if len(message.payload.decode().split(' ')) == 2:
                # This is a smart agent status message
                timestamp, status =  message.payload.decode().split(' ')
                if status != STATUS_CONNECTED:
                    # If this is a disconnect message, remove the smart agent 
                    del connectedDevices[agentname]
            elif len(message.payload.decode().split(' ')) == 3:
                # This is an edge device status message
                timestamp, edgedevice, status = message.payload.decode().split(' ')
                if edgedevice not in connectedDevices[agentname]:
                    if status == STATUS_CONNECTED:
                        connectedDevices[agentname].append(edgedevice)
                else:
                    if status != STATUS_CONNECTED:
                        connectedDevices[agentname].remove(edgedevice)
                        
    elif message.topic == TOPIC_PING:
        mqttClient.publish(TOPIC_PING, str(int(time.time())) + ' ' + STATUS_CONNECTED, qos=1)
            

def handle_publish(mqttClient, userdata, mid):
    """Called when a publish handshake is finished (depending on the qos)"""
    pass


def handle_subscribe(mqttClient, userdata, mid, granted_qos):
    """Called after the MQTT client successfully subscribes to a topic."""
    pass

def handle_disconnect(mqttClient, userdata, rc):
    """Callback when disconnected from MQTT broker"""
    global connected
    connected = False
    if shouldBeConnected:
        share("Disconnected from MQTT ungracefully.", error=True)
    else:
        mqttClient.loop_stop()
        share("Disconnected from MQTT gracefully.")

'''
THREAD MANAGEMENT
'''
def setup():
    """Sets up an mqtt client, registers the handlers and starts a
    threaded loop."""
    global shouldBeConnected
    global connected
    global connectedDevices
    global disconnectedDevices
    
    global TOPIC_STATUS
    global TOPIC_EDGE
    global TOPIC_DISCOVERY
    global TOPIC_HELLO
    global TOPIC_PING
    
    TOPIC_STATUS = "broker-services/status"
    TOPIC_DISCOVERY = "broker-services/discover" 
    TOPIC_HELLO = "broker-services/hello"
    TOPIC_PING = "broker-services/ping"
    # Assume connected unless proved otherwise
    connected = False
    shouldBeConnected = False
    connectedDevices = defaultdict(list)
    disconnectedDevices = defaultdict(list)

    
    if PROTOCOL ==  '3.1':
        mqttClient = Mqtt.Client(protocol=Mqtt.MQTTv31)
    else:
        mqttClient = Mqtt.Client(protocol=Mqtt.MQTTv311)
    try:
        mqttClient.on_connect = handle_connect
        
    except Exception as e:
        share(e, error=True)
    
    mqttClient.on_message = handle_message
    mqttClient.on_publish = handle_publish
    mqttClient.on_subscribe = handle_subscribe
    mqttClient.on_disconnect = handle_disconnect
    
    # Set a LWT that is sent to the broker in the event of unexpected disconnection
    # QoS = 0 because it will be confusing if the message is sent again next time that the smart agent connects
    mqttClient.will_set(TOPIC_STATUS, str(int(time.time())) + ' ' + STATUS_DISCONNECTED_UNGRACE, qos=0, retain=True) 
    
    # Attempt to connect to the broker 
    share("Connecting to MQTT broker...")
    mqttClient.connect(HOSTNAME, PORT, 60)
    return mqttClient

def mainloop(mqttClient):
    global connected
    global shouldBeConnected
    
    # Fix connection if required
    if not connected and shouldBeConnected:
        connected = True
        share("Reconnecting to MQTT broker...")
        mqttClient.connect(HOSTNAME, PORT, 60)
    
    return mqttClient

    
def clean_up(mqttClient):
    global shouldBeConnected
           
    mqttClient.publish(TOPIC_STATUS, str(int(time.time())) + ' ' + STATUS_DISCONNECTED_GRACE, qos=1) 
    shouldBeConnected = False
    mqttClient.disconnect()
    share('Shutdown was successful')


    
if __name__ == "__main__":    

    mqttClient = setup()
    mqttClient.loop_start()
    try:
        while True:
            mqttClient = mainloop(mqttClient)
    except Exception as e:
        raise e
        
    finally:
        clean_up(mqttClient)
  