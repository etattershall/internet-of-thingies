"""Send and recieve mqtt on on the command line.

This script demonstrates how to use a purely python mqtt client rather than
using flask on top. It subscribes to all topics and prints recieved messages.

Usage:
    Input your messages to be published in the form '<topic> <message>'.

Example:
    test/hello this is my message

Expected Response:
    REC-> test/hello b'this is my message'
"""

import paho.mqtt.client as Mqtt


def run():
    """Sets up an mqtt client, registers the handlers and starts a
    threaded loop."""
    # Use this protocol version to suit the particular broker..
    client = Mqtt.Client(protocol=Mqtt.MQTTv31)
    client.on_connect = handle_connect
    client.on_message = handle_message
    client.connect("localhost", port=1883)
    client.loop_start()  # Start a threaded loop in the background.
    return client


def handle_connect(thisClient, userdata, rc):
    """After connection established, check for errors and subscribe
    to topics."""
    if rc != 0:
        raise IOError("Connection returned result: " + Mqtt.connack_string(rc))
    thisClient.subscribe("#")


def handle_message(client, userdata, msg):
    """On message recieved, print it out to the console."""
    print("REC->", msg.topic, msg.payload)


def basic_send():
    """Read input in form '<topic> <message>', and publish to broker."""
    cli = input()
    try:
        topic, payload = tuple(cli.split(" ", 1))
    except ValueError:
        print("Not sent, use input format '<topic> <message>'.")
        return
    runningClient.publish(topic, payload)


if __name__ == "__main__":
    print(__doc__)
    running = True
    runningClient = run()  # Setup and run the client.

    while running is True:
        basic_send()  # Read then send messages from the console.
