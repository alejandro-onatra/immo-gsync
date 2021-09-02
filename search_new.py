import requests
import json

# GoogleClassManager
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


class GoogleSheetManager:

    token_file = 'token.json'
    credentials_file = 'credentials-personal.json'
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    sheet_id = None

    configuration = None
    credentials = None
    service = None

    def __init__(self, configuration):
        self.configuration = configuration
        if 'token_file' in configuration:
            self.token_file = configuration['token_file']
        if 'credentials_file' in configuration:
            self.configuration = configuration['credentials_file']
        if 'scopes' in configuration:
            self.scopes = configuration['scopes']
        if 'sheet_id' in configuration:
            self.sheet_id = configuration['sheet_id']
        self._authenticate()
        self._get_service()

    def set_spreadsheet(self, sheet_id):
        self.sheet_id = sheet_id

    def _authenticate(self):
        creds = None
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)

        if creds and creds.valid:
            self.credentials = creds
            return

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, self.scopes)
            creds = flow.run_local_server(port=0)

        with open(self.token_file, 'w') as token:
            token.write(creds.to_json())

        self.credentials = creds

    def _get_service(self):
        self.service = build('sheets', 'v4', credentials=self.credentials)

    def get_table_data_as_map(self, sheet_range):
        sheet = self.service.spreadsheets()
        result = sheet.values().get(spreadsheetId=self.sheet_id, range=sheet_range).execute()
        values = result.get('values', [])

        if not values:
            print('ERROR:: No data found.')

        # Get the columns to describe the rows, assume it will be in the header
        header = values[0]
        header_size = len(header)
        sheet_rows = []
        for row_number in range(1, len(values),1):
            element_as_map = {}
            for column_number in range(header_size-1):
                element_as_map[header[column_number]] = values[row_number][column_number]
            sheet_rows.append(element_as_map)

        print(json.dumps(sheet_rows, indent=3))
        return sheet_rows

    def set_table_data_from_map(self, sheet_range, data_as_map):
        values = [list(data_as_map[0].keys())]
        for row in data_as_map:
            values.append(list(row.values()))
        body = {
            'values': values
        }
        result = self.service.spreadsheets().values().update(
            spreadsheetId=self.sheet_id, valueInputOption='RAW', range=sheet_range, body=body
        ).execute()
        print('{0} cells updated.'.format(result.get('updatedCells')))

    def append_table_data_from_map(self, sheet_range, data_as_map):
        values = [list(data_as_map[0].keys())]
        for row in data_as_map:
            values.append(list(row.values()))
        body = {
            'values': values
        }
        result = self.service.spreadsheets().values().append(
            spreadsheetId=self.sheet_id, valueInputOption='RAW', range=sheet_range, body=body
        ).execute()
        print('{0} cells updated.'.format(result.get('updatedCells')))

class ApartmentIntegrationPipeline:

    total_success = 0
    total_exchange = 0
    total_rejected = 0
    total_entries = 0
    configuration = None

    def __init__(self, configuration):
        self.configuration = configuration

    def execute(self):
        search_results = self._get_search_results(self.configuration['first_url'])
        processed_entries = self._process_search_results(search_results)
        print(f'INFO:: There were {self.total_success} success and  {self.total_exchange} exchange offers from a total of {self.total_entries} entries')

    def _get_search_results(self, url):

        request = requests.post(url)
        status_code = request.status_code
        json_body = json.loads(request.content)
        if status_code >= 200:
            print(f'INFO:: The request was successfuly processed with code {status_code}')
            # print(json_body)
        else:
            print(f'WARNING:: The request was wrongly processed with code {status_code}, you suck!!')

        return json_body

    def _process_search_results(self, search_results):

        next_page, number_of_pages, page_number, page_size = self._get_apartment_metadata(search_results)
        processed_entries = []
        for iteration in range(number_of_pages - 1):
            mapped_entries = self._get_mapped_apartment_data(search_results)
            processed_entries.append(mapped_entries)
            search_results = self._get_search_results('https://www.immobilienscout24.de'+next_page)
            next_page, number_of_pages, page_number, page_size = self._get_apartment_metadata(search_results)

        return processed_entries

    def _get_apartment_metadata(self, search_results):
        metadata = {
            'paging': search_results['searchResponseModel']['resultlist.resultlist']['paging']
        }

        page_number = metadata['paging']['pageNumber']
        page_size = metadata['paging']['pageSize']
        number_of_pages = metadata['paging']['numberOfPages']
        number_of_hits = metadata['paging']['numberOfHits']
        number_of_listings = metadata['paging']['numberOfListings']
        self.total_entries = number_of_listings
        if 'next' in metadata['paging']:
            next_page = metadata['paging']['next']['@xlink.href']
        else:
            next_page = None

        print(f'INFO:: We are on the page {page_number} of {page_size} viewing {number_of_listings} listings.')
        print(f'DEBUG:: The next page is: {next_page}')

        return next_page, number_of_pages, page_number, page_size

    def _get_mapped_apartment_data(self, search_results):
        processed_entries = []
        entry_list = search_results['searchResponseModel']['resultlist.resultlist']['resultlistEntries'][0]['resultlistEntry']

        print(f'DEBUG:: Processing {len(entry_list)} entries')

        for entry in entry_list:
            processed_entry, errors = self._process_single_apartment(entry)
            if processed_entry is None: continue
            processed_entries.append(processed_entry)
            self.total_success += 1
            print(f'DEBUG:: Processing {processed_entry}')

        return processed_entries

    def _process_single_apartment(self, entry):

        id = entry['@id']

        title = entry['resultlist.realEstate']['title']
        if 'tauschwohnung' in title.lower():
            # print(f'DEBUG:: The id {id} is an exchange apartment and will be rejected')
            self.total_exchange += 1
            return None, [{'code': 'E001', 'message': 'Exchange entries are not valid'}]

        address = entry['resultlist.realEstate']['address']
        if 'wgs84Coordinate' in address:
            latitude = address['wgs84Coordinate']['latitude']
            longitude = address['wgs84Coordinate']['longitude']
        else:
            latitude = 0
            longitude = 0
        quarter = address['quarter']
        cold_rent = entry['resultlist.realEstate']['price']['value']
        hot_rent = entry['resultlist.realEstate']['calculatedTotalRent']['totalRent']['value']
        size = entry['resultlist.realEstate']['livingSpace']
        room_number = entry['resultlist.realEstate']['numberOfRooms']
        built_in_kitchen = entry['resultlist.realEstate']['builtInKitchen']
        have_balcony = entry['resultlist.realEstate']['balcony']
        if 'energyEfficiencyClass' in entry['resultlist.realEstate']:
            energy_efficiency = entry['resultlist.realEstate']['energyEfficiencyClass']
        else:
            energy_efficiency = 'Not available'
        contact = entry['resultlist.realEstate']['contactDetails']

        processed_entry = {
            'id': id,
            'title': title,
            'url': f'https://www.immobilienscout24.de/expose/{id}',
            'address': address,
            'maps_url': f'https://www.google.com/maps/@{latitude},{longitude}z',
            'quarter': quarter,
            'cold_rent': cold_rent,
            'hot_rent': hot_rent,
            'size': size,
            'room_number': room_number,
            'built_in_kitchen': built_in_kitchen,
            'have_balcony': have_balcony,
            'energy_efficiency': energy_efficiency,
            'contact': contact
        }

        return processed_entry, {}


if __name__ == '__main__':

    # first_url = 'https://www.immobilienscout24.de/Suche/de/berlin/berlin/wohnung-mieten?numberofrooms=2.0-&price=0.0-1100.0&livingspace=55.0-&equipment=builtinkitchen,balcony&pricetype=rentpermonth&geocodes=110000000406,110000000101,110000000701,110000000301,110000000201,1100000006&enteredFrom=saved_search'
    # pipeline = ApartmentIntegrationPipeline({'first_url': first_url})
    # pipeline.execute()

    sheet_manager = GoogleSheetManager({
        'sheet_id': '1hooYLbOZrmRSFggVpn4u2zfMNXt2J0asvinYVOgCoV0'
    })
    data = sheet_manager.get_table_data_as_map('Listado!B2:I35')
    sheet_manager.set_table_data_from_map('ListadoTest!B2', data)

