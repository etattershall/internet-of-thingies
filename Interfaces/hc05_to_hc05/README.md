# Connecting HC05 to HC05
Code to interface between two HC05s. 
## AnalogueRead
AnalogueRead.ino - Arduino code to read the value of analog pin0 and sends it over bluetooth.
plotSerialDataMPL.py - A script to plot a live graph of the data
## SerialRelayBluetoothWithLEDs
SerialRelayBluetoothWithLEDs.ino - Arduino code to recieve the data from AnalogueRead
## Setting up HC05 in AT mode:
To set the two HC05s up, followed [this tutorial](http://howtomechatronics.com/tutorials/arduino/how-to-configure-pair-two-hc-05-bluetooth-module-master-slave-commands/)

Use the HC05 AT mode script to interface over USB serial from arduino
### Slave
1. Restore default settings `AT+ORGL` -> `OK`
2. Confirm slave mode `AT+ROLE?` -> `+ROLE=0`
3. Note down BT address `AT+ADDR?` -> `abcd:ef:ghijkl`

### Master
1. Restore default settings `AT+ORGL` -> `OK`
2. Set master mode `AT+ROLE=1` -> `OK`
4. Set connect to fixed address `AT+CMODE=0` -> `OK`
5. Give slave BT address to bind with -> `AT+BIND=abcd,ef,ghijkl` (from slave - replace colons with commas)


