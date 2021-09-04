import os
from src.pipelines.process_apartment_data import ApartmentIntegrationPipeline

if __name__ == '__main__':
    root = os.path.dirname(os.path.abspath(__file__))
    pipeline = ApartmentIntegrationPipeline({
        'sheet_range': 'Listado!B2:S',
        'GoogleSheetManager': {
            'sheet_id': os.environ['SHEET_ID'],
            'token_file': root + '/token.json',
            'credentials_file': root + '/credentials.json'
        },
        'ImmoManager':{
            'first_url': os.environ['SEARCH_URL']
        }
    })
    pipeline.execute()