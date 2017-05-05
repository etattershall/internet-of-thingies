from Crypto.Cipher import ChaCha20
import array

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


def __init__():
    global key, plaintext, iv
    key = convertToByteString(key)
    plaintext = convertToByteString(plaintext)
    iv = convertToByteString(iv)


def convertToByteString(arrayOfBytes):
    "Converts an array of ints <256 to a byte array accepted by Crypto"
    return array.array("B", arrayOfBytes).tostring()


def convertToInt(arrayOfBytes):
    "Converts an array of bytes (bigendian) to an int"
    output = 0
    for byteNum in range(len(arrayOfBytes)):
        correspondingByte = arrayOfBytes[len(arrayOfBytes) - byteNum - 1]
        output += correspondingByte * ((2 ** 8) ** byteNum)
    return output


def convertCounter(arrayOfBytes):
    """Converts an array of ints <256 to an integer to pass into Crypto.

    cipher.seek(int) moves in the stream by 'int' bytes.
    This function takes an arrayOfBytes like those passed to the Arduino and
    generates that 'int'.


    """


def encrypt(p, k, n, c=0):
    """Encrypts plaintext with key, nonce and counter

    Params
    ------
    p: bytestring
        The plaintext to encrypt
    k: bytestring
        The key to use (must be length 32)
    n: bytestring
        The nonce to use (must be length 8)
    c: int
        The inital counter to use (default 0)
    """
    cipher = ChaCha20.new(key=k, nonce=n)
    cipher.seek(c)
    return cipher.encrypt(p)


if __name__ == "__main__":
    __init__()
    print("Without counter")
    print(" ".join(hex(el) for el in encrypt(plaintext, key, iv, c=0)))
    print("With counter")
    print(" ".join(hex(el) for el in encrypt(plaintext, key, iv,
                                             convertToInt(counter))))
