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
**Note: To make this software run, you need to use a much earlier version of the Arduino IDE (1.02 or earlier) because the firmware on the board itself has not been updated to be compatible with the new IDE. I am looking into updating firmware.**
