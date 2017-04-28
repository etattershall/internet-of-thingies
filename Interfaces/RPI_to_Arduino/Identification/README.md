# Identification

## Objective
[MUST] How a device identifies itself to the fog/cloud, how it registers and obtains a key, if necessary
- Main purpose is uniqueness of device
- Could also be used to peer-to-peer or peer-to-authority communication if the device id is used as a symmertic key
- Note that this does not identify the user; to identify the user something like PBE (Password Based Encryption) could be used


## Random Numbers

The [Arduino Crypto](https://rweather.github.io/arduinolibs/crypto.html) library seems to be the established library for cryptography [[1](http://playground.arduino.cc/Main/LibraryList#Cryptography)]. It includes a method from [Entropy](https://sites.google.com/site/astudyofentropy/project-definition/timer-jitter-entropy-sources/entropy-library) which is supposed to be better than sampling an unconnected analogue pin.

### Arduino Crypto
See the [github page](https://github.com/rweather/arduinolibs) for the library. To install the library, I created a .zip (see Crypto.zip) file from the 'Crypto' folder and loaded it into the Arduino IDE through 'Sketch' > 'Include library' > 'Add .ZIP library'

To add entropy to the RNG:
- `.begin(string, EEPROM address)` takes a string and an address to read from EEPROM (by default it saves every hour)
- `RNG.stir()` can pass noise into the pool
- `RNG.addNoiseSource(noise)` adds a noise class provided by a different library in the same repository eg 'RingOscillatorNoiseSource' or 'TransistorNoiseSource'
- By default, the RNG library uses [Entropy's](https://sites.google.com/site/astudyofentropy/project-definition/timer-jitter-entropy-sources/entropy-library) "Harvest entropy from watchdog jitter" to add noise from differences in timing functions

Without the hardware for `addNoiseSource()`, crypto_test.ino uses the other methods. Perhaps using the analoge pin as an input to `stir()` is too predictable so the sketch compares the timings of each of the methods.

#### Note
The key length appears to be different each time... Turns out that the Serial.print(blah, hex) [doesn't print leading zeros](https://forum.arduino.cc/index.php?topic=38107.0)!
