## Edge devices

Edge devices do not have an operating system. Usually they are microcontrollers with one or more inputs and outputs (e.g. light intensity sensor, LED, pushbutton). The microcontrollers that we have available are Arduino Unos.

Edge devices cannot directly communicate with the **cloud**. Instead, they communicate with a **smart agent** which then relays their messages. Communication is over serial, or via a bluetooth chip if the microcontroller is adequately equipped (e.g. with a HC-05 chip or similar). Messages are packages as JSON objects - edge devices have no knowledge of the MQTT protocol.