"""
Runs an mqtt client that provides broker services.

Usage:

Services
--------
Discovery:
    - Maintains a dictionary of connected smart agents as the retained message
      on TOPIC_DISCOVERY. This means that on subscription to TOPIC_DISCOVERY,
      a message with the currently connected devices will imediately be sent.
    - The dictionary is encoded as JSON with each connected agentID as a string
      for the keys. The values are the edgeIDs of Edge Devices that are
      connected to the respective agent.


Smart Agent Setup
-----------------
Connect / Disconnect:
    - All smart agents should publish retained messages on TOPIC_STATUS
      with:
        - STATUS_CONNECTED + str(time.time()) just after connecting
        - STATUS_DISCONNECTED_GRACE just before disconnecting gracefully
        - STATUS_DISCONNECTED_UNGRACE as their last will



"""
import paho.mqtt.client as Mqtt
import json
import logging
import time
from sys import version_info

assert version_info >= (3, 0)


HOSTNAME = "localhost"
PORT = 1883


# Topics will always be joined with a "/" so if you include a "/" at the end
# of these variables (X/) then if they get joined with Y it will be X//Y
# http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/cos01/mqtt-v3.1.1-cos01.pdf
# States that leading or trailing '/' creates a distinct Topic Name and '//'
# IS allowed in a Topic Name.
TOPIC_ROOT = "broker-services"
TOPIC_STATUS = "+/private/status"
TOPIC_EDGE = "+/private/edge"
TOPIC_DISCOVERY = TOPIC_ROOT + "/discover"


STATUS_CONNECTED = "C"
STATUS_DISCONNECTED_GRACE = "DG"
STATUS_DISCONNECTED_UNGRACE = "DU"


# Setup logging
logging.basicConfig(level=logging.INFO)


def run(sync=False):
    """Sets up an mqtt client, registers the handlers and starts a
    threaded loop. If the sync flag is set then client.loop() will have to
    be called manually outside of this function as a threaded loop isn't
    created."""
    global connectedSmartAgents
    global shouldBeConnected
    global messagesInTransit
    # Current map of connected Smart Agents to their list of connected Edge
    # Devices
    connectedSmartAgents = dict()
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
    client.on_subscribe = handle_subscribe

    # Register message callbacks (prefix on)
    client.on_message = on_unhandled_message
    client.message_callback_add(TOPIC_STATUS, on_status_or_edge_change)

    logging.info("Connecting to MQTT broker...")
    client.connect(HOSTNAME, port=PORT)
    if not sync:
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
    if rc != 0:
        raise IOError("Connection returned result: " + Mqtt.connack_string(rc))
    logging.info("Connection to MQTT broker succeeded.")
    # Connected is if the mqtt client is connected to the broker.
    connected = True
    # Subscribe here so that if reconnect the subscriptions are renewed.
    client.subscribe(TOPIC_STATUS)


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


def handle_subscribe(client, userdata, mid, granted_qos):
    """Called after the MQTT client successfully subscribes to a topic."""
    logging.info("Subscribed to a topic with mid: {}".format(mid))


class MQTTDisconnectError(RuntimeError):
    """Raised when disconnected from MQTT while shouldBeConnected is set to
    True. In other words, the disconnection was not expected."""
    pass


def handle_disconnect(mqttClient, userdata, rc):
    """Callback when disconnected from MQTT broker"""
    global connected
    connected = False
    if shouldBeConnected:
        logging.error("Disconnected from MQTT.")
        raise MQTTDisconnectError()
    else:
        mqttClient.loop_stop()
        logging.info("Disconnected from MQTT.")


def on_unhandled_message(mqttClient, userdata, msg):
    """Callback on message recieved, not handled by a specific callback. This
    function raises an error if this is unexpected or ignores the message if
    necessary."""
    if msg.retain:
        return  # Don't keep alerting!
    # Ignore topics which this application posts on so that it doesn't react
    # to its own messages.
    subsToIgnore = [
        TOPIC_DISCOVERY
    ]
    if not any(Mqtt.topic_matches_sub(sub, msg.topic) for sub in subsToIgnore):
        logging.warning("Unexpected message recieved at topic [{}] "
                        "with payload [{}].".format(msg.topic,
                                                    msg.payload))


def on_status_or_edge_change(mqttClient, userdata, msg):
    """Callback when a Smart Agent updates TOPIC_STATUS or TOPIC_EDGE.

    The edge value should be a json encoded list of edgeIDs for the Edge
    Devices connected to that particular Smart Agent.

    The status value should be one of
        - STATUS_CONNECTED + str(time.time())
        - STATUS_DISCONNECTED_UNGRACE
        - STATUS_DISCONNECTED_UNGRACE

    Note that for the moment, the timestamp isn't used.

    This function takes the update and applies it to it's recorded
    connectedSmartAgents, it then publishes the new dict to TOPIC_DISCOVERY if
    there is a change.
    """
    if updateSmartAgentsOrEdgeDevices(msg, connectedSmartAgents):
        updateDiscovery(mqttClient)


def updateSmartAgentsOrEdgeDevices(msg, oldSmartAgents):
    """Given a msg recieved on TOPIC_STATUS or TOPIC_EDGE and the previous
    dictionary of connectedSmartAgents, this updates the dictionary if
    necessary and returns True/False depending on whether there has been a
    change.

    This is separated from on_status_or_edge_change() so that it can
    potentially be imported by a SmartAgent which is also listening to
    TOPIC_STATUS / TOPIC_EDGE so that it can track the connectedSmartAgents
    without broker-services. To do this, a similar callback to
    on_status_or_edge_change() should be implemented on the SmartAgent which
    doesn't include a call to updateDiscovery()
    """
    agentID = msg.topic.split("/", 1)[0]
    payload = msg.payload.decode()

    # Deal with updates to Edge Devices connected to agentID
    if Mqtt.topic_matches_sub(TOPIC_EDGE, msg.topic):
        latestEdgeDevices = json.loads(payload)
        if type(latestEdgeDevices) != list:
            logging.warning("""Didn't get a json list for Edge Devices.""")
            return False
        if agentID in oldSmartAgents:
            if msg.retain:
                logging.debug("Retained Edge Device list")
            if latestEdgeDevices == oldSmartAgents[agentID]:
                logging.debug("""Recieved the same list of Edge Devices for
                              SmartAgent: {}.""".format(agentID))
                return False
            else:
                oldSmartAgents[agentID] = latestEdgeDevices
                logging.info("""Updated the Edge Devices for SmartAgent: {}"""
                             .format(agentID))
                return True
        else:
            if msg.retain:
                # This SmartAgent is not known about and this is an old message
                # so do nothing here
                logging.debug("Retained Edge Device list.")
                return False
            else:
                # If this agent isn't in the dict of smart agents then it
                # either hasn't connected or somehow we have missed the
                # connection. Either way is bad so log this.
                logging.warning("""Recieved list of Edge Devices for an unknown
                                SmartAgent.""")
                # As this is not a retained message, the SmartAgent is clearly
                # connected so add them and their Edge Devices anyway.
                oldSmartAgents[agentID] = latestEdgeDevices
                return True

    # Deal with the updates to the status of agentID
    elif Mqtt.topic_matches_sub(TOPIC_STATUS, msg.topic):
        status = payload
        if status.startswith(STATUS_CONNECTED):  # This ends with timestamp
            if msg.retain:
                logging.debug("Retained connect message")
            try:
                # Could do something with this time in the future.
                float(status.replace(STATUS_CONNECTED, "", 1))
            except ValueError:
                logging.warning("Couldn't parse time from connect status: {}"
                                .format(status))
            if agentID in oldSmartAgents:
                logging.debug("Smart Agent already connected.")
                return False
            else:
                # Add the SmartAgent to the dictionary with an empty list
                # of Edge Devices.
                oldSmartAgents[agentID] = []
                logging.info("Added Smart Agent with id: {}".format(agentID))
                return True
        elif(status == STATUS_DISCONNECTED_GRACE
             or status == STATUS_DISCONNECTED_UNGRACE):
            if msg.retain:  # Skip retained messages, they must be old.
                logging.debug("Skipping retained disconnect message.")
                return False
            # Log ungraceful disconnects
            if status == STATUS_DISCONNECTED_UNGRACE:
                logging.warning("Ungraceful disconnect from smart agent with "
                                "id: {}".format(agentID))
            # Try to delete it + log it else log that it isn't known about
            try:
                del oldSmartAgents[agentID]
            except KeyError:
                logging.warning("Smart Agent with id: {} tried to disconnect "
                                "but was not previously connected."
                                .format(agentID))
                return False
            else:
                logging.info("Removed Smart Agent with id: {}".format(agentID))
                return True
        else:
            logging.warning("Status update is neither connect or "
                            "disconnect: {}".format(status))
            return False
    else:
        logging.warning("Neither TOPIC_EDGE or TOPIC_STATUS was passed to "
                        "updateSmartAgentsOrEdgeDevices(). The topic was {}"
                        .format(msg.topic))
        return False


def updateDiscovery(mqttClient):
    """Publishes the current connectedSmartAgents as JSON to TOPIC_DISCOVERY.

    Must pass in the mqttClient instance as returned from run() or passed into
    a message callback."""
    # Ensure that this get sent so use qos=1. Duplicates shouldn't matter.
    trackedPublish(mqttClient, TOPIC_DISCOVERY,
                   json.dumps(connectedSmartAgents), qos=1, retain=True)
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
