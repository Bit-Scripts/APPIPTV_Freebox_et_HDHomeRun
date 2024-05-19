import sys
import os
import unittest
from unittest.mock import patch

# Ajouter dynamiquement le chemin du module 'src'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from MainWindow import MainWindow  # Assurez-vous de pointer vers l'emplacement correct de votre classe

class TestMainWindow(unittest.TestCase):

    @patch('requests.get')
    def test_get_ordered_uuids(self, mock_get):
        if os.getenv('CI'):
            self.skipTest('Skipping network test in CI environment')

        # Mock the API response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "result": {
                "uuid1": {"name": "France 2"},
                "uuid2": {"name": "France 3"}
            }
        }

        app = MainWindow()
        ordered_uuids = app.get_ordered_uuids()

        # Ajoutez ici vos assertions pour vérifier les résultats
        self.assertEqual(len(ordered_uuids), 2)
        self.assertEqual(ordered_uuids[0][1], "France 2")
        self.assertEqual(ordered_uuids[1][1], "France 3")

if __name__ == '__main__':
    unittest.main()
