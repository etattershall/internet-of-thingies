/*
 * Program to test the toy message protocol with escaping piduino (10-04-2017)
 * 
 * Connections are made by the Pi, not the Arduino. The Arduino simply listens for
 * incoming connections
 *
 */

// If SoftwareSerial is not included, we can't use the normal PC serial terminal and
// also use bluetooth.
#include <SoftwareSerial.h>

const char PACKET_START = 60;   /* <  */
const char PACKET_DIVIDE = 124; /* |  */
const char PACKET_END = 62;     /* >  */
const char ESCAPE = 92;         /* \  */
const char TO_ESCAPE[] = {PACKET_START, PACKET_DIVIDE, PACKET_END, ESCAPE};

const String device_name = "H-C-2010-06-01";
const String device_address = "98:D3:32:10:82:D4";

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
// Is the current character recieved escaped? Depends on the last character
bool charIsEscaped = false;
// Are we after a PACKET_START but before a PACKET_END
bool insidePacket = false;


//Connect the Bluetooth module
SoftwareSerial bluetooth(rxpin, txpin);

void setup() {
  //Initialize Serial for debugging purposes
  Serial.begin(9600);
  //Initialize the bluetooth
  bluetooth.begin(38400);
  Serial.print("Setting up with: ");
  Serial.print(PACKET_START);
  Serial.print(",");
  Serial.print(PACKET_DIVIDE);
  Serial.print(",");
  Serial.print(PACKET_END);
  Serial.print(",");
  Serial.println(ESCAPE);

}

void loop() {
  if (bluetooth.available())
  {
    // Receive information from Pi
    int inbyte = bluetooth.read();
    char inchar = char(inbyte);
    // Block below handles receiving messages. Messages come one byte at a time,
    // in ascii character codes
    // Check if the new byte is the start of a message
    if (inchar == PACKET_START && ! charIsEscaped) {
      // Empty out the message buffer
      incoming_packaged_message = "";
      insidePacket = true;
    }

    else if (inchar == PACKET_END && ! charIsEscaped){
      insidePacket = false;
      // Process the completed message
      Serial.print("Completed message:");
      Serial.println(incoming_packaged_message);
      Message incoming_message = unpackage_message(incoming_packaged_message);
      // Print the message content to serial
      Serial.println(incoming_message.source);
      Serial.println(incoming_message.destination);
      Serial.println(incoming_message.content);

      // Create a message to send back
      Message outgoing_message = {
        device_address, // source
        incoming_message.source, // destination
        incoming_message.content
      };


      
      bluetooth.println(package_message(outgoing_message));
    }

    else if (insidePacket){
      // Append to the end of the buffer
      incoming_packaged_message.concat(inchar);
    }
    // Set up charIsEscaped flag for the next char
    charIsEscaped = inchar == ESCAPE && ! charIsEscaped;
  }
}

String package_message(Message message){
  // Takes a Message object and packages it, ready to send via bluetooth
  String packaged_message = "<" + escape(message.source) + "|" + 
                                  escape(message.destination) + "|" + 
                                  escape(message.content) + ">";
  Serial.print("Sending:");
  Serial.println(packaged_message);
  return packaged_message;
}

Message unpackage_message(String packaged_message){
  // Takes a packaged message string, and unpackages it into a Message object
  // Removes any escaping
  // packaged message string should already have PACKET_START and PACKET_END removed
  String packetData[3];  // A list of items of packet data
  int currentPacketDataIndex = 0;  // The current item to append to
  // Flag if the current char is escaped (different to global charIsEscaped)
  bool thisCharIsEscaped = false;
  // Remove the packet start and packet ends
  for(int i = 0 ; i < packaged_message.length() ; i ++){  // go through each character
    // If this is splitting sections of the packet, start a new section
    if(packaged_message[i] == PACKET_DIVIDE && ! thisCharIsEscaped){
      currentPacketDataIndex ++;
      continue;  // don't do anything else with this character
    }

    // Add this character to the current section of the packet
    if ((packaged_message[i] == ESCAPE && thisCharIsEscaped) | packaged_message[i] != ESCAPE){
      packetData[currentPacketDataIndex] += packaged_message[i];
    }

    // Set the escape flag for the next character
    thisCharIsEscaped = packaged_message[i] == ESCAPE && ! thisCharIsEscaped;

  }
  Message message;
  message.source = packetData[0];
  message.destination = packetData[1];
  message.content = packetData[2];
  return message;
}

bool is_escapable_character(char input){
  // Equivalent of 'input in TO_ESCAPE' in python
  for(int i = 0 ; i < sizeof(TO_ESCAPE); i ++){
    if(TO_ESCAPE[i] == input){
      return true;
    }
  }
  return false;
}

String escape(String text){
  int currentIndex = 0;
  while(currentIndex < text.length()){
    // Step through one character at a time
    if(is_escapable_character(text[currentIndex])){
      // If this char needs escaping, add an escape before it.
      // text:            "aad\asdf"
      // current index:       ^
      // new text:        "add\\asdf"
      // updated index:        ^
      text = text.substring(0, currentIndex) + ESCAPE +
             text.substring(currentIndex);
      currentIndex ++;
    }
    currentIndex ++;
  }
  return text;
}
