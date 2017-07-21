
"""
Broker services

Listens to mf2c/broker_services/status to build up a map of who is online. 
Handles encryption/decryption for clients and stores a database of public keys.
"""
import time
import mf2c

hostname = "vm69.nubes.stfc.ac.uk"
port = 1883
broker_agent = mf2c.BrokerServices(hostname, 'broker_services')
broker_agent.setup()

try:
    while True:
        # Believe me, if you don't introduce a delay, this program will 
        # happily take up 90% of your CPU...
        time.sleep(0.1)
        
        # Get the messages in the buffer and deal with ping requests
        messages = broker_agent.loop()
        if messages != []:
            for message in messages:
                print(message)

except Exception as e:
    raise e
finally:
    # clean up
    broker_agent.clean_up()

