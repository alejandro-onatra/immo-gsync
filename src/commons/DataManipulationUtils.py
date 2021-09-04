class DataManipulationUtils:

    @staticmethod
    def create_indexed_map_from_map_array(data, id_key):
        indexed_data = {}
        for entry in data:
            indexed_data[entry[id_key]] = entry
        return indexed_data