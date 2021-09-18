import os
from src.pipelines.process_apartment_data import ApartmentIntegrationPipeline


def find_apartments():
    root = os.path.dirname(os.path.abspath(__file__))
    pipeline = ApartmentIntegrationPipeline({
        'sheet_range': 'Listado!B2:S',
        'GoogleSheetManager': {
            'sheet_id': os.environ['SHEET_ID'],
            'token_file': root + '/token.json',
            'credentials_file': root + '/credentials.json'
        },
        'ImmoManager': {
            'first_url': os.environ['SEARCH_URL'],
            'filters':{
                'include_exchange': False,
                'include_wbs': False
            }
        },
        'TelegramBotManager': {
            'bot_token': os.environ['BOT_TOKEN'],
            'bot_chat_id': os.environ['BOT_CHAT_ID'],
            'chat_ids': os.environ['CHAT_IDS']
        }
    })
    pipeline.execute()


if __name__ == '__main__':
    find_apartments()