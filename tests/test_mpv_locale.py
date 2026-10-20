"""Protect against Qt resetting the numeric locale after importing mpv."""
import os
from pathlib import Path
import subprocess
import sys
import unittest


class NumericLocaleTest(unittest.TestCase):
    def test_qt_french_locale_before_player_creation(self):
        script = '''
import locale
from PyQt6.QtWidgets import QApplication
from src.MpvWidget import MpvWidget
app = QApplication([])
try:
    locale.setlocale(locale.LC_NUMERIC, 'fr_FR.UTF-8')
except locale.Error:
    print('French locale unavailable')
    raise SystemExit(77)
assert locale.localeconv()['decimal_point'] == ','
widget = MpvWidget()
assert locale.setlocale(locale.LC_NUMERIC) == 'C'
assert locale.localeconv()['decimal_point'] == '.'
widget.shutdown()
print('French numeric locale corrected before mpv_create')
'''
        result = subprocess.run([sys.executable, '-s', '-X', 'faulthandler', '-c', script],
                                cwd=Path(__file__).resolve().parents[1],
                                env=os.environ.copy(), capture_output=True, text=True, timeout=15)
        if result.returncode == 77:
            self.skipTest('French locale unavailable')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('corrected before mpv_create', result.stdout)
