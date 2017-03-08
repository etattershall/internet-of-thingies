/*
 * Recieves values from the 'AnalogRead' arduino and lights one of 3 LEDs
 * depending on the size.
 *
 * Modified from https://www.arduino.cc/en/Tutorial/StringToFloatExample
 */

#include <SoftwareSerial.h>

// (RX, TX) ARDUINO
// (TXD, RXD) BT Chip
SoftwareSerial BTSerial(13, 12);

String inString = "";  // string to hold input, as it is read char by char

// A constant array of pins for the LEDs. The first ones are on for lower
// values, the last ones are on for higher values.
const int ledPins[] = {9, 8, 7};
// Store the length of the array above
const int numberOfLedPins = sizeof(ledPins) / sizeof(int);

void setup() {
  // initialize serial for computer then for bluetooth
  Serial.begin(9600);
  BTSerial.begin(9600);  // configured on the AT-command line
  for(int i = 0; i < numberOfLedPins; i ++){
    pinMode(ledPins[i], OUTPUT);  // set each pin to output
  }
}

void loop() {
  // This loop gets each character and builds up a string 'inString' of
  // digits recieved. When a new line is recieved, it converts the string into
  // an integer and empties the stored string for the next line.
  while (BTSerial.available() > 0) {  // while there is bluetooth data
    int inChar = BTSerial.read();  // store the next character as its int value
    if (isDigit(inChar)) {
      // convert the incoming byte to a char
      // and add it to the string for this line so far
      inString += (char)inChar;
    }
    // If there's a newline then that is the end of this number
    if (inChar == '\n') {
      int valueFromSensor = inString.toInt();  // convert the line into an int
      float voltage = valueFromSensor * 5.0 / 1023.0;  // calculate voltage
      Serial.print("Voltage is: ");
      Serial.print(voltage);
      // calculate which of the LEDs should be lit up
      // divide by 1024 when 1023 is the max sensor value to ensure round down
      int ledIndexToLight = valueFromSensor * numberOfLedPins / 1024;
      Serial.print(" light led index: ");
      Serial.println(ledIndexToLight);
      // turn one LED on and the rest off.
      for(int i = 0 ; i < numberOfLedPins ; i ++){
        if(i == ledIndexToLight){
          digitalWrite(ledPins[i], HIGH);
        } else {
          digitalWrite(ledPins[i], LOW);
        }
      }
      // clear the string for the future
      inString = "";
    }
  }
}
