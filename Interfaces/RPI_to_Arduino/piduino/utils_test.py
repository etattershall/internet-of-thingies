from utils import (escape, package, unpackage, ESCAPE, TO_ESCAPE, PACKET_START,
                   PACKET_DIVIDE, PACKET_END)

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


def test_basic_escaping():
    for startOfString in ["", "start"]:  # test starting with normal chars
        for endOfString in ["", "end"]:  # test ending with normal chars
            for testItem, testResponse in escapedValues.items():  # test above
                fullTest = startOfString + testItem + endOfString
                fullResponse = startOfString + testResponse + endOfString
                actualResponse = escape(fullTest)
                if actualResponse != fullResponse:
                    print("Test escape failed: {} should be {} not {}"
                          .format(fullTest, fullResponse, actualResponse))
                else:
                    print("Test escape passed: {}".format(fullTest))


def test_package():
    BT = "11:11:11:11:11:11"  # default bt address
    basicPackage = (PACKET_START + BT + PACKET_DIVIDE + BT + PACKET_DIVIDE
                    + "{}" + PACKET_END)
    for startOfString in ["", "start"]:  # test starting with normal chars
        for endOfString in ["", "end"]:  # test ending with normal chars
            for testItem, testResponse in escapedValues.items():  # test above
                fullTest = startOfString + testItem + endOfString
                fullResponse = basicPackage.format(startOfString + testResponse
                                                   + endOfString)
                actualResponse = package(BT, BT, fullTest)
                if actualResponse != fullResponse:
                    print("Test package failed: {} should be {} not {}"
                          .format(fullTest, fullResponse, actualResponse))
                else:
                    print("Test package passed: {}".format(fullTest))


def test_unpackage():
    BT = "11:11:11:11:11:11"  # default bt address
    for startOfString in ["", "start"]:  # test starting with normal chars
        for endOfString in ["", "end"]:  # test ending with normal chars
            for testItem, testResponse in escapedValues.items():  # test above
                fullTest = startOfString + testItem + endOfString
                actualResponse = unpackage(package(BT, BT, fullTest))
                if (BT, BT, fullTest) != actualResponse:
                    print("Test unpackage failed: {} changed to {}"
                          .format(fullTest, actualResponse))
                else:
                    print("Test unpackage passed: {}".format(fullTest))


test_basic_escaping()
test_package()
test_unpackage()
