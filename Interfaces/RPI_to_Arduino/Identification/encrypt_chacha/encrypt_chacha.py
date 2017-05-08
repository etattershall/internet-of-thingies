from Crypto.Cipher import ChaCha20
import array
import struct


def convertToByteString(arrayOfBytes):
    "Converts an array of ints <256 to a byte array accepted by Crypto"
    return array.array("B", arrayOfBytes).tostring()


def convertCounter(arrayOfBytes):
    """Converts an array of ints <256 to an integer to pass into Crypto.

    cipher.seek(int) moves in the stream by 'int' bytes.
    This function takes an arrayOfBytes like those passed to the Arduino and
    generates that 'int'.

    """
    assert len(arrayOfBytes) == 8

    # the counter(8 bytes) is split into block_low (4 bytes) then
    # block_high(4 bytes) internally by pycryptodome
    # Everything is little endian here!
    asByteString = convertToByteString(arrayOfBytes)
    # Unpack as two native unsigned longs. If this processor is little endian
    # then this should not be converted in the crypto function
    # _raw_chacha20_lib.chacha20_seek().
    # If this processer is big endian then this should be converted
    block_low, block_high = struct.unpack("LL", asByteString)
    return ((block_high << 32) + block_low) << 6


def get_cipher(k, n, c=0):
    """Sets up a chacha20 cipher object and returns it

    Usage
    -----
    key = convertToByteString(range(0, 32))
    nonce = convertToByteString(range(0, 8))
    counter = convertCounter([0, 0, 0, 0, 0, 0, 0, 1])
    cipher = get_cipher(key, nonce, counter)
    encrypted_stuff = cipher.encrypt(b"The secret plaintext")

    cipher = get_cipher(key, nonce, counter)
    cipher.decrypt(encrypted_stuff)

    Params
    ------
    k: bytestring
        The key to use (must be length 32)
    n: bytestring
        The nonce to use (must be length 8)
    c: int
        The inital counter to use (default 0)
        Use convertCounter(array of bytes (ints <256)) to get this
    """
    # Check the inputs are the correct length
    assert len(k) == 32
    assert len(n) == 8
    assert c >= 0
    # Create a cipher
    cipher = ChaCha20.new(key=k, nonce=n)
    # Set the counter
    cipher.seek(c)
    # Return the cipher
    return cipher
