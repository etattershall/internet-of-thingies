/*
 * Reads the value of analog pin0 and sends it over
 *     - bluetooth
 *            - pins (13, 12) (RX, TX)
 *            - range [0, 1023]
 *     - normal serial
 *            - range [0, 5] (volts)
 */
#include <SoftwareSerial.h>

// (RX, TX) ARDUINO
// (TXD, RXD) BT Chip
SoftwareSerial BTSerial(13, 12);


void setup() {
  Serial.begin(9600);  // setup serial
  BTSerial.begin(9600);  // setup bluetooth serial - use AT to set this value
}

void loop() {
  int valueFromSensor = analogRead(A0);  // read the input pin
  // The reading is an integer [0, 1023], scale this to a float [0, 5]
  // Not using map funciton because only works with integers
  float voltage = valueFromSensor * 5.0 / 1023.0;
  Serial.println(voltage);
  BTSerial.println(valueFromSensor);
  // Wait while the bluetooth end catches up
  delay(70);
}
