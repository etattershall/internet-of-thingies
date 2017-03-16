# Wifi Shield For Arduino
See the [tutorial](https://www.arduino.cc/en/Guide/ArduinoWiFiShield).

Pins that are used:

* Digital: 3, 4, 9, 10, 11, 12, 13
* Analog: None

[source](http://playground.arduino.cc/Main/ShieldPinUsage).
## ScanForNetworks
An arduino sketch to print the MAC address of the wifi shield and then print all reachable networks.

Only slightly adapted from the tutorial -> prints the names of the encryption types rather than a byte.
## WPAConnection
Connect to a given network by supplying an SSID and a password (copied directly from the tutorial)

## ServeWebsite
Connects to chosen wifi network and serves a website.

To run this, you need to update the firmware on the Wifi shield (for some reason they ship with ancient firmware that requires Arduino IDE 1.02 to properly use). Use the instructions here: http://www.instructables.com/id/How-to-Update-Your-Arduino-Wi-Fi-Shield-not-101/ and **not** those on the official Arduino website (almost completely useless). For the device manager step, you'll need to log in as admin, or open devmgmt.msc from an admin command prompt. Also, the 'AT32UC3A' lives under 'libusb-win32 devices' after you've updated the driver software, so don't go looking for 'Other devices'!
