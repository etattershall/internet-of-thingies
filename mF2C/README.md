# mF2C module Architecture

## The Public API
```python
import mf2c

smart_agent = mf2c.SmartAgent()
smart_agent.setup(hostname='vm219.nubes.stfc.ac.uk', name='A')

try:
	while True:
		# Receive messages
		messages, pingacks = smart_agent.loop()
		for m in messages:
			print(m)
		
		# Send messages
		my_message = {
			'payload': 'How are you?'
		}
		smart_agent.send(recipients=['B', 'C'], message=mymessage, security=0)
		
		
except Exception as e:
	raise e
finally:
	client.clean_up()
```
	
## Behind the scenes

**Each agent subscribes to a number of 'inboxes'**

These are:
```
mf2c/[name]/public
mf2c/[name]/protected
mf2c/[name]/private
mf2c/[name]/public/pingreq
mf2c/[name]/public/pingack
```

**When an MQTT message is sent, it goes to the recipients own inboxes**
```
mf2c/[recipient]/public
mf2c/[recipient]/protected
mf2c/[recipient]/private
```

**Messages are dictionary objects**

e.g.
```
my_message = {
	'application_parameter1': ['some', 'stuff'],
	'application_parameter2': 476752306,
	...
}
```
The API adds the arguments:
```
'source': device_name
'timestamp: '1500648668'
```
Before the message is sent, it is flattened into a string using python's JSON library

**In the cloud**

- Public messages are just passed on as usual - they are not normally addressed to the hub.
- Private messages are decrypted, encrypted again with their recipients public keys and sent to their destinations.
