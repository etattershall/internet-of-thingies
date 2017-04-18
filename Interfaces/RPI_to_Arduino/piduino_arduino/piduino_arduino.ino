/*
 * Program to test the toy message protocol piduino (05-04-2017) 
 * 
 * Each Arduino has a connected HC-05 bluetooth chip, a pushbutton and an LED. 
 * 
 * Connections are made by the Pi, not the Arduino. The Arduino simply listens for 
 * incoming connections
 * 
 * If the Arduino receives a message 'Change state', it changesa the state of its
 * LED
 * 
 * The Arduino can send messages of its own when its button is pressed. 
 * 
 * To implement later:
 * Responsive AT mode. Can AT mode even be entered while connected (probably not- 
 * will have to send a BRB message)
 * 
 * Authentication. When Pi connects for the first time, both have to authenticate with
 * pgp - each device has a private key of their own, and the public key of the pinnacle of
 * the pyramid (the pi in this case)
 */

// If SoftwareSerial is not included, we can't use the normal PC serial terminal and
// also use bluetooth.
#include <SoftwareSerial.h>

const String device_name = "SCD_ARDUINO_2";
const String device_address = "98:D3:32:10:8E:5D";

//Define the pins used for receiving and transmitting information via Bluetooth
const int rxpin = 10;
const int txpin = 11;

// Create a data structure to hold message objects in
struct Message {
  String source;
  String destination;
  String content;  
};


// Initialise the holder for messages 
String incoming_packaged_message = "";

//Connect the Bluetooth module
SoftwareSerial bluetooth(rxpin, txpin);

void setup() {
  // Initialize Serial for debugging purposes
  Serial.begin(9600);
  // Initialize the bluetooth using the default baud rate
  bluetooth.begin(38400);
}

void loop() {
  if (bluetooth.available())
  {
      // Receive information from Pi
      int inbyte = bluetooth.read();

      // Block below handles receiving messages. Messages come one byte at a time,
      // in ascii character codes
      // Check if the new byte is the start of a message

      if (char(inbyte) == '<') {
        // Empty out the message buffer
        incoming_packaged_message = "";
      }
      else if (char(inbyte) == '>'){
        // Process the completed message
        Message incoming_message = unpackage_message(incoming_packaged_message);
        // Print the message content to serial
        Serial.println(incoming_message.content);
        // Create a message to send back
        Message outgoing_message = {
          device_address, // source
          incoming_message.source, // destination
          "Confirm received"
        };
        delay(100);
        bluetooth.println(package_message(outgoing_message));
      }
      else {
        // Append to the end of the buffer
        incoming_packaged_message.concat(char(inbyte));
      }     
  }
}

String getSubString(String data, char separator, int index)
{
  // Found at http://arduino.stackexchange.com/questions/1013/how-do-i-split-an-incoming-string
  // Takes a string and splits it
  // Usage getSubString(mystring, '|', 0)
  int found = 0;
  int strIndex[] = { 0, -1 };
  int maxIndex = data.length() - 1;

  for (int i = 0; i <= maxIndex && found <= index; i++) {
      if (data.charAt(i) == separator || i == maxIndex) {
          found++;
          strIndex[0] = strIndex[1] + 1;
          strIndex[1] = (i == maxIndex) ? i+1 : i;
      }
  }
  return found > index ? data.substring(strIndex[0], strIndex[1]) : "";
}

String package_message(Message message){
  // Takes a Message object and packages it, ready to send via bluetooth
  String packaged_message = "<" + message.source + "|" + message.destination + "|" + \
                            message.content + ">";
  return packaged_message;
}

Message unpackage_message(String packaged_message){
  // Takes a packaged message string, and unpackages it into a Message object
  Message message;
  message.source = getSubString(packaged_message, '|', 0);
  message.destination = getSubString(packaged_message, '|', 1);
  message.content = getSubString(packaged_message, '|', 2);
  return message;
}


