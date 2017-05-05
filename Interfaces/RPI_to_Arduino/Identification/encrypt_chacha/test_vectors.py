import pytest
"""
These two tests run through a veriaty of different chacha20 inputs to check
that the correct output is produced

The ChaCha20 official test vectors from
https://tools.ietf.org/html/draft-agl-tls-chacha20poly1305-04#section-7
All of these are with a 0 byte plaintext


raw_official_testVectors is in the format of the official vectors as strings,

official_testVectors is an interator that converts the raw test vectors into
                     real vectors

arduino_vectors are vectors from the arduino's library (some of these are
                are tested in the other script)


"""

import encrypt_chacha

raw_official_testVectors = [
    {
        "key": ("0000000000000000000000000000000000000000000000000000000000000"
                "000"),
        "nonce": "0000000000000000",
        "stream": ("76b8e0ada0f13d90405d6ae55386bd28bdd219b8a08ded1aa836efcc8b"
                   "770dc7da41597c5157488d7724e03fb8d84a376a43b8f41518a11cc387"
                   "b669b2ee6586")
    }, {
        "key": ("0000000000000000000000000000000000000000000000000000000000000"
                "001"),
        "nonce": "0000000000000000",
        "stream": ("4540f05a9f1fb296d7736e7b208e3c96eb4fe1834688d2604f450952ed"
                   "432d41bbe2a0b6ea7566d2a5d1e7e20d42af2c53d792b1c43fea817e9a"
                   "d275ae546963")
    }, {
        "key": ("0000000000000000000000000000000000000000000000000000000000000"
                "000"),
        "nonce": "0000000000000001",
        "stream": ("de9cba7bf3d69ef5e786dc63973f653a0b49e015adbff7134fcb7df137"
                   "821031e85a050278a7084527214f73efc7fa5b5277062eb7a0433e445f"
                   "41e3")
    }, {
        "key": ("0000000000000000000000000000000000000000000000000000000000000"
                "000"),
        "nonce": "0100000000000000",
        "stream": ("ef3fdfd6c61578fbf5cf35bd3dd33b8009631634d21e42ac33960bd138"
                   "e50d32111e4caf237ee53ca8ad6426194a88545ddc497a0b466e7d6bbd"
                   "b0041b2f586b")
    }, {
        "key": ("000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1"
                "e1f"),
        "nonce": "0001020304050607",
        "stream": ("f798a189f195e66982105ffb640bb7757f579da31602fc93ec01ac56f8"
                   "5ac3c134a4547b733b46413042c9440049176905d3be59ea1c53f15916"
                   "155c2be8241a38008b9a26bc35941e2444177c8ade6689de95264986d9"
                   "5889fb60e84629c9bd9a5acb1cc118be563eb9b3a4a472f82e09a7e778"
                   "492b562ef7130e88dfe031c79db9d4f7c7a899151b9a475032b63fc385"
                   "245fe054e3dd5a97a5f576fe064025d3ce042c566ab2c507b138db853e"
                   "3d6959660996546cc9c4a6eafdc777c040d70eaf46f76dad3979e5c536"
                   "0c3317166a1c894c94a371876a94df7628fe4eaaf2ccb27d5aaae0ad7a"
                   "d0f9d4b6ad3b54098746d4524d38407a6deb3ab78fab78c9")
    }
]

arduino_vectors =[
{
    "key": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 201, 202,
            203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215,
            216],
    "plaintext": [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                  0x00, 0x00, 0x00, 0x00],
    "nonce": [101, 102, 103, 104, 105, 106, 107, 108],
    "ciphertext": [0xDA, 0x04, 0x49, 0xA6, 0x77, 0x0C, 0x11, 0x64, 0xF4, 0x9F,
                   0xD3, 0xBD, 0x1A, 0xDC, 0xCA, 0xC0, 0x2D, 0xF1, 0x8E, 0x5E,
                   0x23, 0xB3, 0x45, 0x1C, 0xB9, 0xA6, 0xE1, 0x51, 0x25, 0xBB,
                   0x1E, 0x31, 0x8E, 0x55, 0xD2, 0x7E, 0xB3, 0xEE, 0xF5, 0xD6,
                   0x10, 0x17, 0x1D, 0xBD, 0x5B, 0x13, 0x04, 0x70, 0x3F, 0x10,
                   0x3E, 0xAD, 0x5B, 0x9A, 0xB0, 0x6E, 0x69, 0x7E, 0x3C, 0x7F,
                   0xFA, 0x5C, 0x80, 0xCC],
    "counter": [0, 0, 0, 0, 0, 0, 0, 0]
}, {
    "key": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 201, 202,
            203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215,
            216],
    "plaintext": [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                  0x00, 0x00, 0x00, 0x00],
    "nonce": [101, 102, 103, 104, 105, 106, 107, 108],
    "ciphertext": [0x2A, 0x7E, 0x73, 0xC2, 0x2A, 0xE5, 0xCF, 0x4E, 0x21, 0x75,
                   0xB1, 0x26, 0x38, 0x3F, 0x60, 0x84, 0x11, 0x25, 0xFC, 0xAD,
                   0xFD, 0x16, 0x54, 0xF2, 0xD7, 0x8C, 0x5D, 0x49, 0x8D, 0x96,
                   0xBE, 0x15, 0xC9, 0x00, 0x12, 0x09, 0x14, 0x43, 0x2D, 0x6D,
                   0x64, 0x33, 0x88, 0xA6, 0x16, 0x39, 0x86, 0xFD, 0xD8, 0x85,
                   0x4D, 0x76, 0x42, 0xEC, 0x0A, 0x0C, 0x8A, 0xF2, 0x99, 0x2E,
                   0x54, 0xAE, 0xB4, 0xD9],
    "counter": [109, 110, 111, 112, 113, 114, 115, 116]
}, {
    "key": [49, 50, 51, 52, 53, 54, 55, 56, 57, 48, 49, 50, 51, 52, 53, 54,
            55, 56, 57, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 48, 49, 50],
    "plaintext": [84, 104, 105, 115, 32, 105, 115, 32, 97, 32, 116, 101, 115,
                  116, 32, 115, 116, 114, 105, 110, 103, 44, 32, 101, 110,
                  99, 114, 121, 112, 116, 101, 100, 32, 117, 115, 105, 110,
                  103, 32, 67, 104, 97, 67, 104, 97, 32, 112, 111, 108, 121],
    "nonce": [48, 49, 50, 51, 52, 53, 54, 55],
    "ciphertext": [77, 160, 7, 47, 202, 128, 146, 215, 73, 204, 48, 16, 213,
                   66, 221, 198, 200, 158, 19, 21, 133, 51, 73, 7, 221, 17,
                   153, 242, 1, 147, 79, 14, 149, 204, 162, 198, 107, 169,
                   76, 54, 82, 26, 193, 134, 86, 111, 35, 195, 160, 181],
    "counter": [0, 0, 0, 0, 0, 0, 0, 0]

}]


def convert_hex_string_to_array_of_ints(s):
    "Takes a hex string eg add1 and returns an array of ints < 256"
    return [int(s[hexByteStartIndex:hexByteStartIndex + 2], 16)
            for hexByteStartIndex in range(0, len(s), 2)]


def official_testVectors():
    """Iterator to yeild vectors of [int, int, int] from the hex strings
    above. It also introduces common keys. eg ciphertext"""
    for vector in raw_official_testVectors:
        for key in vector:
            vector[key] = convert_hex_string_to_array_of_ints(vector[key])
        vector["plaintext"] = [0 for i in range(len(vector["stream"]))]
        vector["ciphertext"] = vector["stream"]
        vector["counter"] = [0 for i in range(8)]
        yield vector


def runVector(vector):
    "Runs a vectors against ChaCha20, checks plaintext is expected"
    pt = encrypt_chacha.convertToByteString(vector["plaintext"])
    n = encrypt_chacha.convertToByteString(vector["nonce"])
    c = encrypt_chacha.convertCounter(vector["counter"])
    k = encrypt_chacha.convertToByteString(vector["key"])
    ct = encrypt_chacha.convertToByteString(vector["ciphertext"])
    assert ct == encrypt_chacha.encrypt(pt, k, n, c)


def test_official_vectors():
    """Tests the official test vectors from the iterator in test_vectors.py"""
    for vector in official_testVectors():
        runVector(vector)


def test_arduino_vectors():
    """Tests vectors produced using the arduino"""
    for vector in arduino_vectors:
        runVector(vector)
