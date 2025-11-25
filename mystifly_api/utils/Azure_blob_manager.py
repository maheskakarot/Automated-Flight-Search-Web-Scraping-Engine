import re
import json
import datetime
from azure.storage.blob import BlobServiceClient
from utils.mystifly_encryption import MystiflyEncryption

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
                blob_client.upload_blob(data_obj.data,overwrite=True)

    def get_string(self, data):

        decrypted_data = self.encryption_obj.decrypt(data)
        result = re.search(r'{(.+?)}', decrypted_data).group(0)
        result = json.loads(result)
        return result

    def get_filename_str(self, data):
        res = data.api_name + str(data.time_data)
        if data.data_type == 'request':
            res = res + 'RQ.txt'
        elif data.data_type == 'response':
            res = res + 'RS.txt'

        return res.replace(':', '-').replace(' ', '-').replace('.', '-')

class API_data:

    def __init__(self, data_str, api_name_, supplier_name_, data_category):
        self.time_data = datetime.datetime.now()
        self.api_name = api_name_
        self.supplier_name = supplier_name_
        self.data = data_str
        self.data_type = data_category

