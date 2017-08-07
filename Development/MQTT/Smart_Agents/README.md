## Smart agents

In this context, a smart agent is a device with an operating system. Our smart agents are Raspberry Pis running Raspbian and PCs running varients of Windows and Linux. A smart agent will generally have TCP/IP networking to communicate with ohter smart agents and the **cloud**. It may also communicate with **edge devices** via bluetooth or serial cables.

In their simplest form, smart agents act as intermediaries between their connected edge devices and the cloud, providing networking capabilities and security that would be impossible for the more limited edge devices.

**Communication with the cloud**

All communication with the cloud is via the MQTT protocol over TCP/IP. The cloud acts as a **MQTT Broker**, so the smart agents need only publish and subscribe as appropriate.

**Communication with edge devices: Bluetooth**

A smart agent can connect up to seven devices in a Bluetooth piconet. The smart agent scans for devices with a friendly name matching a predefined address pattern, and then attempts to connect.

This approach has its limitations. Each of our smart agents has a single Bluetooth chip. This means that the agent cannot scan for devices and receive/send messages concurrently. Since scanning takes approx 20 seconds, regular scanning has an adverse effect on real-time communications. Since communications are buffered, it might be possible to cope with a backlog - but there would be a 20s delay involved.

Because of the scanning problem, it is preferable that the smart agent relay and the edge devices do not move relative to each other, and that the smart agent is provided with a list of devices that it should be connected to, to prevent unnecessary scanning. While this seems restrictive, it might work adequately for a variety of use cases - such as statically placed sensors in a house or vehicle controlled by a central smart agent.

**Communication with edge devices: Serial cable**

The simplest smart agent - edge device connection is via serial cable. While this may not be practical for some applications, it does allow for a stable connection with low device discovery costs and a very high maximum rate of data transfer. It also solves the power problem, since the smart agent and edge device(s) can be powered by the same source (normally a mains power socket).

**Code**

All our code for the smart agents is written in Python 3. We make use of the Pybluez library [See installation notes] to handle bluetooth connections.