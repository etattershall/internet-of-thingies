"""
Runs an mqtt client that provides broker services.

Usage


Services
--------
Discovery:
    - Maintains a list of connected smart agents as the retained message on
      TOPIC_DISCOVERY. This means that on subscription to TOPIC_DISCOVERY,
      a message with the currently connected devices will imediately be sent.
    - List is encoded as JSON with each connected agentID as a string within a
      list/array.


Smart Agent Setup
-----------------
Connect:
    - All smart agents should publish their ID on TOPIC_CONNECT immediately
      after connecting.

Disconnect:
    - All smart agents must post their ID on TOPIC_DISCONNECT_GRACE before
      gracefully disconnecting. Ideally this shouldn't be a retained message.
    - All smart agents must set their will to post their ID on
      TOPIC_DISCONNECT_UNGRACE (again, not retained).


"""
import paho.mqtt.client as Mqtt
import json
import logging
import time

HOSTNAME = "localhost"
PORT = 1883


# Topics will always be joined with a "/" so if you include a "/" at the end
# of these variables (X/) then if they get joined with Y it will be X//Y
# http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/cos01/mqtt-v3.1.1-cos01.pdf
# States that leading or trailing '/' creates a distinct Topic Name and '//'
# IS allowed in a Topic Name.
TOPIC_ROOT = "broker-services"
TOPIC_CONNECT = TOPIC_ROOT + "/connect"
TOPIC_DISCONNECT = TOPIC_ROOT + "/disconnect"
TOPIC_DISCONNECT_GRACE = TOPIC_DISCONNECT + "/graceful"
TOPIC_DISCONNECT_UNGRACE = TOPIC_DISCONNECT + "/ungraceful"
TOPIC_DISCOVERY = TOPIC_ROOT + "/discover"

# Setup logging
logging.basicConfig(level=logging.INFO)


def run():
    """Sets up an mqtt client, registers the handlers and starts a
    threaded loop."""
    global connectedSmartAgents
    global shouldBeConnected
    global messagesInTransit
    global connected
    connectedSmartAgents = set()  # Current list of connected Smart Agents
    shouldBeConnected = True      # Set to false before graceful disconnect
    # Create a dict of the mid of each message that has been sent with
    # client.publish() but has not had its callack (on_publish).
    # The value is (topic, payload).
    messagesInTransit = dict()

    # Use this protocol version to suit the particular broker..
    client = Mqtt.Client(protocol=Mqtt.MQTTv31)

    # Register client callbacks (prefix handle)
    client.on_connect = handle_connect
    client.on_disconnect = handle_disconnect
    client.on_publish = handle_publish

    # Register message callbacks (prefix on)
    client.on_message = on_unhandled_message
    client.message_callback_add(TOPIC_DISCONNECT_GRACE + "/#",
                                on_grace_disconnect)
    client.message_callback_add(TOPIC_DISCONNECT_UNGRACE + "/#",
                                on_ungrace_disconnect)
    client.message_callback_add(TOPIC_CONNECT + "/#",
                                on_connect)

    logging.info("Connecting to MQTT broker...")
    client.connect(HOSTNAME, port=PORT)
    client.loop_start()  # Start a threaded loop in the background.
    return client


def stop(client, finishMessages=False, sync=False, timeout=3):
    """Stops the connection to the MQTT broker. This is mainly implemented for
    testing purposes as there shouldn't be any reason to stop the service.

    If the finishMessages flag is True this will wait all messagesInTransit to
    leave before disconnecting.

    If the sync flag is True, this will wait until handle_disconnect sets
    the global connected variable to false.

    For both those waits, after timeout seconds a RuntimeError is raised.
    """
    if finishMessages:
        after = time.time() + timeout
        while time.time() < after:
            if not len(messagesInTransit) > 0:
                break
        else:
            raise RuntimeError("Timeout expired while waiting for messages "
                               "to finish sending.")
    global shouldBeConnected
    shouldBeConnected = False  # tell the callback that this isn't an error
    client.disconnect()
    if sync:
        after = time.time() + timeout
        while time.time() < after:
            if not connected:
                return
        else:
            raise RuntimeError("Timeout expired while waiting for disconnect.")


def handle_connect(client, userdata, rc):
    """After connection with MQTT broker established, check for errors and
    subscribe to topics."""
    global connected
    connected = True
    if rc != 0:
        raise IOError("Connection returned result: " + Mqtt.connack_string(rc))
    logging.info("Connection to MQTT broker succeeded.")
    # Subscribe here so that if reconnect the subscriptions are renewed.
    # Subscribe to all messages on and beneath the TOPIC_ROOT
    # Note: this includes messages that we send.
    client.subscribe(TOPIC_ROOT + "/#")


def handle_publish(client, userdata, mid):
    """Called when a publish handshake is finished (depending on the qos)"""
    if mid not in messagesInTransit:
        logging.error("Message with mid: {} was not in transit but was "
                      "passed to handle_publish.")
        return
    topic, payload = messagesInTransit[mid]
    if topic == TOPIC_DISCOVERY:
        logging.info("Successfully published to discovery.")
    del messagesInTransit[mid]


def handle_subscribe():
    # TODO: Handle subscription success, at least with logging info.
    pass


class MQTTDisconnectError(RuntimeError):
    """Raised when disconnected from MQTT while shouldBeConnected is set to
    True. In other words, the disconnection was expected."""


def handle_disconnect(mqttClient, userdata, rc):
    """Callback when disconnected from MQTT broker"""
    global connected
    connected = False
    if shouldBeConnected:
        logging.warning("Disconnected from MQTT.")
        raise MQTTDisconnectError()
    else:
        mqttClient.loop_stop()
        logging.info("Disconnected from MQTT.")


class UnexpectedMessage(NotImplementedError):
    """Raised when a message to TOPIC_ROOT isn't expected so there isn't a
    custom callback."""
    pass


def on_unhandled_message(mqttClient, userdata, msg):
    """Callback on message recieved, not handled by a specific callback. This
    function raises an error if this is unexpected or ignores the message if
    necessary.

    For example, the message should be ignored if it is from this service,
    perhaps posting on TOPIC_DISCOVERY."""
    subsToIgnore = [
        # TODO: When starting / restarting this script, what should be done
        #       on recieving the retained TOPIC_DISCOVERY messsage from the
        #       previous instance?
        TOPIC_DISCOVERY + "/#"
    ]
    if not any(Mqtt.topic_matches_sub(sub, msg.topic) for sub in subsToIgnore):
        raise UnexpectedMessage("Unexpected message recieved at topic [{}] "
                                "with payload [{}].".format(msg.topic,
                                                            msg.payload))


def on_grace_disconnect(mqttClient, userdata, msg):
    """Callback when a smart agent publishes to TOPIC_DISCONNECT_GRACE, aka
    when they want to disconnect."""
    if msg.retain:  # Skip old retained messages.
        logging.debug("Skipping retained message.")
        return
    if len(msg.payload) == 0:
        logging.warning("Smart Agent didn't send id to disconnect.")
        return
    agentID = msg.payload.decode()
    try:
        connectedSmartAgents.remove(agentID)
    except KeyError:
        logging.warning("Smart Agent with id: {} tried to disconnect but was "
                        "not previously connected.".format(agentID))
    else:
        logging.info("Removed Smart Agent with id: {}".format(agentID))
    updateDiscovery(mqttClient)


def on_ungrace_disconnect(mqttClient, userdata, msg):
    """Could do something with unexpected disconnect here. For the moment,
    just do the same as if it was a graceful disconnect."""
    if msg.retain:  # Skip old retained messages.
        logging.debug("Skipping retained message.")
        return
    logging.warning("Ungraceful disconnect from smart agent with id: {}"
                    .format(msg.payload.decode()))
    on_grace_disconnect(mqttClient, userdata, msg)


def on_connect(mqttClient, userdata, msg):
    """Callback when a smart agent and publishes to TOPIC_CONNECT
    with it's agentID."""
    if msg.retain:  # Skip retained messages, they must be old.
        logging.debug("Skipping retained message.")
        return
    if len(msg.payload) == 0:
        logging.warning("Smart Agent didn't send id to connect.")
    agentID = msg.payload.decode()
    if agentID in connectedSmartAgents:
        logging.warning("Smart Agent: {} registered to connect but is already "
                        "recorded as connected.".format(agentID))
        return
    connectedSmartAgents.add(agentID)  # Add to set -> auto remove DUP
    logging.info("Added Smart Agent with id: {}".format(agentID))
    updateDiscovery(mqttClient)


def updateDiscovery(mqttClient):
    """Publishes the current connectedSmartAgents as JSON to TOPIC_DISCOVERY.

    Must pass in the mqttClient instance as returned from run() or passed into
    a message callback."""
    # Ensure that this get sent so use qos=1. Duplicates shouldn't matter.
    trackedPublish(mqttClient, TOPIC_DISCOVERY,
                   json.dumps(list(connectedSmartAgents)), qos=1, retain=True)
    logging.debug("Connected Smart Agents: {}".format(connectedSmartAgents))


def trackedPublish(mqttClient, topic, payload=None, **kwargs):
    """A wrapper for mqttClient.publish() that adds a tuple of (topic,
    content) by mid to the 'messagesInTransit' dictionary so that they can be
    tracked in the handle_publish callback. It also raises an error if the
    client is disconnected because it shouldn't be."""
    result, mid = mqttClient.publish(topic, payload=payload, **kwargs)
    if result != Mqtt.MQTT_ERR_SUCCESS:
        raise RuntimeError("Should not be disconnected")
    messagesInTransit[mid] = (topic, payload)


if __name__ == "__main__":
    runningClient = run()  # Setup and run the client.
    logging.info("Input something to quit.")
    input("")   # TODO: Better way of keeping this running forever
