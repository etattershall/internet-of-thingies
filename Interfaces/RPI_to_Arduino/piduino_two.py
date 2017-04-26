import select
from piduino import utils

this_device = utils.read_local_bdaddr()
outgoing_message = 'Hello World!'

print('Searching for Arduinos...')
addresses = utils.scan('SCD_ARDUINO')

if len(addresses) == 0:
    print('No Arduinos found!')


else:
    sockets = {}
    for address in addresses:
        print('Attempting to connect to device at '+address)
        sock = utils.connect(address)
        print('Connected!')
        sockets[address] = sock

    # Create a buffer to store
    buffers = {}
    for address in sockets.keys():
        buffers[address] = ''
        
    while True:
        ready_to_read, ready_to_write, ready_with_errors = select.select(sockets.values(), [], [])
        for sock in ready_to_read:
            incoming_packaged_message = utils.listen(sock)
            print(incoming_packaged_message)

    for sock in sockets:
        utils.disconnect(socket) 

