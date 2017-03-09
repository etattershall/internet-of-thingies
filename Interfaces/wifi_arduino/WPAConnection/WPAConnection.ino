#include <WiFi.h>

// Using phone portable hotspot for the moment
char ssid[] = "G4_1236";     //  your network SSID (name)
char pass[] = "wifiTestArduino";    // your network password

int status = WL_IDLE_STATUS;     // the Wifi radio's status

void setup() {
  // initialize serial:
  Serial.begin(9600);

  // attempt to connect using WPA2 encryption:
  Serial.print("Attempting to connect to WPA network: ");
  Serial.println(ssid);
  Serial.print("With password: ");
  Serial.println(pass);

  status = WiFi.begin(ssid, pass);

  // if you're not connected, stop here:
  if ( status != WL_CONNECTED) {
    Serial.println("Couldn't get a wifi connection");
    Serial.println(status);
    while(true);
  }
  // if you are connected, print out info about the connection:
  else {
    Serial.println("Connected to network");
  }
}

void loop() {
  // do nothing
}
