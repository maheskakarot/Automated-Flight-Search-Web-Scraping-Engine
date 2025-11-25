from datetime import datetime
from django.conf import settings
import os
from azure.storage.blob import BlobServiceClient


class LogMessage:
    def __init__(self, msg,screen_name, time_now, search_id=None, driver=None):
        self.driver = driver
        self.msg = msg
        self.folder = str(settings.BASE_DIR) + "/screen_short"
        self.screen_name = screen_name
        self.time_now = time_now
        self.search_id=search_id
    @property
    def save_log(self):
        if self.driver:
            file_name = "{} - {}.jpg".format(self.screen_name, self.time_now)
            self.driver.save_screenshot(f"{self.folder}/{file_name}")
            blob_service_client = BlobServiceClient.from_connection_string(settings.CONNECTION_STRING)
            try:
                blob_service_client.create_container(settings.CONTAINER)
            except:
                pass
            blob_client = blob_service_client.get_blob_client(container=settings.CONTAINER, blob=file_name)
            with open(f"{self.folder}/{file_name}", "rb") as data:
                blob_client.upload_blob(data, blob_type="BlockBlob")
            os.remove(f"{self.folder}/{file_name}")
            return f"{self.msg} screen_short: {blob_client.url}"
        return self.msg,self.search_id
