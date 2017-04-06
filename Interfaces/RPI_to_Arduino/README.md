# RPI to Arduino

	Pythonic interface between Pi and Arduino. Allows devices to send messages to each other, and to other members on the 
	network using the protocol:
	
	<Source MAC address|Destination MAC address|Message Content>
	
	For now, the example python script (running on a Raspberry pi) sends a message to an arduino and receives a 
	confirmation message.
	
## Requirements

	Will write more in this section once I've got it working in the second raspberry pi on a clean install. 
	- Python 2 (Pybluez does not have all the required features on Python 3)
	- Linux; e.g. Raspbian (Again, pybluez does not have all the required features on Windows - although some of 
	the features would still work)
	- Bluez (I think - setup requires the use of bluetoothctl the first time, so that the user can put in a password)
	
	
## Initial setup (for each device pair)
 rfkill unblock bluetooth
	sudo bluetoothctl
	agent on
	scan on
	default-agent
	pair addr
	1234
	
