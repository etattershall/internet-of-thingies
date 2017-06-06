"""
Runs tests against broker-services provider script.
"""

import pytest
import provider
import paho.mqtt.client as Mqtt
import time
from testfixtures import log_capture, LogCapture
import logging


class SmartAgent():
    """Creates a fake smart agent connection to the broker for testing
    broker-services.

    Members:
        agentID (str)
            The unique agent identifier.
        client (paho.mqtt.client.Client)
            The mqtt client instance.
        connected (bool)
            Set True on connect and False on disconnect (callbacks).
        publishedMessages (set)
            A set of the mid of messages that have been published.
            QOS=0 -> Message left client
            QOS=1 -> Message(s) recieved by broker
            QOS=2 -> Message recieved by broker
        timeout (int)
            The number of seconds to wait for a message to call the on_publish
            timeout before raising an error in the wait method.

    """
    def __init__(self, agentID, timeout=3):
        "Sets up the fake client with (str) agentID"
        self.agentID = agentID
        self.publishedMessages = set()
        self.timeout = timeout

    def setup(self):
        """Sets up an mqtt client, registers the handlers + will and starts a
        threaded loop."""
        # Use this protocol version to suit the particular broker.
        self.client = Mqtt.Client(protocol=Mqtt.MQTTv31)
        self.client.on_connect = self._handle_connect
        self.client.on_message = self._handle_message
        self.client.on_disconnect = self._handle_disconnect
        self.client.on_publish = self._handle_publish
        # TODO: Set qos here?
        self.client.will_set(provider.TOPIC_DISCONNECT_UNGRACE,
                             payload=self.agentID)
        self.wantToBeConnected = True
        self.client.connect(provider.HOSTNAME, port=provider.PORT)
        self.client.loop_start()  # Start a threaded loop in the background.

    def _handle_connect(self, client, userdata, flags, rc):
        """After connection established, check for errors and subscribe
        to topics."""
        self.connected = True
        if rc != 0:
            raise IOError("Connection returned result: " +
                          Mqtt.connack_string(rc))

    def _handle_message(self, client, userdata, msg):
        """Callback after recieving a message"""
        raise NotImplementedError()

    def _handle_disconnect(self, client, userdata, rc):
        """Callback after disconnection."""
        self.connected = False
        if self.wantToBeConnected:
            raise Exception("Shouldn't be disconnected here!")
        else:
            self.client.loop_stop()

    def _handle_publish(self, client, userdata, mid):
        """Record messages that have been published"""
        self.publishedMessages.add(mid)

    def registerConnect(self, retain=False):
        """Register with broker-services by publishing agentID to
        TOPIC_CONNECT"""
        result, mid = self.client.publish(provider.TOPIC_CONNECT, self.agentID,
                                          retain=retain, qos=2)
        assert result == Mqtt.MQTT_ERR_SUCCESS  # Shouldn't be disconnected
        return mid

    def wait(self, mid):
        """Waits for mid to be added to self.publishedMessages. If self.timeout
        expires, this raises a runtime error."""
        timeout = time.time() + self.timeout
        while mid not in self.publishedMessages:
            if time.time() > timeout:
                raise RuntimeError("Timeout reached before msg publish.")

    def registerDisconnect(self, graceful=True, retain=False):
        """Fake disconnection by publishing agentID to TOPIC_DISCONNECT.
        The graceful flag determines the exact topic and the retain flag
        determines whether it is retained."""
        topic = (provider.TOPIC_DISCONNECT_GRACE if graceful
                 else provider.TOPIC_DISCONNECT_UNGRACE)
        result, mid = self.client.publish(topic, self.agentID, retain=retain,
                                          qos=2)
        assert result == Mqtt.MQTT_ERR_SUCCESS
        return mid

    def disconnect(self):
        """Sends disconnect message and closes the connection. Doesn't post
        the will. Reconnect with client.reconnect()."""
        self.wantToBeConnected = False
        self.client.disconnect()


@log_capture(level=logging.INFO)
def test_run(l):
    """Tests that a client is setup and that handle_connect returns within 1
    second logging that it succeeded."""
    try:
        p = provider.run()
        l.check(("root", "INFO", "Connecting to MQTT broker..."),
                ("root", "INFO", "Connection to MQTT broker succeeded."))
        # TODO: Test subscribe
    finally:
        provider.stop(p)
