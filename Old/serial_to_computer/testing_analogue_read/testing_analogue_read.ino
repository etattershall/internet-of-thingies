/*
 * Reads the value of analog pin0 and sends it over normal serial
 *    - range [0, 1023] (divide by 5 to get volts)
 * also sends the time (in microseconds) since the previous reading
 */

// Use an unsigned long because 'micros()' returns an unsigned long so
// the difference will always wrap around
// eg 5 - 4294967295 (max for unsigned long) = 6

// microseconds since the begining of the sketch of the last reading
unsigned long lastReading;

void setup() {
  Serial.begin(115200);  // setup serial
  lastReading = 0;
  Serial.println("Starting up!");
}

void loop() {
  int valueFromSensor = analogRead(A0);  // read the input pin
  unsigned long timeNow = micros();
  Serial.print(timeNow - lastReading); // print the difference
  Serial.print(","); // a separator
  Serial.println(valueFromSensor); // print the reading
  lastReading = timeNow;  // set lastReading time
}
