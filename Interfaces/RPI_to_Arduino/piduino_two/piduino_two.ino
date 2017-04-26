/*
 * TEST MULTIPLE ARDUINO SYSTEM
 * ----------------------------
 * 
 * Function:
 * - Arduino sends the message "Button Pressed" when its button is pressed
 * 
 * To implement
 * - Arduino recieves messages and lights its LED under given conditions
 * - Arduino broadcasts to all its friends (i.e. the other Arduino)
 */

// If SoftwareSerial is not included, we can't use the normal PC serial terminal and
// also use bluetooth.
#include <SoftwareSerial.h>

const String device_name = "SCD_ARDUINO_2";
const String device_address = "98:D3:32:10:8E:5D";
const String friend_address = "98:D3:32:30:87:EE";

//Define the pins used for receiving and transmitting information via Bluetooth
const int rxpin = 10;
const int txpin = 11;

// Define the pins used for inputs and outputs
const int button = 2;
const int led = 7;

// Create a data structure to hold message objects in
struct Message {
  String source;
  String destination;
  String content;  
};

// Record the current button state
// If the button goes from 0 - 1, send a message to the other Arduino
int old_button_state = 0;
int button_state = 0;

// Record LED state 
int led_state = 0;

// Initialise a message string
String incoming_packaged_message = "";

//Connect the Bluetooth module
SoftwareSerial bluetooth(rxpin, txpin);

void setup() {
  // Set input and output pins
  pinMode(led, OUTPUT);
  pinMode(button, INPUT);
  
  // Initialize Serial for debugging purposes
  Serial.begin(9600);
  // Initialize the bluetooth using the default baud rate
  bluetooth.begin(38400);
}

void loop() {
  if (led_state == 0){
    digitalWrite(led, LOW);
  }
  else {
    digitalWrite(led, HIGH);
  }
      
  button_state = digitalRead(button);
  
  // If the button has gone from low to high, send a message
  if ((old_button_state == 0) && (button_state == 1)){
    Message outgoing_message = {
      device_address, // source
      friend_address, // destination
      "Button Pressed"
    };
    Serial.println(package_message(outgoing_message));
    bluetooth.println(package_message(outgoing_message));
  }  
  old_button_state = button_state;

  // Receive any available messages
  if (bluetooth.available())
  {
    // Receive information from hub
    int inbyte = bluetooth.read();

    // Check to see if it is the start of a packet
    if (char(inbyte) == '<') {
      // Empty out the message buffer
      incoming_packaged_message = "";
    }
    // If the incoming byte marks the end of a packet, switch on LED.
    else if (char(inbyte) == '>'){
      // Process the completed message
      Message incoming_message = unpackage_message(incoming_packaged_message);
      // Print the message content to serial
      Serial.println(incoming_message.content);
      if (incoming_message.content == "Button Pressed"){
        // Change the state of the LED
        Serial.println("Changing state of LED");
        if (led_state == 0){
          led_state = 1;
        }
        else {
          led_state = 0;
        }
      }
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
  String packaged_message = "<" + message.source + "#" + message.destination + "#" + \
                            message.content + ">";
  return packaged_message;
}

Message unpackage_message(String packaged_message){
  // Takes a packaged message string, and unpackages it into a Message object
  Message message;
  message.source = getSubString(packaged_message, '#', 0);
  message.destination = getSubString(packaged_message, '#', 1);
  message.content = getSubString(packaged_message, '#', 2);
  return message;
}


