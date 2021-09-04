import requests
import json
from haversine import haversine


class ImmoManager:

    _total_success = 0
    _total_exchange = 0
    _total_wbs = 0
    _total_rejected = 0
    _total_entries = 0

    _configuration = None
    _first_url = None

    def __init__(self, configuration):
        self._configuration = configuration
        if 'first_url' in configuration:
            self._first_url = configuration['first_url']

    def set_first_url(self,url):
        self._first_url = url

    def get_processed_search_results(self):
        search_results = self._get_search_results(self._first_url)
        processed_entries = self._process_search_results(search_results)
        print(f'INFO:: There were {self._total_success} success, {self._total_exchange} exchange offers and {self._total_wbs} WBS from a total of {self._total_entries} entries')
        return processed_entries

    def _get_search_results(self, url):
        request = requests.post(url)
        status_code = request.status_code
        json_body = json.loads(request.content)
        if status_code >= 200:
            print(f'INFO:: The request was successfuly processed with code {status_code}')
        else:
            print(f'WARNING:: The request was wrongly processed with code {status_code}, you suck!!')

        return json_body

    def _process_search_results(self, search_results):

        next_page, number_of_pages, page_number, page_size = self._get_apartment_metadata(search_results)
        processed_entries = {}
        for iteration in range(number_of_pages - 1):
            mapped_entries = self._get_mapped_apartment_data(search_results)
            processed_entries = processed_entries | mapped_entries
            search_results = self._get_search_results('https://www.immobilienscout24.de'+next_page)
            next_page, number_of_pages, page_number, page_size = self._get_apartment_metadata(search_results)

        # print(json.dumps(processed_entries, indent=3))
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
        self._total_entries = number_of_listings
        if 'next' in metadata['paging']:
            next_page = metadata['paging']['next']['@xlink.href']
        else:
            next_page = None

        print(f'INFO:: We are on the page {page_number} of {page_size} viewing {number_of_listings} listings.')
        print(f'DEBUG:: The next page is: {next_page}')

        return next_page, number_of_pages, page_number, page_size

    def _get_mapped_apartment_data(self, search_results):
        processed_entries = {}
        entry_list = search_results['searchResponseModel']['resultlist.resultlist']['resultlistEntries'][0]['resultlistEntry']

        print(f'DEBUG:: Processing {len(entry_list)} entries')

        for entry in entry_list:
            id, processed_entry, errors = self._process_single_apartment(entry)
            if id is None or processed_entry is None:
                continue
            processed_entries[id] = processed_entry
            self._total_success += 1
            # print(f'DEBUG:: Processing {processed_entry}')

        return processed_entries

    def _process_single_apartment(self, entry):

        id = entry['@id']
        # Filter out
        title = entry['resultlist.realEstate']['title']
        if 'tauschwohnung' in title.lower():
            # print(f'DEBUG:: The id {id} is an exchange apartment and will be rejected')
            self._total_exchange += 1
            return None, None, [{'code': 'E001', 'message': 'Exchange entries are not valid'}]
        if 'wbs' in title.lower():
            # print(f'DEBUG:: The id {id} requires wbs and will be rejected')
            self._total_wbs += 1
            return None, None, [{'code': 'E002', 'message': 'WBS entries are not valid'}]
        # Process address
        address = entry['resultlist.realEstate']['address']
        if 'wgs84Coordinate' in address:
            latitude = address['wgs84Coordinate']['latitude']
            longitude = address['wgs84Coordinate']['longitude']
        else:
            latitude = 0
            longitude = 0
        quarter = address['quarter']
        center_coordinates = (52.519606771749594, 13.407080083827983)
        apartment_coordinates = (latitude, longitude)
        distance_center = haversine(center_coordinates, apartment_coordinates) if latitude > 0 and longitude > 0 else 9999
        # Process main apartment features
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
        # Process contact information
        contact = entry['resultlist.realEstate']['contactDetails']
        if 'portraitUrl' in contact:
            del contact['portraitUrl']
        if 'portraitUrlForResultList' in contact:
            del contact['portraitUrlForResultList']
        # Process pictures
        picture_number = 0
        if 'galleryAttachments' in entry['resultlist.realEstate']:
            picture_number = len(entry['resultlist.realEstate']['galleryAttachments']['attachment'])
        # Calculate total apartment score
        raw_score = (20 * (size/hot_rent)) + (0.5 if built_in_kitchen else 0) + (0.5 if have_balcony else 0) + (4 * (1/distance_center)) + (room_number/8)
        normalized_score = raw_score * 100 + picture_number

        processed_entry = {
            'opinion': '', # temporal usage as i need one empty space in the google sheet
            'application_state': 'Abierto',
            'score': normalized_score,
            'cold_rent': cold_rent,
            'hot_rent': hot_rent,
            'size': size,
            'room_number': room_number,
            'quarter': quarter,
            'distance_center': distance_center,
            'built_in_kitchen': built_in_kitchen,
            'have_balcony': have_balcony,
            'url': f'https://www.immobilienscout24.de/expose/{id}',
            'number_of_pics': picture_number,
            'energy_efficiency': energy_efficiency,
            'maps_url': f'https://www.google.com/maps/@{latitude},{longitude},18z',
            'address': str(address),
            'contact': str(contact),
            'title': title,
            'id': id,
        }

        return id, processed_entry, {}