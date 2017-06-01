'''
A (very) basic test of the escaping. This script adapts 'pyduino_example.py'
to send a number of different strings to the arduino. The arduino echoes them
back and the script checks that they are the same (having been escaped to be
sent and then unescaped and reescaped on the arduino and finally unescaped
on the PI)

The arduino should load protocol.ino which is setup to echo anything which is
sent back to the PI
'''

from piduino import utils

ESCAPE = utils.ESCAPE
PACKET_START = utils.PACKET_START
PACKET_END = utils.PACKET_END
PACKET_DIVIDE = utils.PACKET_DIVIDE

escapedValues = {
    "": "",
    ESCAPE: ESCAPE + ESCAPE,
    PACKET_START: ESCAPE + PACKET_START,
    PACKET_END: ESCAPE + PACKET_END,
    PACKET_DIVIDE: ESCAPE + PACKET_DIVIDE,
    ESCAPE + PACKET_START: ESCAPE + ESCAPE + ESCAPE + PACKET_START,
    ESCAPE + PACKET_END: ESCAPE + ESCAPE + ESCAPE + PACKET_END,
    ESCAPE + PACKET_DIVIDE: ESCAPE + ESCAPE + ESCAPE + PACKET_DIVIDE,
    "normal text": "normal text",
    ESCAPE + PACKET_START + PACKET_DIVIDE + PACKET_END:
        (ESCAPE + ESCAPE + ESCAPE + PACKET_START + ESCAPE + PACKET_DIVIDE +
         ESCAPE + PACKET_END)
}


def run():
    global this_device, socket, destination
    this_device = utils.read_local_bdaddr()

    print('Searching for Arduinos...')

    destinations = utils.scan('SCD_ARDUINO')
    if len(destinations) == 0:
        print('No Arduinos found!')
    else:
        destination = destinations[0]
        print('Attempting to connect to device at '+destination)
        socket = utils.connect(destination)
        print('Connected!')
        for startOfString in ["", "start"]:  # test starting with normal chars
            for endOfString in ["", "end"]:  # test ending with normal chars
                for testItem, testResponse in escapedValues.items():
                    fullTest = startOfString + testItem + endOfString
                    # fullResponse = startOfString + testResponse + endOfString
                    actualResponse = send_message_wait_response(fullTest)
                    if actualResponse[2] != fullTest:
                        print("Test failed: {} not {}"
                              .format(fullTest, actualResponse[2]))
                    else:
                        print("Test passed: {}".format(fullTest))


def send_message_wait_response(outgoing_message):
    outgoing_packaged_message = utils.package(this_device, destination,
                                              outgoing_message)
    success = utils.send_message(socket, outgoing_packaged_message)
    if success:
        incoming_packaged_message = utils.listen(socket)
        if incoming_packaged_message == '':
            raise IOError("No reply!")
        else:
            return utils.unpackage(incoming_packaged_message)

    else:
        raise IOError("Message not sent")
    utils.disconnect(socket)


run()
