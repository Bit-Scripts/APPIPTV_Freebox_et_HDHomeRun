import json
import os
import sys
import requests
from PyQt6.QtWidgets import QMessageBox, QDialog, QLineEdit, QPushButton, QCheckBox, QApplication, QVBoxLayout, QLabel

def validate_hdhomerun_url(url):
    try:
        response = requests.get(url, timeout=5)  # Limite de temps pour la réponse
        if response.status_code == 200 and response.text.strip().startswith('#EXTM3U'):
            return True
    except requests.RequestException:
        return False
    return False

def show_restart_dialog():
    msg_box = QMessageBox()
    msg_box.setWindowTitle("Redémarrer l'application")
    msg_box.setText("Les modifications ont été enregistrées. Voulez-vous redémarrer l'application pour appliquer les changements ?")
    msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
    response = msg_box.exec()

    if response == QMessageBox.StandardButton.Yes:
        restart_application()

def restart_application():
    # Ajoutez votre logique de redémarrage ici
    # Cela peut être aussi simple que d'exécuter le script à nouveau et de fermer l'instance actuelle
    # Vous pouvez utiliser os.execv pour cela si vous êtes sous Unix ou Windows
    os.execv(sys.executable, ['python'] + sys.argv)


class SettingsDialog(QDialog):
    def __init__(self, config_file_path, config, parent=None):
        super().__init__(parent)
        self.config_file_path = config_file_path
        self.setGeometry(400, 400, 400, 100)
        self.centerWindow()
        self.config = config
        self.setWindowTitle("Configuration")
        self.setup_ui()

    def centerWindow(self):
        # Obtenir la taille de l'écran depuis l'application
        screen = QApplication.primaryScreen().geometry()
        windowSize = self.geometry()  # Obtient la taille de la fenêtre courante
        # Calculer la position x et y pour centrer la fenêtre
        x = int((screen.width() - windowSize.width()) / 2)
        y = int((screen.height() - windowSize.height()) / 2)
        self.setGeometry(x, y, windowSize.width(), windowSize.height())
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Ajouter des champs pour l'adresse IP
        self.url_label = QLabel("HDHomeRun IP Address:", self)
        self.url_input = QLineEdit(self.config.get("hdhomerun_url", "http://hdhomerun.local/lineup.m3u"), self)
        
        self.auto_detect_checkbox = QCheckBox("Auto-detect IP", self)
        self.auto_detect_checkbox.setChecked(self.config.get("auto_detect", True))
        
        save_button = QPushButton("Sauvegarder", self)
        save_button.clicked.connect(self.save_settings)
        
        layout.addWidget(self.url_label)
        layout.addWidget(self.url_input)
        layout.addWidget(self.auto_detect_checkbox)
        layout.addWidget(save_button)

    def save_settings(self):
        new_url = self.url_input.text().strip()
        auto_detect = self.auto_detect_checkbox.isChecked()
        
        if auto_detect:
            # Valider l'URL uniquement si auto_detect est activé et l'URL est spécifiée
            if new_url and validate_hdhomerun_url(new_url):
                self.config["hdhomerun_url"] = new_url
                self.save_config()
                QMessageBox.information(self, "Validation Réussie", "L'URL est valide et a été enregistrée.")
                show_restart_dialog()
                self.accept()  # Ferme le dialogue avec un status de succès
            else:
                QMessageBox.warning(self, "Validation Échouée", "L'URL fournie n'est pas une playlist M3U valide.")
        else:
            # Sauvegarder la configuration sans validation d'URL
            self.save_config()
            show_restart_dialog()
            self.accept()

    def save_config(self):
        # Écrire le config dans un fichier JSON
        with open(self.config_file_path, 'w') as config_file:
            json.dump(self.config, config_file, indent=4)