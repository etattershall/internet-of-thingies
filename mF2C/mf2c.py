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
    
    
"""
Define topic conventions
"""
def topic_public(agentID):
    return 'mf2c/' + str(agentID) + '/public'

def topic_protected(agentID):
    return 'mf2c/' + str(agentID) + '/protected'
    
def topic_private(agentID):
    return 'mf2c/' + str(agentID) + '/private'
    
def topic_pingreq(agentID):
    return 'mf2c/' + str(agentID) + '/public/pingreq'

def topic_pingack(agentID):
    return 'mf2c/' + str(agentID) + '/public/pingack'
    
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
    """
    
    """
    def __init__(self, hostname, agentID, port=1883, protocol='3.1'):
        # Check input
        assert type(hostname) is str
        assert type(agentID) is str
        assert type(port) is int
        assert protocol in ['3.1', '3.1.1']

        # Set class level variables
        self.hostname = hostname
        self.agentID = agentID
        self.port = port
        if protocol == '3.1':
            self.protocol = mqtt.MQTTv31
        elif protocol == '3.1.1':
            self.protocol = mqtt.MQTTv311

        # Set the topics that will be subscribed to
        self.PUBLIC = topic_public(self.agentID)
        self.PROTECTED = topic_protected(self.agentID)
        self.PRIVATE = topic_private(self.agentID)
        self.PINGREQ = topic_pingreq(self.agentID)
        self.PINGACK = topic_pingack(self.agentID)
    
    def setup(self, timeout=20):
        """
        This method sets up the actual MQTT client, assigns all callback 
        functions for event handling and sets a last will and testament (LWT)
        message. 
        
        It then attempts to connect to the broker. The connection call
        is blocking; it continues until a connection acknowlegement message is 
        received from the broker or until the timeout is reached.
        
        After connection has been acheived, it subscribes to the topics:
            mf2c/[agentID]/public
            mf2c/[agentID]/protected
            mf2c/[agentID]/private
            mf2c/[agentID]/public/pinreq
            mf2c/[agentID]/public/pingack
            
        If another device wants to contact this smart agent, it must publish to
        one of these topics. 
        
        Finally, this method starts the MQTT loop running on a separate thread.
        This loop thread handles publishing and receiving messages, and also 
        routinely pings the broker to check the connection status. If the
        connection is lost, the thread automatically buffers messages and 
        attempts to reconnect
        """
        global connack
        global incoming_message_buffer
        # Blocks until connected or timeout
        # Setting clean_session = True means that subsciption information and 
        # queued messages are retained after the client disconnects. It is suitable
        # in an environment where disconnects are frequent.
        mqtt_client = mqtt.Client(protocol=self.protocol, client_id=self.agentID, clean_session=False)
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        mqtt_client.on_publish = on_publish
        mqtt_client.on_disconnect = on_disconnect
                
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
        """
        This loop method can be run periodically to read messages out of the
        incoming message buffer. It also deals with replying to ping requests
        from other devices.
        
        Note that it is not necessary to handle reconnection to the broker in 
        this function; that task is done by the paho-mqtt loop function. 
        """
        global incoming_message_buffer
        
        # dump all incoming messages into a list and empty the string
        incoming_messages = incoming_message_buffer
        # empty the buffer
        incoming_message_buffer = []

        parsed_messages = []
        pingacks = []
        for message in incoming_messages:
            # Deal with ping requests
            if message.topic == self.PINGREQ:
                self.pingack(json.loads(message.payload.decode()))
            # Deal with acknowledgements to our own ping requests
            elif message.topic == self.PINGACK:
                pingacks.append(json.loads(message.payload.decode()))
            # Parse non-encrypted messages
            elif message.topic == self.PUBLIC:
                parsed_messages.append(json.loads(message.payload.decode()))

        return parsed_messages, pingacks
        
    def send(self, recipients, payload, security=0, qos=1):
        """
        Method sends a specified jsonic payload to a list of recipients.
        """
        # Check input
        assert type(recipients) == list
        assert len(recipients) > 0
        assert security in [0, 1, 2]
        assert type(payload) == dict

        # Nothing needs to be encrypted if the level of security is set to
        # public
        if security == 0:
            for recipient in recipients:
                topic = topic_public(recipient)
                payload['timestamp'] = timestamp()
                if 'source' not in payload.keys():
                    payload['source'] = self.agentID
                self.client.publish(topic, json.dumps(payload), qos=qos)

    
    def pingack(self, payload):
        """
        Respond to a ping from another device with a ping acknowledgement.
        
        This method is called automatically when a 
        """
        # ping is always public
        try:
            recipient = payload['source']
        except:
            return
        topic = topic_pingack(recipient)
        payload = {
                    'timestamp': timestamp(),
                    'source': self.agentID
                   }

        self.client.publish(topic, json.dumps(payload), qos=2)
     
    def ping(self, recipients):
        """
        Send a ping request to one or more recipients
        """
        assert type(recipients) == list
        assert len(recipients) > 0
        for recipient in recipients:
            topic = topic_pingreq(recipient)
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
    smart_agent = Agent(hostname, '0001').setup()
    
    oldtimestamp = int(timestamp())
    try:
        while True:
            # Believe me, if you don't introduce a delay, this program will 
            # happily take up 90% of your CPU...
            time.sleep(0.1)
            
            # Get the messages in the buffer and deal with ping requests
            messages, pingacks = smart_agent.loop()
            if messages != []:
                for message in messages:
                    print(message)
            
            # Send a message every 10 seconds
            if int(timestamp()) - oldtimestamp >= 10:
                smart_agent.send(['0002', '0003'], {'payload': 'Hello from Windows Computer'}, security=0, qos=2)
                oldtimestamp = int(timestamp())
    except Exception as e:
        raise e
    finally:
        # clean up
        smart_agent.clean_up()