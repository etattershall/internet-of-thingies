# mF2C module Architecture

## The Public API
```python
import mf2c

client = mf2c.Client()
client.connect()

try:
	while True:
		client.loop()

		# Deal with new messages
		if client.waiting():
			newmessage = client.receive()

		# Send our own messages
		mymessage = mf2c.message(
			recipients = <list>, 	# List of signatures of other users
			security = <int>, 	# public=0, protected=1, private=2.
						# Defaults to private
			payload = <str>,
			qos = 1			# Default value is 1, invisible argument
		)

		client.send(mymessage)
except Exception as e:
	raise e
finally:
	client.disconnect()
```
	
## Behind the scenes

**The MQTT message topic is:**

```
mf2c/[destination id]/private
		     /protected
		     /public
```

**The MQTT payload is**

[signature(encrypted checksum)|flattenedjson(encrypted with JWT if private)]

Where:
```
flattenedjson = {
	source_device: 00000001,
	recipients: [00000002, 00000003],
	payload: 'Do you fancy a coffee?'
}
```
Notes:
- The signature has a fixed length
- Device IDs are fixed length (e.g. 8 characters?)
- Device ID 00000000 is the hub
- If the message is not encrypted, it is sent directly to its recipients
- Private messages are always addressed to the cloud

**In the cloud**

- Public messages are just passed on as usual - they are not normally addressed to the hub.
- I can't remember what happens to protected messages.
- Private messages are decrypted, encrypted again with their recipients public keys and sent to their destinations.
