
#include <SoftwareSerial.h>
#include <ArduinoJson.h>

// Define the pins used for inputs and outputs
const int LED = 7;
const int SENSOR = 0;

// Set the name of the device
const String DEVICE = "Arduino 1";

// Create an empty string to store incoming data in
String data = "";

// Store a value for last publish time
long previousMillis = 0; 
long interval = 5000; 

void setup() {
  Serial.begin(9600);
  pinMode(LED, OUTPUT);
}

void loop() {
  // Set the json buffer
  StaticJsonBuffer<500> jsonBuffer;

  // If there is data available to read from the serial port, append it to our data string
  if (Serial.available()) 
  {
    int inbyte = Serial.read();
    data = data + char(inbyte);
    
  }
  // If there is no new data available...
  else {
    // But we have some stored..
    if (data.length() > 0){
      // Attempt to parse it
      JsonObject& incoming_message = jsonBuffer.parseObject(data);
      // If parsing was successful...
      if (incoming_message.success()) {
        // Do what the message says!
        if (incoming_message["topic"] == "led" && incoming_message["payload"] == "HIGH"){
          digitalWrite(LED, HIGH);
        }
        else if (incoming_message["topic"] == "led" && incoming_message["payload"] == "LOW"){
          digitalWrite(LED, LOW);
        }

        // If the message was a success, we no longer need the message data.
        // clear it out ready for the next message
        data = "";
      }
    }

    else {
    unsigned long currentMillis = millis();
    if(currentMillis - previousMillis > interval) {
      previousMillis = currentMillis;
      
      // Send data about our sensor
      int sensor_state = analogRead(SENSOR);
      JsonObject& outgoing_message = jsonBuffer.createObject();
      outgoing_message["source"] = DEVICE;
      outgoing_message["type"] = "pub";
      outgoing_message["topic"] = "LDR";
      outgoing_message["payload"] = sensor_state;
      outgoing_message.printTo(Serial);
    }
    }
  }
  delay(10);
}

