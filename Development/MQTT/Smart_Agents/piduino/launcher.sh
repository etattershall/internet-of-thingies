#!/bin/sh
# launcher.sh
# navigate to home directory, then to piduino directory, then execute script

cd /
cd home/pi/piduino
sudo python3 serial_relay.py
cd /


