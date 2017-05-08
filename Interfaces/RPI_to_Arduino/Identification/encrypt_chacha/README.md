# Example Encrytion With ChaCha20

This sketch demonstrates encrypting and decrypting with ChaCha20 from the Arduino Crypto library.

**encrypt_chacha.py** is a python script that uses the **PyCryptodome** library to perform the same encryption and decryption.

**test_encrypt_chacha.py** is a pytest script for encrypt_chacha

**test_vectors.py** is a pytest script that that confirms that some hand copied examples from encrypt_chacha.ino are encrypted and decrypted in the same way in the python script. It also checks some official inputs and output provided for chacha20.
