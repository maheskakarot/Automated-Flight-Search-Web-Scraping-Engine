from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Protocol.KDF import PBKDF2
import base64



class MystiflyEncryption:
    IV = b'GJh6QuOiZUBcEGYf'
    PASSWORD = '2R5JS3QJ9Q5PUMS'
    SALT = b'vdIFlor2TdTIjAvH'

    def encrypt(self, raw):
        try:
            key = PBKDF2(self.PASSWORD, self.SALT, 16, 65536)
            cipher = AES.new(key, AES.MODE_CBC, self.IV)
            padded_data = pad(raw.encode('utf-8'), AES.block_size)
            encrypted_data = cipher.encrypt(padded_data)
            encoded_data = base64.b64encode(encrypted_data)
            return encoded_data.decode('utf-8')
        except Exception as e:
            raise Exception("Encryption failed: {}".format(str(e)))

    def decrypt(self, encrypted_data):
        try:

            decoded_value = base64.b64decode(encrypted_data)
            cipher = AES.new(self.generate_key(), AES.MODE_CBC, self.IV)
            dec_value = cipher.decrypt(decoded_value)
            return dec_value.decode('utf-8')
        except Exception as e:
            raise ValueError("Invalid Input")

    def generate_key(self):
        key = PBKDF2(self.PASSWORD, self.SALT, 16, 65536)
        return key