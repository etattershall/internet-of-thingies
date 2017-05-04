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

byte key[] = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16,
              201, 202, 203, 204, 205, 206, 207, 208, 209, 210,
              211, 212, 213, 214, 215, 216};
byte plaintext[] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
// byte ciphertext  = {0x2A, 0x7E, 0x73, 0xC2, 0x2A, 0xE5, 0xCF, 0x4E,
//                     0x21, 0x75, 0xB1, 0x26, 0x38, 0x3F, 0x60, 0x84,
//                     0x11, 0x25, 0xFC, 0xAD, 0xFD, 0x16, 0x54, 0xF2,
//                     0xD7, 0x8C, 0x5D, 0x49, 0x8D, 0x96, 0xBE, 0x15,
//                     0xC9, 0x00, 0x12, 0x09, 0x14, 0x43, 0x2D, 0x6D,
//                     0x64, 0x33, 0x88, 0xA6, 0x16, 0x39, 0x86, 0xFD,
//                     0xD8, 0x85, 0x4D, 0x76, 0x42, 0xEC, 0x0A, 0x0C,
//                     0x8A, 0xF2, 0x99, 0x2E, 0x54, 0xAE, 0xB4, 0xD9};
byte iv[] = {101, 102, 103, 104, 105, 106, 107, 108};
byte counter[] = {109, 110, 111, 112, 113, 114, 115, 116};

ChaCha chacha;

const char hexChars[] = "0123456789ABCDEF";

/*
 * Takes a pointer to the ChaChaPoly cipher, a pointer to outBuffer and a
 * pointer to the t buffer. It writes the encrypted data to the outBuffer
 * and the computed tag to the t buffer.
 */
void test_encrypt(ChaCha *cipher, byte *outBuffer, uint8_t *t){
  // Set the key, IV and counter
  cipher->clear();
  cipher->setKey(key, sizeof(key));
  cipher->setIV(iv, sizeof(iv));
  cipher->setCounter(counter, sizeof(counter));


  // Write the encrypted data to the buffer
  cipher->encrypt(outBuffer, plaintext, sizeof(plaintext));
}

void setup()
{
    Serial.begin(9600);

    // Initalise a buffer to store to encrypted data
    byte encryptedOut[MAX_PLAINTEXT_LEN];
    // Initialize a buffer to store the computed tag
    uint8_t tag[16];

    // Encrypt the data into the buffer
    test_encrypt(&chacha, encryptedOut, tag);

    Serial.println("TEST ENCRYPTION:");

    Serial.println("In Key:");
    printArray(key, sizeof(key)); Serial.println();
    Serial.println();

    Serial.println("In Plaintext: ");
    printArray(plaintext, sizeof(plaintext)); Serial.println();
    Serial.println();

    Serial.println("In Counter: ");
    printArray(counter, sizeof(counter)); Serial.println();
    Serial.println();

    Serial.println("In IV: ");
    printArray(iv, sizeof(iv)); Serial.println();
    Serial.println();

    Serial.println("Encrypted Data: ");
    printArray(encryptedOut, sizeof(plaintext)); Serial.println();
    Serial.println();
}

void loop()
{
}


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
