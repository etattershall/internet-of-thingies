import pytest
import struct

from Crypto.Util._raw_api import expect_byte_string
import encrypt_chacha


def test_convertToByteString_is_accepted_by_crypto():
    '''The output from convertToByteString should not raise an error when
    passed to expect_byte_string'''
    testArray = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    expect_byte_string(encrypt_chacha.convertToByteString(testArray))


def test_convertCounter_offset_is_0():
    """ChaCha20.seek() takes the output from convertCounter and uses the last
    6 bits (mod 64) to use as an offset within each block rather than setting
    the counter. This tests that convertCounter always makes this offset 0."""
    testArrays = [[0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 1],
                  [0, 0, 0, 0, 0, 0, 1, 0], [0, 0, 1, 0, 0, 0, 0, 0],
                  [0, 0, 0, 0, 0, 0, 1, 1], [0, 255, 0, 0, 0, 0, 0, 255]]

    for test in testArrays:
        # For all the test cases, check that the output is divisible by 64
        assert encrypt_chacha.convertCounter(test) % 64 == 0


def test_convertCounter_blocks():
    """This splits the output from convertCounter into block_high and block_low
    in the same way that ChaCha20.seek() does. It tests that when those
    32bit integers are packed into a byte array by
    _raw_chacha20_lib.chacha20_seek(), the bytes are ordered in the correct way
    as the input. This could be an issue because of the endianness of the
    processor.
    """
    testInputs = [
        ([0, 0, 0, 0, 0, 0, 0, 0], b"\x00\x00\x00\x00", b"\x00\x00\x00\x00"),
        ([0, 1, 0, 0, 0, 0, 0, 0], b"\x00\x01\x00\x00", b"\x00\x00\x00\x00"),
        ([0, 0, 0, 0, 0, 0, 0, 1], b"\x00\x00\x00\x00", b"\x00\x00\x00\x01"),
        ([0, 0, 0, 4, 0, 0, 0, 2], b"\x00\x00\x00\x04", b"\x00\x00\x00\x02")
    ]
    for test, low, high in testInputs:
        # Remove offset
        position = encrypt_chacha.convertCounter(test) >> 6
        block_low = position & 0xFFFFFFFF
        block_high = position >> 32
        # _raw_chacha20_lib.chacha20_seek() writes these inputs as little
        # endian regardless of processor. Check that this writing is in the
        # expected way here regardless of processor.
        # TODO: It would be good to run this on a big endian machine.
        assert struct.pack("<i", block_low) == low
        assert struct.pack("<i", block_high) == high


def test_encrypt_works_with_plaintext_key_nonce():
    """Tests if encrypt works with the default counter. If the cipher works
    then it should output the same as the Arduino implementation."""
    key = [1,   2,   3,   4,   5,   6,   7,   8,
           9,   10,  11,  12,  13,  14,  15,  16,
           201, 202, 203, 204, 205, 206, 207, 208,
           209, 210, 211, 212, 213, 214, 215, 216]
    plaintext = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    iv = [101, 102, 103, 104, 105, 106, 107, 108]
    arduinoOuput = [0xDA, 0x04, 0x49, 0xA6, 0x77, 0x0C, 0x11, 0x64, 0xF4, 0x9F,
                    0xD3, 0xBD, 0x1A, 0xDC, 0xCA, 0xC0, 0x2D, 0xF1, 0x8E, 0x5E,
                    0x23, 0xB3, 0x45, 0x1C, 0xB9, 0xA6, 0xE1, 0x51, 0x25, 0xBB,
                    0x1E, 0x31, 0x8E, 0x55, 0xD2, 0x7E, 0xB3, 0xEE, 0xF5, 0xD6,
                    0x10, 0x17, 0x1D, 0xBD, 0x5B, 0x13, 0x04, 0x70, 0x3F, 0x10,
                    0x3E, 0xAD, 0x5B, 0x9A, 0xB0, 0x6E, 0x69, 0x7E, 0x3C, 0x7F,
                    0xFA, 0x5C, 0x80, 0xCC]
    key = encrypt_chacha.convertToByteString(key)
    plaintext = encrypt_chacha.convertToByteString(plaintext)
    iv = encrypt_chacha.convertToByteString(iv)
    arduinoOuput = encrypt_chacha.convertToByteString(arduinoOuput)
    assert arduinoOuput == encrypt_chacha.encrypt(plaintext, key, iv, c=0)


def test_encrypt_works_with_plaintext_key_nonce_counter():
    """Tests if encrypt works with counter set as well as the other params.
    Again, this should give the same as the Arduino."""
    key = [1,   2,   3,   4,   5,   6,   7,   8,
           9,   10,  11,  12,  13,  14,  15,  16,
           201, 202, 203, 204, 205, 206, 207, 208,
           209, 210, 211, 212, 213, 214, 215, 216]
    plaintext = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    iv = [101, 102, 103, 104, 105, 106, 107, 108]
    counter = [109, 110, 111, 112, 113, 114, 115, 116]
    arduinoOuput = [0x2A, 0x7E, 0x73, 0xC2, 0x2A, 0xE5, 0xCF, 0x4E, 0x21, 0x75,
                    0xB1, 0x26, 0x38, 0x3F, 0x60, 0x84, 0x11, 0x25, 0xFC, 0xAD,
                    0xFD, 0x16, 0x54, 0xF2, 0xD7, 0x8C, 0x5D, 0x49, 0x8D, 0x96,
                    0xBE, 0x15, 0xC9, 0x00, 0x12, 0x09, 0x14, 0x43, 0x2D, 0x6D,
                    0x64, 0x33, 0x88, 0xA6, 0x16, 0x39, 0x86, 0xFD, 0xD8, 0x85,
                    0x4D, 0x76, 0x42, 0xEC, 0x0A, 0x0C, 0x8A, 0xF2, 0x99, 0x2E,
                    0x54, 0xAE, 0xB4, 0xD9]

    # Convert everything to a byte array, the arrays above are deliberately
    # pasted directly from arduino code to prove that the two ciphers take the
    # same input.
    key = encrypt_chacha.convertToByteString(key)
    plaintext = encrypt_chacha.convertToByteString(plaintext)
    iv = encrypt_chacha.convertToByteString(iv)
    counter = encrypt_chacha.convertCounter(counter)
    arduinoOuput = encrypt_chacha.convertToByteString(arduinoOuput)

    # Check outputs are the same between the two ciphers
    assert arduinoOuput == encrypt_chacha.encrypt(plaintext, key, iv,
                                                  c=counter)
