#include<RNG.h>
byte key[32];
unsigned long startMicros;
bool analogStir = false; // a flag: stir in analogue read?
const char hexChars[] = "0123456789ABCDEF";  // for printing hex

void setup() {
    // Initialize the random number generator with the application tag
    // "MyApp 1.0" and load the previous seed from EEPROM address 950.
    RNG.begin("MyApp 1.0", 950);


    // Stir in the Ethernet MAC address.
    //RNG.stir(some array of bytes, sizeof(the array of bytes));
    // Add the noise source to the list of sources known to RNG.
    //RNG.addNoiseSource(noise);

    Serial.begin(115200);
    Serial.println("Starting Up!");
    delay(50);
    // testPrintHexByte();
}




void loop(){
  startMicros = micros();
  Serial.print("Generating random numbers starting at: ");
  Serial.print(startMicros);
  Serial.print(analogStir ? " using" : " not using");
  Serial.println(" analog pin");
  while(!RNG.available(sizeof(key))) { //  Wait for randomness
    if(analogStir){
      RNG.stir((byte)analogRead(A0) & 0x0001, 1); // Stir in the last bit of analogRead
    }
    RNG.loop();
  }
  RNG.rand(key, sizeof(key)); // store the key
  Serial.print("Done. Took: ");
  Serial.print((float)(micros() - startMicros) / 1000000); // print the time taken
  Serial.println("s");
  Serial.print("This is the key: "); // print the key
  for(int i = 0 ; i < sizeof(key) ; i++){
    printHexByte(key[i]);
    Serial.print("|");
  }
  Serial.println("");
  analogStir = !analogStir; // toggle analogStir so the opposite happens next
}

/* prints a byte to serial in hex, *DOES* print leading 0s*/
void printHexByte(byte toPrint){
  // Do it this way to avoid print(,HEX) which removes 0 padding
  byte HSN = toPrint >> 4;  // high nibble
  byte LSN = toPrint & 0x0f;  // low nibble
  // print hex
  Serial.print(hexChars[HSN]);
  Serial.print(hexChars[LSN]);
}


/* tests printHexByte */
void testPrintHexByte(){
  Serial.println(" ---- Testing Print Hex ---- ");
  byte i = 0;
  do {
    printHexByte(i);
    i ++;
    if(i % 16 == 0){
      Serial.println();
    }
  } while (i != 0);
}
