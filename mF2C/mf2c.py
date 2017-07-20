"""mF2C-MQTT

This module uses MQTT and JSON based encryption to provide a secure method of
direct messaging in which encryption is handled by a trusted central server.

Example:
    Examples can be given using either the ``Example`` or ``Examples``
    sections. Sections support any reStructuredText formatting, including
    literal blocks::

        $ python example_google.py

Section breaks are created by resuming unindented text. Section breaks
are also implicitly created anytime a new section starts.

Attributes:
    module_level_variable1 (int): Module level variables may be documented in
        either the ``Attributes`` section of the module docstring, or in an
        inline docstring immediately following the variable.

        Either form is acceptable, but the two should not be mixed. Choose
        one convention to document module level variables and be consistent
        with it.

Todo:
    * For module TODOs
    * You have to also use ``sphinx.ext.todo`` extension

.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

MY NOTES
There are other ways to do security: TLS is reportedly a good option. However, 
I found it more challenging to set up, since it requires mqtt 3.1.1., and many 
of the operating systems I have access to (Scientific Linux 7, Ubuntu 14.04 
and Raspian) do not have all the relevant up-to-date packages. Therefore, we
have chosen to explicitly handle encryption/decryption at the payload level. 
Another advantage of this approach is its modifiability and transparancy.
"""

import logging
import time
import json
import paho.mqtt.client as mqtt

__author__ = "Emma Tattershall & Callum Iddon"
__version__ = "1.3"
__email__ = "etat02@gmail.com, jens.jensen@stfc.ac.uk"
__status__ = "Pre-Alpha"

STATUS_CONNECTED = "C"
STATUS_DISCONNECTED_GRACE = "DG"
STATUS_DISCONNECTED_UNGRACE = "DU"
HUB = '00000000'

logging.basicConfig(level=logging.INFO)

def encrypt(plaintext):
    encrypted_string = plaintext
    return encrypted_string
    
def decrypt(encrypted_string):
    plaintext = encrypted_string
    return plaintext

def timestamp():
    # Returns an integer UNIX time
    return str(int(time.time()))
    
def on_connect(mqtt_client, userdata, flags, rc):
    """
    Called when a connect acknowledgement (CONNACK) is received. 
    
    This function sets a global connack flag when broker connection has been
    confirmed.
    """
    global connack
    logging.info("Connected to broker")
    connack = True
    
def on_disconnect(mqtt_client, userdata, rc):
    """
    This function is called when a disconnect packet is sent from this client.
    It is also used if the broker itself disconnects.
    """
    logging.info('Disconnected from broker')
    
def on_publish(mqtt_client, userdata, mid):
    """
    Called when a publish acknowledgement (PUBACK) is received. 
    PUBACKs will only be sent if the message has a QoS > 0
    """
    pass

def on_message(mqtt_client, userdata, message):
    """
    Called when a message is received.
    
    This function adds the new messsage to the module-level message buffer. We
    have chosen to use a buffer rather than dealing with messages in this callback
    function because it means we can provide greater flexibility for users
    """
    global incoming_message_buffer
    incoming_message_buffer.append(message)

class TimeOutError(Exception):
    def __init__(self, value):
        self.value = value

class Agent():
    def __init__(self, hostname, agentID, port=1883, protocol='3.1'):
        
        assert type(hostname) is str
        assert type(agentID) is str
        assert type(port) is int
        assert protocol in ['3.1', '3.1.1']

        self.hostname = hostname
        self.agentID = agentID
        self.port = port
        if protocol == '3.1':
            self.protocol = mqtt.MQTTv31
        elif protocol == '3.1.1':
            self.protocol = mqtt.MQTTv311

        self.PUBLIC = 'mf2c/' + agentID + '/public'
        self.PROTECTED = 'mf2c/' + agentID + '/protected'
        self.PRIVATE = 'mf2c/' + agentID + '/private'
        self.PINGREQ = self.PUBLIC + '/ping'
        self.PINGACK = self.PUBLIC + '/pingack'
    
    def setup(self, timeout=20):
        global connack
        global incoming_message_buffer
        # Blocks until connected or timeout
        # Setting clean_session = True means that subsciption information and 
        # queued messages are retained after the client disconnects. It is suitable
        # in an environment where disconnects are frequent.
        mqtt_client = mqtt.Client(protocol=self.protocol, client_id=self.agentID, clean_session=False)
        mqtt_client.on_connect = on_connect
        
        # Set the LWT
        # If the client disconnects without calling disconnect, the broker will
        # publish this message on its behalf
        # retain should be set to true
        
        # keepalive is maximum number of seconds allowed between communications
        # with the broker. If no other messages are sent, the client will send a
        # ping request at this interval
        logging.info('Attempting to connect to broker at ' + self.hostname)
        mqtt_client.connect(self.hostname, self.port, keepalive=60)
        
        # Force function to block until connack is sent from the broker, or timeout
        connack = False
        start_time = time.time()
        while not connack:
            time.sleep(0.1)
            mqtt_client.loop()
        
            if time.time() - start_time > timeout:
                raise TimeOutError("The program timed out while trying to connect to the broker!")
                break
            
        
        
        # When connected, subscribe to the relevant channels
        mqtt_client.subscribe([(self.PUBLIC, 1), (self.PROTECTED, 1),
                              (self.PRIVATE, 1), (self.PINGREQ, 1),
                              (self.PINGACK, 1)
                             ])
        
        self.client = mqtt_client
        incoming_message_buffer = []
        # Start the loop. This method is preferable to repeatedly calling loop
        # since it handles reconnections automatically. It is non-blocking and 
        # handles interactions with the broker in the background.
        logging.info('Starting loop')
        self.client.loop_start()
    
    def loop(self):
        # housekeeping
        global incoming_message_buffer
        # Reconnection is handled at a lower level: it's not necessary to make
        # reconnection attempts here - in fact, doing so will raise a connection 
        # refused error and crash the program. If instead the program waits until
        # the broker comes back online, it will reconnect at that point and attempt
        # to publish the buffer of unsent messages (messages w/ qos > 0)
        

        
            
        
        # Decode messages if necessary
        # each message has: [security, source, payload, timestamp]

        # dump all incoming messages into a list and empty the string
        incoming_messages = incoming_message_buffer
        # empty the buffer
        incoming_message_buffer = []

        parsed_messages = []
        pingacks = []
        for message in incoming_messages:
            # Deal with ping requests
            if message.topic == self.PINGREQ:
                self.pingack(json.loads(message.payload))
            elif message.topic == self.PINGACK:
                pingacks.append(json.loads(message.payload))
            elif message.topic == self.PUBLIC:
                parsed_messages.append(json.loads(message.payload))

        return parsed_messages, pingacks
        
    def send(self, recipients, payload, security=0, qos=1):
        assert type(recipients) == list
        assert len(recipients) > 0
        assert security in [0, 1, 2]
        assert type(payload) == dict
        # payload is assumed to be a jsonic object
        # the keyword 'source' is protected

        # Nothing needs to be encrypted if the level of security is set to
        # public
        if security == 0:
            for recipient in recipients:
                topic = 'mf2c/' + str(recipient) + '/public'
                payload['timestamp'] = timestamp()
                if 'source' not in payload.keys():
                    payload['source'] = self.agentID
                self.client.publish(topic, json.dumps(payload), qos=qos)

    
    def pingack(self, payload):
        """
        Respond to a ping from another device with a ping acknowledgement
        """
        # ping is always public
        try:
            recipient = payload['source']
        except:
            return
        topic = 'mf2c/' + str(recipient) + '/public/pingack'
        payload = {
                    'timestamp': timestamp(),
                    'source': self.agentID
                   }

        self.client.publish(topic, json.dumps(payload), qos=2)
     
    def ping(self, recipient):
        # ping is always public
        topic = 'mf2c/' + str(recipient) + '/public/pingreq'
        payload = {
                    'timestamp': timestamp(),
                    'source': self.agentID
                   }

        self.client.publish(topic, json.dumps(payload), qos=2)
        
    def clean_up(self):
        self.client.disconnect()
        self.client.loop_stop()




if __name__ == "__main__":
    hostname = "vm219.nubes.stfc.ac.uk"
    port = 1883
    smart_agent = Agent(hostname, '00000001')
    smart_agent.setup()
    
    try:
        while True:
            # Believe me, if you don't introduce a delay, this program will 
            # happily take up 90% of your CPU...
            time.sleep(0.1)
            
            messages, pingacks = smart_agent.loop()
        
    except Exception as e:
        raise e
    finally:
        # clean up
        smart_agent.clean_up()