# Reset on Serial Established
When the arduino is connected to serial (after the sketch is already running), it resets itself and starts the sketch from the begining. This arduino sketch proves that.
 * **test_reset_serial_established.ino** = the sketch
 * **test_reset_serial_established.py** = a python script to test if the same happens when using python rather than the IDE's serial monitor (it does).

## Disabling this
According to [this article](http://playground.arduino.cc/Main/DisablingAutoResetOnSerialConnection), using a 120ohm resistor between 5v and ground prevents this. I tried with a 110ohm resistor and didn't get it to work on the arduino uno (the article says that it won't work for the uno). **Using a 100uF capacitor worked instead.**

## Note
After the reset, a few characters sent before the reset and/or some random binary (truncated characters?) are send through before the sketch starts up again. More seem to come at higher baud rate.
