from piduino import utils

this_device = utils.read_local_bdaddr()
outgoing_message = 'Hello World!'

print('Searching for Arduinos...')
destinations = utils.scan('SCD_ARDUINO')

if len(destinations) == 0:
    print('No Arduinos found!')


else:
    destination = destinations[0]
    print('Attempting to connect to device at '+destination)
    socket = utils.connect(destination)
    print('Connected!')
    outgoing_packaged_message = utils.package(this_device, destination, outgoing_message)
    print('Sending message...')
    success = utils.send_message(socket, outgoing_packaged_message)
    if success:
        print('Message sent')
        print('Waiting for response...')
        incoming_packaged_message = utils.listen(socket)
        if incoming_packaged_message == '':
            print('No reply from device!')
        else:
            message_source, message_destination, incoming_message = utils.unpackage(incoming_packaged_message)
            print('Reply: ' + incoming_message)
           
    else:
        print('Message not sent')
    utils.disconnect(socket) 

