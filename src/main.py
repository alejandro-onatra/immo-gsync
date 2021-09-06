import os
import schedule
import time
from src.pipelines.process_apartment_data import ApartmentIntegrationPipeline
from src.components.telegram.TelegramBotManager import TelegramBotManager


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
            'first_url': os.environ['SEARCH_URL']
        },
        'TelegramBotManager': {
            'bot_token': os.environ['BOT_TOKEN'],
            'bot_chat_id': os.environ['BOT_CHAT_ID'],
            'chat_ids': os.environ['CHAT_IDS']
        }
    })
    pipeline.execute()


if __name__ == '__main__':
    # schedule.every().hour.do(find_apartments)
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)
    find_apartments()