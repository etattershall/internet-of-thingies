# Project skeleton
## Introduction
- **Why should I read this?** Internet of things waffle 
- **Use cases?** For instance (tweeting fridge door, smart homes, blah. Less work has been done on large, distributed multi-user cases, such as a smart airport (Jen’s use case))
- **Summarise the project in less than 50 words?** mF2C project aims to do this. At STFC, we have been working on prototyping an IoT system using affordable off-the-shelf-components for use as a test bed for developing an IoT security protocol.
-	**What problem does this solve?** internet of things systems are vulnerable because the devices used often have low memory available. Also, the people who set them up don’t worry about security. This leads to problems – e.g. Mirai botnet.
-	**What are you doing to solve this problem?** Using a hierarchical network where more powerful devices can ensure the security and privacy needs of smaller devices.
-	**Tell me what’s in the rest of this paper?** (Write when the rest of the paper has been written!)


Words and phrases to include: 

Proof of concept, prototype, affordable, extensible, adaptable

## Theory and specification
This is the part of the paper where we define some general terms, but don’t go deeply into what we actually did. We will be talking lots of theoretical stuff here. 
### Network Specification
-	The solution architecture we chose is a three layer hierarchal network. 
-	At the base of the pyramid are edge devices (low memory/power/connectivity devices that do not have operating systems and are not capable of storing large keys or doing their own encryption). 
-	Several edge devices may be managed by a single smart agent, a more powerful device with an operating system such as a raspberry pi or a mobile phone. 
-	Smart agents can share information with each other via a Cloud. 
-	Communication is achieved via Bluetooth or serial cable at the lower levels and a popular IoT protocol called MQTT over standard internet connections.
-	Must allow devices to discover each other, share information, etc.
### Privacy Specification
-	We defined three levels of security. These are:
  -	**Public** (nothing needs to be done, anyone can see)
  -	**Protected** (message must be signed so that sender can be verified. Anyone can see message contents)
  -	**Private** (message needs to be signed so that sender can be verified. Payload of message must be encrypted with strong asymmetric encryption)
-	What do we mean by asymmetric encryption? Brief description + mention how big the keys are and how difficult the algorithm is to explain why our edge devices can’t use it.
-	Certificate authority to distribute keys. (We didn’t actually use this, but...). What is a CA?
Communication
- Communication with via Bluetooth. What is Bluetooth? Why is it a good option for communicating with low memory/power/connectivity devices? 
-	Communication via MQTT. What does MQTT stand for? Why is it a better option than standard TCP/IP? Publish/subscribe stuff, explain what the broker is and different levels of quality of service.
Communication diagram
-	Show Jen’s UML diagram, adapted to show what we actually implemented

## Implementation
### Waffle:
-	We wanted to make a prototype for use as a test bed (or proof-of-concept) for future development of an IoT security protocol, blah.
-	Also used for outreach activities, blah
-	Chose to use off-the-shelf component for maximum applicability, blah
### The equipment:
-	We used Arduino Unos (£25-30) as edge devices. They have X inputs and outputs (analog and digital) and can be loaded with pre-compiled programs.
-	HC-05 chip for Bluetooth option (picture of HC-05, range=10m?, cost=£4...)
-	Raspberry pi as smart agents. Stats – 1GB RAM, can be run headless, use linux...
-	SCD Cloud machine (Scientific Linux 7) hugely useful, blah. Broker (mosquitto) runs on cloud, as does telemetry and monitoring applications (broker services) and a flask app.
### Pretty diagrams and pictures of the equipment
-	Diagram with the pretty logos on it I made for the pre-coffee talk. I’ll go find it.
The programming
- Exact topic structure that we used
### Pretty graph of some data collected
-	Graph, and also some brief waffle about what’s on the graph.
-	Picture of the Arduino/raspberry pi setup

## Dissemination and Future work
-	Have created an API for use by the project partners. Handles all of the MQTT stuff under the surface + security (public/protected/private)
-	Botnet attack simulation
-	Virtualisation via docker containers
-	Machine learning of some unspecified thing
-	Anything else you can think of

## Conclusion
-	Slightly reword the introduction
-	Write a really brief summary of what we did and how it can be used in the future by our project partners (API) and our organisation (oureach, monitoring) 
Acknowledgements
-	EU flag
-	Funded by H2020, EU, mF2C, ...
-	With thanks to our project partners, ...
