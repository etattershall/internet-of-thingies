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
#include <ChaChaPoly.h>
#include <string.h>
#include <avr/pgmspace.h>

#define MAX_PLAINTEXT_LEN 265

byte key[] = {0x80, 0x81, 0x82, 0x83, 0x84, 0x85, 0x86, 0x87,
            0x88, 0x89, 0x8a, 0x8b, 0x8c, 0x8d, 0x8e, 0x8f,
            0x90, 0x91, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97,
            0x98, 0x99, 0x9a, 0x9b, 0x9c, 0x9d, 0x9e, 0x9f};
byte plaintext[] = {0x4c, 0x61, 0x64, 0x69, 0x65, 0x73, 0x20, 0x61,
                  0x6e, 0x64, 0x20, 0x47, 0x65, 0x6e, 0x74, 0x6c,
                  0x65, 0x6d, 0x65, 0x6e, 0x20, 0x6f, 0x66, 0x20,
                  0x74, 0x68, 0x65, 0x20, 0x63, 0x6c, 0x61, 0x73,
                  0x73, 0x20, 0x6f, 0x66, 0x20, 0x27, 0x39, 0x39,
                  0x3a, 0x20, 0x49, 0x66, 0x20, 0x49, 0x20, 0x63,
                  0x6f, 0x75, 0x6c, 0x64, 0x20, 0x6f, 0x66, 0x66,
                  0x65, 0x72, 0x20, 0x79, 0x6f, 0x75, 0x20, 0x6f,
                  0x6e, 0x6c, 0x79, 0x20, 0x6f, 0x6e, 0x65, 0x20,
                  0x74, 0x69, 0x70, 0x20, 0x66, 0x6f, 0x72, 0x20,
                  0x74, 0x68, 0x65, 0x20, 0x66, 0x75, 0x74, 0x75,
                  0x72, 0x65, 0x2c, 0x20, 0x73, 0x75, 0x6e, 0x73,
                  0x63, 0x72, 0x65, 0x65, 0x6e, 0x20, 0x77, 0x6f,
                  0x75, 0x6c, 0x64, 0x20, 0x62, 0x65, 0x20, 0x69,
                  0x74, 0x2e};
// ciphertext  = {0xd3, 0x1a, 0x8d, 0x34, 0x64, 0x8e, 0x60, 0xdb,
//                0x7b, 0x86, 0xaf, 0xbc, 0x53, 0xef, 0x7e, 0xc2,
//                0xa4, 0xad, 0xed, 0x51, 0x29, 0x6e, 0x08, 0xfe,
//                0xa9, 0xe2, 0xb5, 0xa7, 0x36, 0xee, 0x62, 0xd6,
//                0x3d, 0xbe, 0xa4, 0x5e, 0x8c, 0xa9, 0x67, 0x12,
//                0x82, 0xfa, 0xfb, 0x69, 0xda, 0x92, 0x72, 0x8b,
//                0x1a, 0x71, 0xde, 0x0a, 0x9e, 0x06, 0x0b, 0x29,
//                0x05, 0xd6, 0xa5, 0xb6, 0x7e, 0xcd, 0x3b, 0x36,
//                0x92, 0xdd, 0xbd, 0x7f, 0x2d, 0x77, 0x8b, 0x8c,
//                0x98, 0x03, 0xae, 0xe3, 0x28, 0x09, 0x1b, 0x58,
//                0xfa, 0xb3, 0x24, 0xe4, 0xfa, 0xd6, 0x75, 0x94,
//                0x55, 0x85, 0x80, 0x8b, 0x48, 0x31, 0xd7, 0xbc,
//                0x3f, 0xf4, 0xde, 0xf0, 0x8e, 0x4b, 0x7a, 0x9d,
//                0xe5, 0x76, 0xd2, 0x65, 0x86, 0xce, 0xc6, 0x4b,
//                0x61, 0x16},
byte authdata[] = {0x50, 0x51, 0x52, 0x53, 0xc0, 0xc1, 0xc2, 0xc3,
                   0xc4, 0xc5, 0xc6, 0xc7};
byte iv[] = {0x07, 0x00, 0x00, 0x00, 0x40, 0x41, 0x42, 0x43,
             0x44, 0x45, 0x46, 0x47};
// byte tag[] = {0x1a, 0xe1, 0x0b, 0x59, 0x4f, 0x09, 0xe2, 0x6a,
//             0x7e, 0x90, 0x2e, 0xcb, 0xd0, 0x60, 0x06, 0x91};

ChaChaPoly chachapoly;

const char hexChars[] = "0123456789ABCDEF";

/*
 * Takes a pointer to the ChaChaPoly cipher, a pointer to outBuffer and a
 * pointer to the t buffer. It writes the encrypted data to the outBuffer
 * and the computed tag to the t buffer.
 */
void test_encrypt(ChaChaPoly *cipher, byte *outBuffer, uint8_t *t){
  // Set the key and the IV
  cipher->clear();
  cipher->setKey(key, sizeof(key));
  cipher->setIV(iv, sizeof(iv));

  // Add the auth data
  cipher->addAuthData(authdata, sizeof(authdata));

  // Write the encrypted data to the buffer
  cipher->encrypt(outBuffer, plaintext, sizeof(plaintext));

  // Write the tag to the tag buffer
  cipher->computeTag(t, cipher->tagSize());
}

void setup()
{
    Serial.begin(9600);

    // Initalise a buffer to store to encrypted data
    byte encryptedOut[MAX_PLAINTEXT_LEN];
    // Initialize a buffer to store the computed tag
    uint8_t tag[16];

    // Encrypt the data into the buffer
    test_encrypt(&chachapoly, encryptedOut, tag);

    Serial.println("TEST ENCRYPTION:");

    Serial.println("In Key:");
    printArray(key, sizeof(key)); Serial.println();
    Serial.println();

    Serial.println("In Plaintext: ");
    printArray(plaintext, sizeof(plaintext)); Serial.println();
    Serial.println();

    Serial.println("In Authdata: ");
    printArray(authdata, sizeof(authdata)); Serial.println();
    Serial.println();

    Serial.println("In IV: ");
    printArray(iv, sizeof(iv)); Serial.println();
    Serial.println();

    Serial.println("Computed Tag: ");
    printArray(tag, sizeof(tag)); Serial.println();
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
