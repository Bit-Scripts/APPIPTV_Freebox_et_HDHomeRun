import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from PyQt6.QtCore import QBuffer, QIODevice
from PyQt6.QtGui import QImage
from src.FreeboxLogos import match_channel, read_catalogue, refresh_logos
from src.MainWindow import MainWindow


class LogoTest(unittest.TestCase):
    def test_matches_current_names_and_unique_truncations(self):
        catalogue = {'one': {'name': 'Chaîne très longue', 'short_name': 'Courte'}}
        self.assertEqual(match_channel('Chaine tres longue', catalogue)[0], 'one')
        self.assertEqual(match_channel('Courte', catalogue)[0], 'one')
        self.assertIsNone(match_channel('Ancienne chaîne', catalogue))
        catalogue['two'] = {'name': 'Chaîne très longue aussi'}
        self.assertIsNone(match_channel('Chaîne très lo', catalogue))

    def test_duplicate_names_require_unique_service(self):
        catalogue = {'old': {'name': 'Station', 'has_service': False},
                     'current': {'name': 'Station', 'has_service': True}}
        self.assertEqual(match_channel('Station', catalogue)[0], 'current')
        catalogue['old']['has_service'] = True
        self.assertIsNone(match_channel('Station', catalogue))

    def test_refresh_overwrites_existing_and_preserves_failed_cache(self):
        image = QImage(2, 2, QImage.Format.Format_RGB32)
        image.fill(0xff0000)
        buffer = QBuffer(); buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        image.save(buffer, 'PNG')
        catalogue = {'one': {'name': 'One', 'logo_url': '/one.png'},
                     'two': {'name': 'Two', 'logo_url': '/two.png'}}
        response = Mock(); response.json.return_value = {'success': True, 'result': catalogue}
        good = Mock(); good.content = bytes(buffer.data())
        bad = Mock(); bad.content = b'invalid image'
        with tempfile.TemporaryDirectory() as folder, patch('src.FreeboxLogos.requests.Session') as session:
            root = Path(folder)
            (root / 'one.png').write_bytes(b'old')
            (root / 'two.png').write_bytes(b'previous cached logo')
            session.return_value.__enter__.return_value.get.side_effect = [response, good, bad]
            _, report = refresh_logos(folder)
            self.assertEqual(report['downloaded'], 1)
            self.assertEqual(report['failed'], ['two'])
            self.assertNotEqual((root / 'one.png').read_bytes(), b'old')
            self.assertEqual((root / 'two.png').read_bytes(), b'previous cached logo')
            self.assertEqual(read_catalogue(folder), catalogue)

    def test_playlist_keeps_more_than_two_channels_and_auto_only(self):
        lines = []
        for index in range(1, 101):
            lines.extend([f'#EXTINF:0,{index} - Channel {index} (auto)', f'rtsp://router/{index}'])
        channels = MainWindow.filter_freebox_playlist(None, lines)
        self.assertEqual(len(channels), 100)
        self.assertEqual(channels['100 - Channel 100'], 'rtsp://router/100')
