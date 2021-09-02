import requests
import json

total_success = 0
total_exchange = 0
total_rejected = 0
total_entries = 0


def get_search_results(url):

    request = requests.post(url)
    status_code = request.status_code
    json_body = json.loads(request.content)
    if status_code >= 200:
        print(f'INFO:: The request was successfuly processed with code {status_code}')
        # print(json_body)
    else:
        print(f'WARNING:: The request was wrongly processed with code {status_code}, you suck!!')

    return json_body


def process_search_results(search_results):

    next_page, number_of_pages, page_number, page_size = get_apartment_metadata(search_results)
    processed_entries = []
    for iteration in range(number_of_pages - 1):
        mapped_entries = get_mapped_apartment_data(search_results)
        processed_entries.append(mapped_entries)
        search_results = get_search_results('https://www.immobilienscout24.de'+next_page)
        next_page, number_of_pages, page_number, page_size = get_apartment_metadata(search_results)

    return processed_entries


def get_apartment_metadata(search_results):
    metadata = {
        'paging': search_results['searchResponseModel']['resultlist.resultlist']['paging']
    }

    page_number = metadata['paging']['pageNumber']
    page_size = metadata['paging']['pageSize']
    number_of_pages = metadata['paging']['numberOfPages']
    number_of_hits = metadata['paging']['numberOfHits']
    number_of_listings = metadata['paging']['numberOfListings']
    global total_entries
    total_entries = number_of_listings
    if 'next' in metadata['paging']:
        next_page = metadata['paging']['next']['@xlink.href']
    else:
        next_page = None

    print(f'INFO:: We are on the page {page_number} of {page_size} viewing {number_of_listings} listings.')
    print(f'DEBUG:: The next page is: {next_page}')

    return next_page, number_of_pages, page_number, page_size


def get_mapped_apartment_data(search_results):
    processed_entries = []
    entry_list = search_results['searchResponseModel']['resultlist.resultlist']['resultlistEntries'][0]['resultlistEntry']

    print(f'DEBUG:: Processing {len(entry_list)} entries')

    global total_success
    for entry in entry_list:
        processed_entry, errors = process_single_apartment(entry)
        if processed_entry is None: continue
        processed_entries.append(processed_entry)
        total_success += 1
        print(f'Processing {processed_entry}')

    return processed_entries


def process_single_apartment(entry):

    id = entry['@id']

    title = entry['resultlist.realEstate']['title']
    if 'tauschwohnung' in title.lower():
        print(f'The id {id} is an exchange apartment and will be rejected')
        global total_exchange
        total_exchange += 1
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

    return processed_entry


if __name__ == '__main__':

    first_url = 'https://www.immobilienscout24.de/Suche/de/berlin/berlin/wohnung-mieten?numberofrooms=2.0-&price=0.0-1100.0&livingspace=55.0-&equipment=builtinkitchen,balcony&pricetype=rentpermonth&geocodes=110000000406,110000000101,110000000701,110000000301,110000000201,1100000006&enteredFrom=saved_search'
    search_results = get_search_results(first_url)
    processed_entries = process_search_results(search_results)
    global total_success
    global total_exchange
    global total_entries
    print(f'INFO:: There were {total_success} and we found {total_exchange} exchange offers from a total of {total_entries} entries')


