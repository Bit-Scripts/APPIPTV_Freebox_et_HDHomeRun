import os
import time
import requests
from PyQt6.QtCore import pyqtSignal, QThread

class DataLoadThread(QThread):
    data_loaded = pyqtSignal(dict)
    # channels_loaded = pyqtSignal(dict)

    def __init__(self, ordered_uuids, logger, application_path, parent=None):
        super(DataLoadThread, self).__init__(parent)
        self.ordered_uuids = ordered_uuids
        self.logger = logger
        self.application_path = application_path

    def run(self):
        channel_info = self.load_channel_info()
        epg_data = self.load_epg_data()
        self.emit_sorted_data(channel_info, epg_data)

    def load_channel_info(self):
        channels_list_url = 'http://mafreebox.freebox.fr/api/v8/tv/channels'
        try:
            response = requests.get(channels_list_url, timeout=60)
            response.raise_for_status()
            data = response.json()
            return {uuid: {'name': info['name'], 'logo_url': self.get_channel_icon(info['name'])} for uuid, info in data['result'].items()}
        except requests.RequestException as e:
            self.logger.error(f"Failed to load channel info: {e}", exc_info=True)
            return {}

    def load_epg_data(self):
        now = int(time.time())
        two_hours = 2 * 60 * 60
        eighteen_hours = 18 * 60 * 60
        all_data = {}
        try:
            for timestamp in range(now - two_hours, now + eighteen_hours, 3600):  # Ajout de pas d'une heure
                url = f"http://mafreebox.freebox.fr/api/v8/tv/epg/by_time/{timestamp}"
                response = requests.get(url, timeout=60)
                response.raise_for_status()
                data = response.json()
                if 'result' in data:
                    for uuid, value in data['result'].items():
                        if uuid in all_data:
                            # Ici, dépend de la structure des données, par exemple, ajouter à une liste ou mettre à jour un sous-dictionnaire
                            all_data[uuid].update(value)  # Si c'est un dictionnaire
                        else:
                            all_data[uuid] = value
            return all_data
        except requests.RequestException as e:
            self.logger.error(f"Failed to load EPG data: {e}", exc_info=True)
            return {}
        
    def enrich_epg_data(self, epg_data, channel_info):
        enriched_data = {}
        for number, name, icon_path, uuid_ordered in self.ordered_uuids:
            if uuid_ordered in epg_data:
                programs = epg_data[uuid_ordered]
                enriched_programs = {}
                for program_id, program in programs.items():
                    adjusted_number = "3" if number == "301" else number
                    enriched_programs[program_id] = {
                        'channel_number': adjusted_number,
                        'channel_name': name,
                        'channel_icon': icon_path,
                        **program
                    }
                enriched_data[uuid_ordered] = enriched_programs
            else:
                self.logger.error(f"Missing program data for UUID: {uuid_ordered}")
        return enriched_data

    def emit_sorted_data(self, channel_info, epg_data):
        # Assurez-vous que tous les UUID nécessaires sont inclus
        sorted_channels_info = {uuid: channel_info.get(uuid, {}) for uuid in self.ordered_uuids}
        enriched_epg_data = self.enrich_epg_data(epg_data, sorted_channels_info)
        self.data_loaded.emit(enriched_epg_data)

    def get_channel_icon(self, channel_name):
        sanitized_name = channel_name.replace(" ", "_").replace("-", "_").replace("'", "")
        icon_formats = ['svg', 'png']
        for fmt in icon_formats:
            icon_path = os.path.join(self.application_path, 'assets', 'logos', f'{sanitized_name}.{fmt}')
            if os.path.exists(icon_path):
                return icon_path
        return os.path.join(self.application_path, 'assets', 'image', 'missing_icon.png')