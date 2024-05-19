from PyQt6.QtCore import QObject, pyqtSignal
import vlc

class VLCStateMonitor(QObject):
    error_detected = pyqtSignal(str)

    def __init__(self, media_player, parent=None):
        super().__init__(parent)
        self.media_player = media_player

    def check_state(self):
        player_state = self.media_player.get_state()

        if player_state == vlc.State.Ended:
            self.error_detected.emit("Erreur lors de la lecture du flux vidéo.")