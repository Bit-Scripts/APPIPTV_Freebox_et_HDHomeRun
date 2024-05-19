import os
import unittest
from src.MainWindow import MainWindow  # Assurez-vous de pointer vers l'emplacement correct de votre classe

class MainWindow(unittest.TestCase):

    def test_get_ordered_uuids(self):
        if os.getenv('CI'):
            self.skipTest('Skipping network test in CI environment')

        app = MainWindow()
        ordered_uuids = app.get_ordered_uuids()

        # Ajoutez ici vos assertions pour vérifier les résultats

if __name__ == '__main__':
    unittest.main()
