"""
Runs tests against broker-services provider script.
"""

import pytest
import provider
import paho.mqtt.client as Mqtt
import time
from testfixtures import LogCapture
import logging
import json
import socket


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
        smartAgentsKnown (set)
            The set of Smart Agents that were last published by the provider to
            TOPIC_DISCOVERY. This is stored after being recieved over MQTT.

    """
    def __init__(self, agentID, timeout=3):
        "Sets up the fake client with (str) agentID"
        self.agentID = agentID
        self.publishedMessages = set()
        self.timeout = timeout
        self.smartAgentsKnown = set()

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
        # Add callback when provider posts list of connected clients
        self.client.message_callback_add(provider.TOPIC_DISCOVERY,
                                         self._handle_discover_message)
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

    def _handle_discover_message(self, client, userdata, msg):
        """Callback after recieving a discovery message"""
        self.smartAgentsKnown = set(json.loads(msg.payload.decode()))

    def _handle_disconnect(self, client, userdata, rc):
        """Callback after disconnection."""
        self.connected = False
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
        self.client.disconnect()


def test_run():
    """Tests that a client is setup and that handle_connect is called logging a
    connection to the broker."""
    try:
        with LogCapture() as l:
            p = provider.run()
            l.check(("root", "INFO", "Connecting to MQTT broker..."),
                    ("root", "INFO", "Connection to MQTT broker succeeded."))
    finally:
        provider.stop(p)


def test_subscribe():
    """Tests that the client manages to subscribe after calling run."""
    timeout = time.time() + 3
    try:
        with LogCapture() as l:
            p = provider.run()
            while time.time() < timeout:
                logMessages = set(r.msg for r in l.records)
                if "Subscribed to a topic with mid: 1" in logMessages:
                    break
            else:
                raise Exception("Timeout ended before subscription callback.")
    finally:
        provider.stop(p)


def test_connect_disconnect():
    """Tests that a connection and disconnection doesn't raise errors. Under
    the different options of retaining and not retaining messages or being
    graceful and ungraceful."""
    for option in range(8):
        graceful = bool(option & 1)
        retainConnect = bool(option & 2)
        retainDisconnect = bool(option & 4)
        with LogCapture() as l:
            try:
                p = provider.run()
                sa = SmartAgent("Id")
                sa.setup()
                # Wait for the two messages to be published before advancing
                sa.wait(sa.registerConnect(retain=retainConnect))
                sa.wait(sa.registerDisconnect(retain=retainDisconnect,
                                              graceful=graceful))
                # Crudely wait here for provider to recieve the messages from
                # the broker.
                time.sleep(1)
            finally:
                sa.disconnect()
                provider.stop(p, finishMessages=True, sync=True)

        logMessages = set(r.msg for r in l.records)
        logLevels = list(r.levelno for r in l.records)
        # Use assert + l.records rather than the check() function because
        # the order that these messages will come (including perhaps other
        # log messages) is unknown.
        assert "Connecting to MQTT broker..." in logMessages
        assert "Connection to MQTT broker succeeded." in logMessages
        assert "Subscribed to a topic with mid: 1" in logMessages
        assert "Added Smart Agent with id: Id" in logMessages
        assert "Successfully published to discovery." in logMessages
        assert "Removed Smart Agent with id: Id" in logMessages
        assert "Successfully published to discovery." in logMessages
        assert "Disconnected from MQTT." in logMessages
        if graceful:
            assert all(l <= logging.INFO for l in logLevels)
        if not graceful:
            assert ('Ungraceful disconnect from smart agent '
                    'with id: Id') in logMessages
            assert all(l <= logging.WARN for l in logLevels)
            assert logLevels.count(logging.WARN) == 1
        l.uninstall()


def test_unhandled_message():
    """Tests that messages to TOPIC_ROOT which aren't expected are logged"""
    test_topics = [  # Topics that aren't expected
        provider.TOPIC_ROOT,
        provider.TOPIC_DISCONNECT,  # Disonnect without grace/ungrace
        provider.TOPIC_ROOT + "/somethingRandom",
        # Truncated
        provider.TOPIC_ROOT + "/connec",
        provider.TOPIC_ROOT + "/disonnect/gracefu",
        provider.TOPIC_ROOT + "/disconnect/ungracefu",
        # Extra
        provider.TOPIC_ROOT + "/connectANDEXTRA",
        provider.TOPIC_ROOT + "/EXTRAANDconnect",
        provider.TOPIC_DISCONNECT + "/gracefulANDEXTRA",
        provider.TOPIC_DISCONNECT + "/EXTRAANDgraceful",
        provider.TOPIC_DISCONNECT + "/ungracefulANDEXTRA",
        provider.TOPIC_DISCONNECT + "/ANDEXTRAungraceful",
        # Beneath topic
        provider.TOPIC_CONNECT + "/extraTopicLevel",
        provider.TOPIC_DISCONNECT_GRACE + "/extraTopicLevel"
    ]
    test_payload = b"payload"
    try:
        p = provider.run()
        sa = SmartAgent("Id")
        sa.setup()
        mids = []  # List of mids to wait for publish
        with LogCapture() as l:
            for topic in test_topics:
                result, mid = sa.client.publish(topic,
                                                test_payload, qos=2)
                assert result == Mqtt.MQTT_ERR_SUCCESS
                mids.append(mid)
            for mid in mids:
                sa.wait(mid)   # Wait for all the messages to be published
            # Wait for the provider to deal with the published messages
            time.sleep(1)
        logMessages = set(r.msg for r in l.records)
        logLevels = list(r.levelno for r in l.records)
        assert all(l <= logging.WARN for l in logLevels)
        toFormat = ("Unexpected message recieved at topic [{}] with "
                    "payload [{}].")
        expectedMessages = set(toFormat.format(topic, test_payload)
                               for topic in test_topics)
        assert all(expected in logMessages for expected in expectedMessages)
        assert logLevels.count(logging.WARN) == len(expectedMessages)
    finally:
        sa.disconnect()
        provider.stop(p)


def test_last_will():
    """Tests that shutting down the underlying socket causes the last will to
    be sent."""
    p = provider.run()
    try:
        # Create a Smart Agent that will register connection with a will
        # and then disconnect
        sa = SmartAgent("Id1")
        sa.setup()
        sa.wait(sa.registerConnect())

        with LogCapture() as l:
            # Close the MQTT socket, forcing unexpected disconnect
            soc = sa.client.socket()
            soc.shutdown(socket.SHUT_RDWR)

            # Wait for disconnection
            timeout = time.time() + 3
            while time.time() < timeout:
                if sa.connected is False:
                    break
            else:
                raise RuntimeError("Exceeded timeout on disconnect.")
            # Wait for provider to register ungraceful disconnect
            time.sleep(1)
        logMessages = list(r.msg for r in l.records)
        logLevels = list(r.levelno for r in l.records)
        assert logMessages.count("Ungraceful disconnect from smart "
                                 "agent with id: Id1") == 1
        assert logMessages.count("Removed Smart Agent with id: Id1") == 1
        assert logLevels.count(logging.WARN) == 1
    finally:
        provider.stop(p)
