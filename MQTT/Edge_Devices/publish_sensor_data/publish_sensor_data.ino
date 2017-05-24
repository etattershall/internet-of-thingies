/*
 * SIMPLE SERIAL DEVICE
 * -------------
 * 
 * Extremely simple script that reads a variety of sensors and publishes information on 
 * their values to a smart agent connected by serial. It can also receive instructions
 * to control its outputs
 */

#include <SoftwareSerial.h>
#include <ArduinoJson.h>

// Outputs
const int GREEN_LED = 7;
const int RED_LED = 8;

// Inputs
const int LDR = 0;
const int THERM = 1;

// Create a string to store incoming data
String data = "";

// Store a value for last publish time
long previousMillis = 0; 
long interval = 5000; 

void setup() {
  Serial.begin(9600);

  // Configure the digital pins
  pinMode(GREEN_LED, OUTPUT);
  pinMode(RED_LED, OUTPUT);
}

void loop() {
  StaticJsonBuffer<500> jsonBuffer;
  
  // Check if there is data to read from the serial
  if (Serial.available()) {
    int inbyte = Serial.read();
    data += char(inbyte);
  }
  else {
    // Attempt to parse the incoming data
    JsonObject& incoming_message = jsonBuffer.parseObject(data);
    if (incoming_message.success()) {
      // Clear out the buffer
      data = "";
      // Deal with the message
      if (incoming_message["topic"]=="GREEN_LED" && incoming_message["payload"]=="HIGH") {
        digitalWrite(GREEN_LED, HIGH);
      }
      else if (incoming_message["topic"]=="GREEN_LED" && incoming_message["payload"]=="LOW") {
        digitalWrite(GREEN_LED, LOW);
      }
      else if (incoming_message["topic"]=="RED_LED" && incoming_message["payload"]=="HIGH") {
        digitalWrite(RED_LED, HIGH);
      }
      else if (incoming_message["topic"]=="RED_LED" && incoming_message["payload"]=="LOW") {
        digitalWrite(RED_LED, LOW);
      }    
    }
  }
  

  // Whether or not we have a message to read, we still want to share data about our sensors
  unsigned long currentMillis = millis();
  if(currentMillis - previousMillis > interval) {
    previousMillis = currentMillis; 
    int LDR_state = analogRead(LDR);
    JsonObject& LDR_message = jsonBuffer.createObject();
    LDR_message["type"] = "pub";
    LDR_message["topic"] = "LDR";
    LDR_message["payload"] = LDR_state;
    LDR_message.printTo(Serial);
  
    int THERM_state = analogRead(THERM);
    JsonObject& THERM_message = jsonBuffer.createObject();
    THERM_message["type"] = "pub";
    THERM_message["topic"] = "THERM";
    THERM_message["payload"] = THERM_state;
    THERM_message.printTo(Serial);
  }
}
