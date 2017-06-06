"""
Runs an mqtt client that provides broker services.

Services
--------
Discovery:
    - Maintains a list of connected smart agents as the retained message on
      TOPIC_DISCOVERY. This means that on subscription to TOPIC_DISCOVERY,
      a message with the currently connected devices will imediately be sent.
    - List is encoded as JSON with each connected agentID as a string within a
      list/array.


Smart Agent Setup
------------
Connect / Disconnect:
    - All smart agents must post their ID on TOPIC_DISCONNECT_GRACE before
      gracefully disconnecting.
    - All smart agents must set their will to post their ID on
      TOPIC_DISCONNECT_UNGRACE.


"""
import paho.mqtt.client as Mqtt
import json
import logging

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

# The current list of connected clients
connectedSmartAgents = set()
# Setup logging
logging.basicConfig(level=logging.INFO)


def run():
    """Sets up an mqtt client, registers the handlers and starts a
    threaded loop."""
    # Use this protocol version to suit the particular broker..
    client = Mqtt.Client(protocol=Mqtt.MQTTv31)

    # Register client callbacks (prefix handle)
    client.on_connect = handle_connect
    client.on_disconnect = handle_disconnect

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


def handle_connect(client, userdata, rc):
    """After connection with MQTT broker established, check for errors and
    subscribe to topics."""
    if rc != 0:
        raise IOError("Connection returned result: " + Mqtt.connack_string(rc))
    logging.info("Connection to MQTT broker succeeded.")
    # Subscribe here so that if reconnect the subscriptions are renewed.
    # Subscribe to all messages on and beneath the TOPIC_ROOT
    # Note: this includes messages that we send.
    client.subscribe(TOPIC_ROOT + "/#")


def handle_subscribe():
    # TODO: Handle subscription success, at least with logging info.
    pass


def handle_disconnect(mqttClient, userdata, rc):
    # TODO: Perhaps retry here instead of giving up?
    raise Exception("Should not be disconnected from MQTT.")


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
        logging.info("Skipping retained message.")
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
    logging.warning("Ungraceful disconnect from smart agent with id: {}"
                    .format(msg.payload.decode()))
    on_grace_disconnect(mqttClient, userdata, msg)


def on_connect(mqttClient, userdata, msg):
    """Callback when a smart agent and publishes to TOPIC_CONNECT
    with it's agentID."""
    if msg.retain:  # Skip retained messages, they must be old.
        logging.info("Skipping retained message.")
        return
    if len(msg.payload) == 0:
        logging.warning("Smart Agent didn't send id to connect.")
    agentID = msg.payload.decode()
    if agentID in connectedSmartAgents:
        logging.warning("Smart Agent: {} registered to connect but is already "
                        "recorded as connected.")
        return
    connectedSmartAgents.add(agentID)  # Add to set -> auto remove DUP
    logging.info("Added Smart Agent with id: {}".format(agentID))
    updateDiscovery(mqttClient)


def updateDiscovery(mqttClient):
    """Publishes the current connectedSmartAgents as JSON to TOPIC_DISCOVERY.

    Must pass in the mqttClient instance as returned from run() or passed into
    a message callback."""
    # Ensure that this get sent so use qos=1. Duplicates shouldn't matter.
    result, mid = mqttClient.publish(TOPIC_DISCOVERY,
                                     json.dumps(list(connectedSmartAgents)),
                                     qos=1, retain=True)
    if result == Mqtt.MQTT_ERR_SUCCESS:
        # This is always true if the client is not disconnected.
        # TODO: A callback should be used to check that the message has been
        #       recieved (qos=1) by the broker instead.
        logging.info("Successfully published to discovery.")
        logging.info("Currently my record of connected Smart Agents is: {}"
                     .format(connectedSmartAgents))
    else:
        raise Exception("Should not ")


if __name__ == "__main__":
    runningClient = run()  # Setup and run the client.
    logging.info("Input something to quit.")
    input("")   # TODO: Better way of keeping this running forever
