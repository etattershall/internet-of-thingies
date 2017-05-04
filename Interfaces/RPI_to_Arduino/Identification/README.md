# Identification

## Objective
[MUST] How a device identifies itself to the fog/cloud, how it registers and obtains a key, if necessary
- Main purpose is uniqueness of device
- Could also be used to peer-to-peer or peer-to-authority communication if the device id is used as a symmertic key
- Note that this does not identify the user; to identify the user something like PBE (Password Based Encryption) could be used


## Random Numbers

The generate_random_key.ino sketch gives an example implementation.

The [Arduino Crypto](https://rweather.github.io/arduinolibs/crypto.html) library seems to be the established library for cryptography [[1](http://playground.arduino.cc/Main/LibraryList#Cryptography)]. It includes random number generator method from [Entropy](https://sites.google.com/site/astudyofentropy/project-definition/timer-jitter-entropy-sources/entropy-library) which is supposed to be better than sampling an unconnected analogue pin.

### RN Using Arduino Crypto
See the [github page](https://github.com/rweather/arduinolibs) for the library. To install the library, I created a .zip (see Crypto.zip) file from the 'Crypto' folder and loaded it into the Arduino IDE through 'Sketch' > 'Include library' > 'Add .ZIP library'

To add entropy to the RNG:
- `.begin(string, EEPROM address)` takes a string and an address to read from EEPROM (by default it saves every hour)
- `RNG.stir()` can pass noise into the pool
- `RNG.addNoiseSource(noise)` adds a noise class provided by a different library in the same repository eg 'RingOscillatorNoiseSource' or 'TransistorNoiseSource'
- By default, the RNG library uses [Entropy's](https://sites.google.com/site/astudyofentropy/project-definition/timer-jitter-entropy-sources/entropy-library) "Harvest entropy from watchdog jitter" to add noise from differences in timing functions

Without the hardware for `addNoiseSource()`, generate_random_key.ino uses the other methods. Perhaps using the analoge pin as an input to `stir()` is too predictable so the sketch compares the timings of each of the methods.

#### Serial Print Hex Doesn't Work
The key length appears to be different each time... Turns out that the Serial.print(blah, hex) [doesn't print leading zeros](https://forum.arduino.cc/index.php?topic=38107.0)!


## Symmetric Encryption

According to [wikipedia](https://en.wikipedia.org/wiki/Transport_Layer_Security#Algorithm), the standard stream cipher is ChaChaPoly. This is compared with AES - the standard block cipher.

Their [tests](https://rweather.github.io/arduinolibs/crypto.html) are for the arduino uno at 16MHz - we should get the same results.

### My Results for ChaChaPoly
```
State Size ... 221

Test Vectors:
ChaChaPoly #1 ... Passed
ChaChaPoly #2 ... Passed

Performance Tests:
ChaChaPoly #1 SetKey ... 978.01us per operation, 1022.48 per second
ChaChaPoly #1 Encrypt ... 43.00us per byte, 23254.19 bytes per second
ChaChaPoly #1 Decrypt ... 43.00us per byte, 23258.22 bytes per second
ChaChaPoly #1 AddAuthData ... 27.47us per byte, 36396.89 bytes per second
```

### Why not using ChaChaPoly
While there is a python library to implement the ChaCha20-Poly1305 [see here](https://github.com/AntonKueltz/ChaCha20Poly1305/graphs/contributors), I couldn't get it to produce the same output (it sets different key sizes and encrypts the tag before using it). It is also a very small library (13 commits, not on pip, 2 watchers) so may not have been implemented correctly.

### Using only ChaCha
