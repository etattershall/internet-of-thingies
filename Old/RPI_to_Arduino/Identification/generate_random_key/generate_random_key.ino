/*
 * An example implementation of using the arduino 'Crypto' library to generate
 * a 32 byte key for use with identificaiton.
 *
 * The sketch prints the random key and the time taken to produce the random
 * key for two methods: one which just uses the RNG libraries 'Entropy'
 * (see README) and another which includes stiring in samples from an analogue
 * pin.
 *
 * This depends on the arduino Crypto library
 * https://rweather.github.io/arduinolibs/crypto.html
 */

// Include the random number generator library
#include<RNG.h>

byte key[32];  // Create a byte array to store the key
// Initialize a variable to store 'micros()' at start of generating each key
// so that it can be timed
unsigned long startMicros;
bool analogStir = false; // Flag: stir in analogue read?
// For printing hex without lead 0s, create a string of the chars at each pos
const char hexChars[] = "0123456789ABCDEF";

void setup() {
    // Initialize the random number generator with the application tag
    // "MyApp 1.0" and load the previous seed from EEPROM address 950.
    RNG.begin("MyApp 1.0", 950);

    // This could be used to stir in something like the ethernet address
    // RNG.stir(some array of bytes, sizeof(the array of bytes));
    // A noise source could be added here
    // RNG.addNoiseSource(noise);

    // Start Serial
    Serial.begin(115200);
    Serial.println("Starting Up!");
    delay(50);

    // Un comment this to test printing hex
    // testPrintHexByte();
}

void loop(){
  startMicros = micros();  // Store the start micros for timing

  // Print state
  Serial.print("Generating random numbers starting at: ");
  Serial.print(startMicros);
  Serial.print(analogStir ? " using" : " not using");
  Serial.println(" analog pin");

  //  Wait for randomness
  while(!RNG.available(sizeof(key))) {
    if(analogStir){  // If stiring in from the analog pin
      // Stir in the last bit of analogRead
      RNG.stir((byte)analogRead(A0) & 0x0001, 1);
    }
    RNG.loop();  // Update the RNG
  }

  RNG.rand(key, sizeof(key)); // store the key

  // Print results
  Serial.print("Done. Took: ");
  Serial.print((float)(micros() - startMicros) / 1000000); // print the time taken
  Serial.println("s");
  Serial.print("This is the key: "); // print the key
  for(int i = 0 ; i < sizeof(key) ; i++){
    printHexByte(key[i]);
    Serial.print("|");
  }
  Serial.println("");

  // Toggle analogStir so the opposite happens next
  analogStir = !analogStir;
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


/* tests printHexByte by printing all possible bytes as hex */
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
