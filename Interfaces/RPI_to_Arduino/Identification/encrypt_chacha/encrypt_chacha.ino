/*
 * Copyright (C) 2015 Southern Storm Software, Pty Ltd.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a
 * copy of this software and associated documentation files (the "Software"),
 * to deal in the Software without restriction, including without limitation
 * the rights to use, copy, modify, merge, publish, distribute, sublicense,
 * and/or sell copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included
 * in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
 * OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
 * DEALINGS IN THE SOFTWARE.
 */

/*
This example runs tests on the ChaChaPoly implementation with a given key, tag
and iv to encrypt a given plaintext and authdata
*/

#include <Crypto.h>
#include <ChaCha.h>
#include <string.h>
#include <avr/pgmspace.h>

#define MAX_PLAINTEXT_LEN 265
#define KEY_SIZE 32
#define NONCE_SIZE 8
#define COUNTER_SIZE 8


// byte key[] = {  1,   2,   3,   4,   5,   6,   7,   8,
//                 9,  10,  11,  12,  13,  14,  15,  16,
//               201, 202, 203, 204, 205, 206, 207, 208,
//               209, 210, 211, 212, 213, 214, 215, 216};
// byte plaintext[] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
//                     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
//                     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
//                     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
//                     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
//                     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
//                     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
//                     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
// byte iv[] = {101, 102, 103, 104, 105, 106, 107, 108};
// byte counter[] = {109, 110, 111, 112, 113, 114, 115, 116};

byte key[] = {49, 50, 51, 52, 53, 54, 55, 56, 57, 48, 49, 50, 51, 52, 53, 54,
              55, 56, 57, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 48, 49, 50};
byte ciphertext[] = {77, 160, 7, 47, 202, 128, 146, 215, 73, 204, 48, 16, 213,
                     66, 221, 198, 200, 158, 19, 21, 133, 51, 73, 7, 221, 17,
                     153, 242, 1, 147, 79, 14, 149, 204, 162, 198, 107, 169,
                     76, 54, 82, 26, 193, 134, 86, 111, 35, 195, 160, 181};
byte plaintext[] = {84, 104, 105, 115, 32, 105, 115, 32, 97, 32, 116, 101, 115,
                    116, 32, 115, 116, 114, 105, 110, 103, 44, 32, 101, 110,
                    99, 114, 121, 112, 116, 101, 100, 32, 117, 115, 105, 110,
                    103, 32, 67, 104, 97, 67, 104, 97, 32, 112, 111, 108, 121};
byte iv[] = {48, 49, 50, 51, 52, 53, 54, 55};
byte counter[] = {0, 0, 0, 0, 0, 0, 0, 0};


// According to the specification (https://tools.ietf.org/html/rfc7539)
// the counter and the iv are used to set the inital state for each block
// that this is used on.

// cccccccc  cccccccc  cccccccc  cccccccc
// kkkkkkkk  kkkkkkkk  kkkkkkkk  kkkkkkkk
// kkkkkkkk  kkkkkkkk  kkkkkkkk  kkkkkkkk
// bbbbbbbb  nnnnnnnn  nnnnnnnn  nnnnnnnn

// This shows how the inital state is set up for each 64 byte block
// c represents a constant that is always the same for all implementations
// k is the key (32 bytes)
// b is the counter, n is the nonce == iv

// For each new block, the implementation increments the counter so that a
// different seed is used.
// NOTE: This implementation (Arduino) uses any size key (it sets the
//       rest to 0) and truncates at 32 bytes.
// NOTE: This implementation uses either 8 or 12 byte nonces. So
//       if 8 bytes are used then the first 4 bytes are set to 0. The counter
//       can be 4 or 8 bytes and it is written last from 48th byte up to its
//       length. So if counter = 4 and nonce = 8 then there are lots of 0s!



// Define the global ChaCha cipher class to use.
ChaCha chacha;

/*
 * Sets up the ChaCha cipher according to the parameters
 * Params:
 * cipher = pointer to ChaCha cipher
 * k = pointer to a byte array containing the key
 * nonce = pointer to a byte array containing the nonce
 * count = pointer to a byte array containing the counter
 * note these should all be of sizes defined in the SIZE macros
 */
void setup_chacha(ChaCha *cipher, byte *k, byte *nonce, byte *count){
  // Set the key, IV and counter
  cipher->clear();
  cipher->setKey(k, KEY_SIZE);
  cipher->setIV(nonce, NONCE_SIZE);
  cipher->setCounter(count, COUNTER_SIZE);
}


// cipher->encrypt(outBuffer, plaintext, sizeof(plaintext));
// cipher->decrypt(outBuffer, ciphertext, sizeOfCipher);

void setup()
{
    Serial.begin(9600);

    // Print the initial state
    Serial.println("TEST ENCRYPTION:");
    Serial.println("Hardcoded Key:");
    printArray(key, sizeof(key)); Serial.println();
    Serial.println();
    Serial.println("Hardcoded Plaintext: ");
    printArray(plaintext, sizeof(plaintext)); Serial.println();
    Serial.println();
    Serial.println("Hardcoded Ciphertext: ");
    printArray(ciphertext, sizeof(ciphertext)); Serial.println();
    Serial.println();
    Serial.println("Hardcoded Counter: ");
    printArray(counter, sizeof(counter)); Serial.println();
    Serial.println();
    Serial.println("Hardcoded IV: ");
    printArray(iv, sizeof(iv)); Serial.println();
    Serial.println();

    // Encrypt the plaintext into a buffer
    setup_chacha(&chacha, key, iv, counter);
    byte outBuffer[MAX_PLAINTEXT_LEN];
    chacha.encrypt(outBuffer, plaintext, sizeof(plaintext));
    Serial.println("Encrypted Data: ");
    // Print sizeof plaintext (as encryptedOut is of length MAX_PLAINTEXT_LEN
    // rather than length of the plaintext - there are probably 0s at the end!)
    printArray(outBuffer, sizeof(plaintext)); Serial.println();
    Serial.println();

    memset(outBuffer, 0, MAX_PLAINTEXT_LEN); // Reset the buffer

    // Decrypt the cipher into a the same buffer
    setup_chacha(&chacha, key, iv, counter);
    chacha.encrypt(outBuffer, ciphertext, sizeof(plaintext));
    Serial.println("Decrypted Data: ");
    printArray(outBuffer, sizeof(plaintext)); Serial.println();
    Serial.println();
}

void loop()
{
}


// From here onward, there is just code to print clean hex characters

// Define an array mapping hex character to index
const char hexChars[] = "0123456789ABCDEF";

/* takes a pointer to an array and prints it as hex */
void printArray(byte pointerToArray[], int sizeOfArray){
  for(int i = 0 ; i < sizeOfArray ; i++){
    Serial.print("0x");
    printHexByte(pointerToArray[i]);
    if(i + 1 < sizeOfArray){
      Serial.print(", ");
    }
  }
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
