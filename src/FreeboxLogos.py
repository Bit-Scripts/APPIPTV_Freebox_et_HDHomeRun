"""Refresh the router's current catalogue and every advertised channel logo."""
import json
import logging
import os
from pathlib import Path
import re
from urllib.parse import urljoin

import requests
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage
from unidecode import unidecode

BASE_URL = 'http://mafreebox.freebox.fr'
CATALOGUE_URL = BASE_URL + '/api/v8/tv/channels'


def channel_key(name):
    return re.sub(r'[^a-z0-9+]', '', unidecode(name).lower())


def match_channel(name, catalogue):
    """Match names, including the playlist's unique 14-character truncations."""
    key = channel_key(name)
    exact = [(uuid, info) for uuid, info in catalogue.items()
             if key in {channel_key(info.get('name', '')),
                        channel_key(info.get('short_name', ''))}]
    if len(exact) == 1:
        return exact[0]
    services = [item for item in exact if item[1].get('has_service')]
    if len(services) == 1:
        return services[0]
    if len(name) == 14:
        prefix = [(uuid, info) for uuid, info in catalogue.items()
                  if channel_key(info.get('name', '')[:14]) == key]
        if len(prefix) == 1:
            return prefix[0]
    return None


def read_catalogue(directory):
    try:
        return json.loads((Path(directory) / 'catalogue.json').read_text())
    except (OSError, ValueError):
        return {}


def refresh_logos(directory, interrupted=lambda: False):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    with requests.Session() as session:
        response = session.get(CATALOGUE_URL, timeout=10)
        response.raise_for_status()
        payload = response.json()
        if not payload.get('success'):
            raise RuntimeError('Catalogue Freebox indisponible : %s' % payload.get('error_code'))
        catalogue = payload['result']
        downloaded, failed = 0, []
        for uuid, info in catalogue.items():
            if interrupted():
                break
            logo_url = info.get('logo_url')
            if not logo_url:
                continue
            # Never derive a guessed image endpoint from a channel name.
            filename = re.sub(r'[^a-zA-Z0-9_-]', '_', uuid) + '.png'
            try:
                logo = session.get(urljoin(BASE_URL, logo_url), timeout=5)
                logo.raise_for_status()
                if QImage.fromData(logo.content).isNull():
                    raise ValueError('Logo non décodable')
                temporary = directory / (filename + '.tmp')
                temporary.write_bytes(logo.content)
                os.replace(temporary, directory / filename)
                downloaded += 1
            except (requests.RequestException, OSError, ValueError) as exc:
                failed.append(uuid)
                logging.getLogger(__name__).debug('Logo %s : %s', uuid, exc)
        temporary = directory / 'catalogue.json.tmp'
        temporary.write_text(json.dumps(catalogue, ensure_ascii=False, indent=2))
        os.replace(temporary, directory / 'catalogue.json')
    return catalogue, {'catalogue': len(catalogue), 'downloaded': downloaded,
                       'failed': failed, 'interrupted': interrupted()}


class FreeboxLogoRefresh(QThread):
    refreshed = pyqtSignal(dict, dict)
    failed = pyqtSignal(str)

    def __init__(self, directory, parent=None):
        super().__init__(parent)
        self.directory = directory

    def run(self):
        try:
            catalogue, report = refresh_logos(self.directory, self.isInterruptionRequested)
            self.refreshed.emit(catalogue, report)
        except Exception as exc:
            self.failed.emit(str(exc))
