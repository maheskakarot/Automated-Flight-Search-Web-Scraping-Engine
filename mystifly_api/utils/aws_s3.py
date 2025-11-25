import boto3


class UploadFiles:
    def __init__(self):
        self.s3_obj = boto3.client('s3')
        self.base_url = "https://mystifly.s3.ap-south-1.amazonaws.com/"

    def upload_files(self, file_name, bucket_name, folder_name):
        self.s3_obj.upload_file(file_name, bucket_name, f"{folder_name}/{file_name}")

    def get_file_link(self, file_name, folder_name):
        file_name = file_name.replace(" ", "+").replace(":", "%3A")
        file_link = self.base_url + folder_name + "/" + file_name
        print(file_link)
