import eventlet
import json
from flask import Flask, render_template
from flask_mqtt import Mqtt
from flask_socketio import SocketIO
from flask_bootstrap import Bootstrap

# Finally, need this so that we can change the protocol
from paho.mqtt.client import Client, MQTTv31

eventlet.monkey_patch()

app = Flask(__name__)
app.config['SECRET'] = 'my secret key'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['MQTT_BROKER_URL'] = 'localhost'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_REFRESH_TIME'] = 1.0  # refresh time in seconds

# Initialise the client WITHOUT the app
mqtt = Mqtt()

# Perform open heart surgery on the brand new object, setting the protocol to the old version
mqtt.client = Client(protocol=MQTTv31)

# Now we initialise it with the app
mqtt.init_app(app)

socketio = SocketIO(app)
bootstrap = Bootstrap(app)

@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('publish')
def handle_publish(json_str):
    data = json.loads(json_str)
    mqtt.publish(data['topic'], data['message'])


@socketio.on('subscribe')
def handle_subscribe(json_str):
    data = json.loads(json_str)
    mqtt.subscribe(data['topic'])


@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    data = dict(
        topic=message.topic,
        payload=message.payload.decode()
    )
    socketio.emit('mqtt_message', data=data)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, use_reloader=True)
