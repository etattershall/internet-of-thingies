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
