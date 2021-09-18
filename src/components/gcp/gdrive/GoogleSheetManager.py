import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


class GoogleSheetManager:

    _token_file = 'token.json'
    _credentials_file = 'credentials.json'
    _scopes = ['https://www.googleapis.com/auth/spreadsheets']
    _sheet_id = None

    _configuration = None
    _credentials = None
    _service = None

    def __init__(self, configuration):
        """Constructor using standard a configuation map

        :param configuration:
        """
        self._configuration = configuration
        if 'token_file' in configuration:
            self._token_file = configuration['token_file']
        if 'credentials_file' in configuration:
            self._credentials_file = configuration['credentials_file']
        if 'scopes' in configuration:
            self._scopes = configuration['scopes']
        if 'sheet_id' in configuration:
            self._sheet_id = configuration['sheet_id']
        self._authenticate()
        self._get_service()

    def set_spreadsheet(self, sheet_id):
        self._sheet_id = sheet_id

    def _authenticate(self):
        creds = None
        if os.path.exists(self._token_file):
            creds = Credentials.from_authorized_user_file(self._token_file, self._scopes)

        if creds and creds.valid:
            self._credentials = creds
            return

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(self._credentials_file, self._scopes)
            creds = flow.run_local_server(port=0)

        with open(self._token_file, 'w') as token:
            token.write(creds.to_json())

        self._credentials = creds

    def _get_service(self):
        self._service = build('sheets', 'v4', credentials=self._credentials)

    def get_table_data_as_map_array(self, sheet_range):
        sheet = self._service.spreadsheets()
        result = sheet.values().get(spreadsheetId=self._sheet_id, range=sheet_range).execute()
        values = result.get('values', [])

        if not values:
            print('ERROR:: No data found.')

        # Get the columns to describe the rows, assume it will be in the header
        header = values[0]
        header_size = len(header)
        sheet_rows = []
        for row_number in range(1, len(values),1):
            element_as_map = {}
            for column_number in range(header_size):
                element_as_map[header[column_number]] = values[row_number][column_number]
            sheet_rows.append(element_as_map)

        # print(json.dumps(sheet_rows, indent=3))
        return sheet_rows

    def set_table_data_from_map_array(self, sheet_range, data):
        if len(data) == 0:
            print('WARNING:: No data to process')
            return

        values = [list(data[0].keys())]
        for row in data:
            values.append(list(row.values()))
        body = {
            'values': values
        }
        result = self._service.spreadsheets().values().update(
            spreadsheetId=self._sheet_id, valueInputOption='RAW', range=sheet_range, body=body
        ).execute()
        print('{0} cells updated.'.format(result.get('updatedCells')))

    def append_table_data_from_map_array(self, sheet_range, data_as_map):
        values = []
        for row in data_as_map:
            values.append(list(row.values()))
        body = {
            'values': values
        }
        result = self._service.spreadsheets().values().append(
            spreadsheetId=self._sheet_id, valueInputOption='RAW', range=sheet_range, body=body
        ).execute()
        print('{0} cells updated.'.format(result.get('updatedCells')))