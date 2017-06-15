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
        status_topic (str)
            The topic to use to update this agent's status.
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
        msgsRecieved (list)
            A list of messages recieved as paho.mqtt.client.MQTTMessage
            instances. Each has a topic, payload, qos, retain, mid.

    """
    def __init__(self, agentID, timeout=3):
        "Sets up the fake client with (str) agentID"
        self.agentID = agentID
        self.status_topic = provider.TOPIC_STATUS.replace("+", self.agentID)
        self.publishedMessages = set()
        self.timeout = timeout
        self.smartAgentsKnown = set()
        self.msgsRecieved = []
        self.connected = False

    def setup(self):
        """Sets up an mqtt client, registers the handlers + will and starts a
        threaded loop."""
        # Use this protocol version to suit the particular broker.
        self.client = Mqtt.Client(protocol=Mqtt.MQTTv31)
        self.client.on_connect = self._handle_connect
        self.client.on_message = self._handle_message
        self.client.on_disconnect = self._handle_disconnect
        self.client.on_publish = self._handle_publish
        self.client.will_set(self.status_topic,
                             payload=provider.STATUS_DISCONNECTED_UNGRACE,
                             retain=True, qos=1)
        # Add callback when provider posts list of connected clients
        self.client.message_callback_add(provider.TOPIC_DISCOVERY,
                                         self._handle_discover_message)
        self.client.connect(provider.HOSTNAME, port=provider.PORT)
        self.client.loop_start()  # Start a threaded loop in the background.

    def _handle_connect(self, client, userdata, flags, rc):
        """After connection established, check for errors and subscribe
        to topics."""
        if rc != 0:
            raise IOError("Connection returned result: " +
                          Mqtt.connack_string(rc))
        self.connected = True

    def _handle_message(self, client, userdata, msg):
        """Callback after recieving a message"""
        self.msgsRecieved.append(msg)

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

    def registerConnect(self, timeToUse=None, retain=True):
        """Register with broker-services by publishing agentID to
        TOPIC_STATUS.

        Default to True and current time but allow editing these for
        testing."""
        if timeToUse is None:
            timeToUse = time.time()  # Default to current time
        msg = provider.STATUS_CONNECTED + str(timeToUse)
        result, mid = self.client.publish(self.status_topic, msg,
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
        """Fake disconnection by publishing agentID to TOPIC_STATUS.
        The graceful flag determines the exact topic and the retain flag
        determines whether it is retained."""
        status = (provider.STATUS_DISCONNECTED_GRACE if graceful
                  else provider.STATUS_DISCONNECTED_UNGRACE)
        result, mid = self.client.publish(self.status_topic, status,
                                          retain=retain, qos=2)
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
            p = provider.run(sync=True)
            time.sleep(0.1)  # Sleep for mosquitto to respond
            p.loop()
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
    the different options of retaining and not retaining connect or being
    graceful and ungraceful."""
    for option in range(4):
        graceful = bool(option & 1)
        retainConnect = bool(option & 2)
        # Disconnect must be retained otherwise the next test will be
        # influenced
        retainDisconnect = True
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
            try:
                assert all(l <= logging.WARN for l in logLevels)
            except:
                for l in logLevels:
                    print(l)
                raise
            assert logLevels.count(logging.WARN) == 1
        l.uninstall()


def test_unexpected_status():
    """Tests that an unexpected status is logged"""
    p = provider.run()
    sas = []
    wrong_strings = [
        "",
        provider.STATUS_DISCONNECTED_GRACE[:-1],
        provider.STATUS_DISCONNECTED_GRACE + "extra",
        provider.STATUS_DISCONNECTED_UNGRACE[:-1],
        provider.STATUS_DISCONNECTED_UNGRACE + "extra"
    ]
    wrong_times = [provider.STATUS_CONNECTED]
    wrong_times += [(provider.STATUS_CONNECTED + "{}" + str(time.time())
                     ).format(extraChar)
                    for extraChar in ("|", ",", ".")]
    test_payloads = wrong_strings + wrong_times
    try:
        mids = []  # List of mids to wait for publish
        with LogCapture() as l:
            for payload in test_payloads:
                sa = SmartAgent("Id_unexpected_status_" + payload)
                sas.append(sa)
                sa.setup()
                result, mid = sa.client.publish(sa.status_topic,
                                                payload, qos=2)
                assert result == Mqtt.MQTT_ERR_SUCCESS
            mids.append(mid)
            for mid, sa in zip(mids, sas):
                sa.wait(mid)   # Wait for all the messages to be published
            # Wait for the provider to deal with the published messages
            time.sleep(1)
        logMessages = list(r.msg for r in l.records)
        logLevels = list(r.levelno for r in l.records)
        assert all(l <= logging.WARN for l in logLevels)
        warn_string = "Status update is neither connect or disconnect: {}"
        warn_time = "Couldn't parse time from connect status: {}"
        try:
            for s in wrong_strings:
                assert warn_string.format(s) in logMessages
            for s in wrong_times:
                assert warn_time.format(s) in logMessages
        except:
            for m in logMessages:
                print(m)
            raise
        assert logLevels.count(logging.WARN) == (len(wrong_strings)
                                                 + len(wrong_times))
        provider.connectedSmartAgents = dict()

    finally:
        for sa in sas:
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


def test_unexpected_disconnect():
    """Tests that an error is raised on broker unexpected disconnect"""
    p = provider.run(sync=True)
    # Close the socket
    soc = p.socket()
    soc.shutdown(socket.SHUT_RDWR)
    with pytest.raises(provider.MQTTDisconnectError):
        p.loop()


def test_starting_request_sent_on_connection():
    """Tests that starting the provider publishes on TOPIC_REQUEST to
    request SmartAgents that are already connected to post that they are."""
    sa = SmartAgent("ID1")
    sa.setup()
    stopAt = time.time() + 10
    while time.time() < stopAt:
        if sa.connected:
            break
    else:
        raise RuntimeError("Timeout expired before SA connected.")
    sa.client.subscribe(provider.TOPIC_ROOT + "/#")
    # Ideally callback should be handled here but until it stops working,
    # this is only a test
    p = provider.run()
    try:
        stopAt = time.time() + 10
        while time.time() < stopAt:
            if any(Mqtt.topic_matches_sub(provider.TOPIC_REQUEST, m.topic)
                   for m in sa.msgsRecieved):
                break
        else:
            raise RuntimeError("Timeout expired and no message on "
                               "TOPIC_REQUEST.")
    finally:
        sa.disconnect()
        provider.stop(p)


def test_updateSmartAgents():
    """Checks that updateSmartAgents() returns True or False depending on
    whether updateDiscovery() needs to be called"""
    agentID = "id"

    payloadOptions = [
        (provider.STATUS_CONNECTED + str(0.0)).encode(),
        (provider.STATUS_CONNECTED + str(1.0)).encode(),
        provider.STATUS_DISCONNECTED_GRACE.encode(),
        provider.STATUS_DISCONNECTED_UNGRACE.encode()
    ]

    def runTest(payload, old, expectedResult):
        m = Mqtt.MQTTMessage(0, topic=agentID.encode() + b"/status")
        m.payload = payload
        print(m.topic, m.payload, old)
        assert provider.updateSmartAgents(m, old) is expectedResult

    # Add new
    runTest(payloadOptions[0], {}, True)
    runTest(payloadOptions[0], {"old1": 0.0}, True)
    runTest(payloadOptions[0], {"old1": 0.0, "old2": 0.0}, True)
    runTest(payloadOptions[1], {}, True)
    runTest(payloadOptions[1], {"old1": 0.0}, True)
    runTest(payloadOptions[1], {"old1": 0.0, "old2": 0.0}, True)

    # Already added - but time will have updated
    runTest(payloadOptions[0], {agentID: 0.0}, False)
    runTest(payloadOptions[0], {agentID: 0.0, "old1": 0.0}, False)
    runTest(payloadOptions[0], {agentID: 0.0, "old1": 0.0, "old2": 0.0}, False)
    runTest(payloadOptions[1], {agentID: 0.0}, False)
    runTest(payloadOptions[1], {agentID: 0.0, "old1": 0.0}, False)
    runTest(payloadOptions[1], {agentID: 0.0, "old1": 0.0, "old2": 0.0}, False)

    # Disconnect new
    runTest(payloadOptions[2], {}, False)
    runTest(payloadOptions[2], {"old1": 0.0}, False)
    runTest(payloadOptions[2], {"old1": 0.0, "old2": 0.0}, False)
    runTest(payloadOptions[3], {}, False)
    runTest(payloadOptions[3], {"old1": 0.0}, False)
    runTest(payloadOptions[3], {"old1": 0.0, "old2": 0.0}, False)

    # Disconnect remove
    runTest(payloadOptions[2], {agentID: 0.0}, True)
    runTest(payloadOptions[2], {agentID: 0.0, "old1": 0.0}, True)
    runTest(payloadOptions[2], {agentID: 0.0, "old1": 0.0, "old2": 0.0}, True)
    runTest(payloadOptions[3], {agentID: 0.0}, True)
    runTest(payloadOptions[3], {agentID: 0.0, "old1": 0.0}, True)
    runTest(payloadOptions[3], {agentID: 0.0, "old1": 0.0, "old2": 0.0}, True)
