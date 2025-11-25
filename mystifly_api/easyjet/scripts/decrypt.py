
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Protocol.KDF import PBKDF2
import base64
import json
import re
import requests

class MystiflyEncryption:
    IV = b'GJh6QuOiZUBcEGYf'
    PASSWORD = '2R5JS3QJ9Q5PUMS'
    SALT = b'vdIFlor2TdTIjAvH'


    def decrypt(self,encrypted_data):
        try:
            decoded_value = base64.b64decode(encrypted_data)
            key = PBKDF2(self.PASSWORD, self.SALT, 16, 65536)
            cipher = AES.new(key, AES.MODE_CBC,self.IV)
            dec_value = cipher.decrypt(decoded_value)
            decrypted_data =  dec_value.decode('utf-8')
            result = re.search(r'{(.+?)}', decrypted_data).group(0)
            result = json.loads(result)
            return result
        except Exception as e:
            raise ValueError("Invalid Input")



def get_card_details(my_scard_config,data, api):
    encryption = MystiflyEncryption()
    decrypted_data = encryption.decrypt(my_scard_config)

    url = decrypted_data['Url']
    endpoint = decrypted_data[api]
    url = f'{url}/{endpoint}'
    
    response = requests.post(url, json=data)
    data = response.json()
    return data