import os
from src.components.immo.ImmoManager import ImmoManager
from src.components.gcp.gdrive.GoogleSheetManager import GoogleSheetManager
from src.commons.DataManipulationUtils import DataManipulationUtils


class ApartmentIntegrationPipeline:

    _processed_entries = None

    _configuration = None
    _sheet_range = None
    _gsheet_manager_conf = None
    _immo_manager_conf = None

    def __init__(self, configuration):
        self._configuration = configuration
        if 'sheet_range' in configuration:
            self._sheet_range = configuration['sheet_range']
        self._gsheet_manager_conf = configuration['GoogleSheetManager']
        self._immo_manager_conf = configuration['ImmoManager']

    def execute(self):
        self._extract_apartment_data()
        self._load_data_to_sheets()

    def _extract_apartment_data(self):
        immo_manager = ImmoManager(self._immo_manager_conf)
        processed_entries = immo_manager.get_processed_search_results()
        self._processed_entries = processed_entries

    def _load_data_to_sheets(self):
        sheet_manager = GoogleSheetManager(self._gsheet_manager_conf)
        data = sheet_manager.get_table_data_as_map_array(self._sheet_range)
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
                sheet_manager.append_table_data_from_map_array(self._sheet_range, list(append_entries.values()))
            return

        sheet_manager.set_table_data_from_map_array(self._sheet_range, list(self._processed_entries.values()))

