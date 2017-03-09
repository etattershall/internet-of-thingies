//Include the module so we don't
//have to use the default Serial
//so the Arduino can be plugged in
//to a computer and still use bluetooth
#include <SoftwareSerial.h>

//Define the pins used for receiving
//and transmitting information via Bluetooth
const int rxpin = 10;
const int txpin = 11;

//Variable to store input value

//Connect the Bluetooth module
SoftwareSerial bluetooth(rxpin, txpin);


void setup()
{
  //Initialize Serial for debugging purposes
  Serial.begin(9600);
  //Initialize the bluetooth
  bluetooth.begin(9600);
}

void loop()
{
  // Get the data from the LDR 
  int sensorValue = analogRead(A0);
  Serial.println(sensorValue);
  
  bluetooth.println('<'+String(sensorValue)+'>');
  //Wait ten milliseconds to decrease unnecessary hardware strain
  delay(100);
  
}
