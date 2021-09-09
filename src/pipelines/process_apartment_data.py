import datetime
import json
from src.components.immo.ImmoManager import ImmoManager
from src.components.gcp.gdrive.GoogleSheetManager import GoogleSheetManager
from src.commons.DataManipulationUtils import DataManipulationUtils
from src.components.telegram.TelegramBotManager import TelegramBotManager


class ApartmentIntegrationPipeline:

    _processed_entries = None
    _append_entries = None
    _notification_status = None
    _immo_manager = None
    _gsheet_manager = None
    _telegram_bot = None

    _configuration = None
    _sheet_range = None
    _gsheet_manager_conf = None
    _immo_manager_conf = None
    _telegram_bot_conf = None

    def __init__(self, configuration):
        self._configuration = configuration
        if 'sheet_range' in configuration:
            self._sheet_range = configuration['sheet_range']
        self._gsheet_manager_conf = configuration['GoogleSheetManager']
        self._immo_manager_conf = configuration['ImmoManager']
        self._telegram_bot_conf = configuration['TelegramBotManager']
        self._telegram_bot = TelegramBotManager(self._telegram_bot_conf)
        self._sheet_manager = GoogleSheetManager(self._gsheet_manager_conf)
        self._immo_manager = ImmoManager(self._immo_manager_conf)

    def execute(self):
        self._extract_apartment_data()
        self._load_data_to_sheets()
        if self._append_entries:
            self._send_alerts_for_best_apartments()
        self._notify_process_metadata()

    def _extract_apartment_data(self):
        processed_entries = self._immo_manager.get_processed_search_results()
        self._processed_entries = processed_entries

    def _load_data_to_sheets(self):
        data = self._sheet_manager.get_table_data_as_map_array(self._sheet_range)
        previous_entries = DataManipulationUtils.create_indexed_map_from_map_array(data, 'id') if len(data) > 0 else []

        if len(previous_entries) > 0:
            previous_keys = previous_entries.keys()
            current_keys = self._processed_entries.keys()
            append_entries = {}
            for current_key in current_keys:
                if current_key not in previous_keys:
                    append_entries[current_key] = self._processed_entries[current_key]
            print(f'DEBUG:: Found {len(append_entries)} new entries in the new batch')
            if append_entries:
                self._sheet_manager.append_table_data_from_map_array(self._sheet_range, list(append_entries.values()))
                self._append_entries = append_entries
            return

        # In case of no previous entries
        self._sheet_manager.set_table_data_from_map_array(self._sheet_range, list(self._processed_entries.values()))
        self._append_entries = self._processed_entries

    def _send_alerts_for_best_apartments(self):
        responses = []
        notification_entry_ids = set()
        for entry in self._append_entries.values():
            if entry['score'] > 400 and entry['distance_center'] <= 4 and entry['hot_rent'] < 1200:
                notification_entry_ids.add(entry['id'])
        for id in notification_entry_ids:
            entry = self._append_entries[id]
            hot_rent = entry['hot_rent']
            size = entry['size']
            distance_center = entry['distance_center']
            room_number = entry['room_number']
            score = entry['score']
            quarter = entry['quarter']
            url = entry['url']
            maps_url = entry['maps_url']
            built_in_kitchen = 'has a fitted kitchen' if entry['built_in_kitchen'] else 'does not have a fitted kitchen'
            have_balcony = 'has a balcony' if entry['have_balcony'] else 'does not have a balcony'
            message = f'Apartment id: {id} with {score} points.\n'
            message += f'The apartment has *{size}sqm* and *{room_number}* rooms. The rent cost in total *{hot_rent}* euros, ' \
                       f'it is located in *{quarter}* at *{distance_center} km* from the center. ' \
                       f'It {built_in_kitchen} and {have_balcony}. \n'
            message += f'You can find more info at {url} and the location in {maps_url} \n'

            # Send messages 1 by 1 because it the text is too long it will failed.
            responses.append(self._telegram_bot.send_text_message_to_users(message, self._telegram_bot_conf['chat_ids']))

        self._notification_status = responses

    def _notify_process_metadata(self):
        message = f'These are the results of the process at {str(datetime.datetime.now())} \n'
        message += f'There were {self._immo_manager.total_success} success, {self._immo_manager.total_exchange} exchange offers and {self._immo_manager.total_wbs} WBS from a total of {self._immo_manager.total_entries} entries \n'
        message += f'Found {len(self._append_entries) if self._append_entries else 0} new entries in the new batch \n'
        if self._notification_status:
            for response in self._notification_status:
                message += f'The responses to the notification is: ```{json.loads(response.content)}```'
        responses = self._telegram_bot.send_text_message_to_users(message)




