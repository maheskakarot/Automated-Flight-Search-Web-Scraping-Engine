import gspread
from oauth2client.service_account import ServiceAccountCredentials
from .constants import CREDS_FILE_LOCATION, REQUESTED_GOOGLE_SHEET_SCOPES


class SheetClient:
    def __init__(self):
        self.CREDS_FILE_LOCATION = CREDS_FILE_LOCATION
        self.REQUESTED_GOOGLE_SHEET_SCOPES = REQUESTED_GOOGLE_SHEET_SCOPES
        self.client = self.__get_sheet_client()

    def __get_sheet_client(self):
        creds = ServiceAccountCredentials.from_json_keyfile_name(self.CREDS_FILE_LOCATION, self.REQUESTED_GOOGLE_SHEET_SCOPES)

        client = gspread.authorize(creds)

        return client

    def get_sheet_instance(self, sheet_name, tab_name):
        sheet_instance = self.client.open(sheet_name).worksheet(tab_name)

        return sheet_instance
