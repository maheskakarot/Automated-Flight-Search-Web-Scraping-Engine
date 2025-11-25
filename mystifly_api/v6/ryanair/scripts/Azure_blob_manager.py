import re
import json
import base64
import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Protocol.KDF import PBKDF2
from azure.storage.blob import BlobServiceClient


class AzureBlob:

    def __init__(self):
        self.encryption_obj = MystiflyEncryption()

    def upload_data_to_blob_storage(self, azure_config, search_id, data_list):
        if len(data_list):

            decrypted_data = self.get_string(azure_config)
            blob_service_client = BlobServiceClient(
                account_url=f"https://{decrypted_data['AccountName']}.blob.core.windows.net",
                credential=decrypted_data['AccountKey'])
            container_client = blob_service_client.get_container_client(decrypted_data['ConnectionRef'])

            for data_obj in data_list:
                blob_name = decrypted_data['Store_Dir'] + '/' + search_id[:6] + '/' + search_id[6:8] + '/' + \
                            search_id + '/' + 'SupplierLogs' + '/' + data_obj.supplier_name + '/' + data_obj.api_name + '/' + \
                            self.get_filename_str(data_obj)

                blob_client = container_client.get_blob_client(blob_name)
                blob_client.upload_blob(data_obj.data)

    def get_string(self, data):

        decrypted_data = self.encryption_obj.decrypt(data)
        result = re.search(r'{(.+?)}', decrypted_data).group(0)
        result = json.loads(result)
        return result

    def get_filename_str(self, data):
        name = data.api_name.split('/')
        if len(name) == 2:
            name = name[1]
        else:
            name = name[0]

        res = name + str(data.time_data)
        if data.data_type == 'request':
            res = res + 'RQ.txt'
        elif data.data_type == 'response':
            res = res + 'RS.txt'

        return res.replace(':', '-').replace(' ', '-').replace('.', '-')

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


class API_data:

    def __init__(self, data_str, api_name_, supplier_name_, data_category):
        self.time_data = datetime.datetime.now()
        self.api_name = api_name_
        self.supplier_name = supplier_name_
        self.data = data_str
        self.data_type = data_category

