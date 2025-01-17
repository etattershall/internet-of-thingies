## Current IoThingies architecture

![](Architecture.png)


## Topics
```
MQTT is a subscription/publication protocol. This means that instead of sending direct messages to each other, devices subscribe and publish to topics managed by a central broker device. We came up with a structure of standard topics for devices to post on for our prototype application. 

Each smart agent posts details about its state using the topic structure shown below. 

Pi1/public                          (data that the customer can see)
          /arduino1/input/sensor1   (e.g. state of an LDR or button)
                         /sensor2
                         ...
                   /output/sensor3  (e.g. state of an LED)
                          /sensor4
                           ...
          /arduino2/...
          /arduino3/...
          ...
   /private                         (behind-the-scenes data)
           /log/...                 (debugging information to be sent to central log)
           /error/...
           /status                  (connected, disconnected or disconnected ungracefully)
           /edge                    (json list of edge devices (arduinos) for
                                    this PI)
Pi2/public/...
   /private/...
Pi3/...
Pi4/...
...

The broker services cloud application keeps a dictionary of connected devices. It shares this list with all smart agents on 
the “broker-services/discover” topic.

broker-services/discover          (json dict of connected smart agents and their dependent edge devices)
               /request           (request repost status)
               /hello             (each smart agent posts its name on this topic when it first connects)

In the future, if we were to implement an application on the cloud, smart agents would be able to request data from 
broker-services. They would also be able to restrict access to their data or request its deletion in the same manner.

```

### Setup / Explanation

#### Status
All smart agents should publish retained messages on `agentID/private/status`
with:
- `"C" + str(time.time())` just after connecting
- `"DG"` just before disconnecting gracefully
- `"DU"` as their last will

For the moment, `time.time()` is not used. It could be used in the future to clean up devices that haven't contacted in a while. It may as well be implemented now for the future. Note that this seems to be common across SCD Cloud + RPI (I assume the Internet is used to sync this).

It might be nice to import [provider.py](Cloud/broker_services/provider.py)'s `STATUS_CONNECTED`, `STATUS_DISCONNECTED_GRACE`, `STATUS_DISCONNECTED_UNGRACE`,  rather than hardcode `"C", "DG", "DU"` respectively.


There are now two ways to get the currently connected smart agents:

1. Subscribing to `+/private/status`, anyone can get the current status of any/all devices (provided retained messages are used). [provider.py](Cloud/broker_services/provider.py)'s `updateSmartAgentsOrEdgeDevices()` could be imported by a smart agent and called in the callback to receiving a message here or on `agentID/private/edge` to update a local dictionary of connected smart agents to their edge devices.
2. `broker-services/discover` is updated by the python script [provider.py](Cloud/broker_services/provider.py). Containing a json encoded dictionary of the currently connected smart agents to a list of their edge devices. It posts a retained message here so a newly connected smart agent can immediately get information as soon as they subscribe.

#### Edge

All smart agents should publish retained messages on `agentID/private/edge` with a json encoded list of the smart agents connected to it (publish every time this changes).
