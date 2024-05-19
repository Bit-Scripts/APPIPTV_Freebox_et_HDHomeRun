import requests
from PyQt6.QtGui import QPixmap
from io import BytesIO
from functools import lru_cache

class ImageCache:
    @staticmethod
    @lru_cache(maxsize=100)  # Limite de cache à 100 images
    def get_pixmap(url):
        """ Télécharge une image depuis une URL et retourne un QPixmap. """
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        image_bytes = BytesIO(response.content)
        pixmap = QPixmap()
        pixmap.loadFromData(image_bytes.getvalue())
        return pixmap