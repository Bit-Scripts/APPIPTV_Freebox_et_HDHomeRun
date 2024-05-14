import datetime
import json
import os
import sys
import time
import requests
from PyQt6 import QtWidgets
from PyQt6.QtGui import QPixmap, QColor, QPalette, QIcon, QPainter
from PyQt6.QtCore import Qt, QObject, QSize, QEvent, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer, QThread
from PyQt6.QtWidgets import QProgressBar, QSplashScreen, QMessageBox, QDialog, QLineEdit, QPushButton, QCheckBox, QTableWidgetItem, QApplication, QMainWindow, QStackedWidget, QVBoxLayout, QScrollArea, QWidget, QGridLayout, QToolButton, QSplitter, QHBoxLayout, QLabel
import vlc
from io import BytesIO
from functools import lru_cache
import pytz
import platform
import logging
from logging.handlers import RotatingFileHandler
import qdarkstyle

if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app 
    # path into variable _MEIPASS'.
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

# Définir le répertoire de base des logs selon le système d'exploitation
if platform.system() == "Windows":
    log_directory = "C:\\ProgramData\\IPTVAPP\\Logs"
    # Set environment variables
    os.environ['VLC_PLUGIN_PATH'] = 'C:·\\Program Files\\VideoLAN\\VLC\\plugins'
elif platform.system() == "Linux":
    log_directory = os.path.expanduser("~/.local/share/IPTVAPP/logs")
    # Set environment variables
    os.environ['VLC_PLUGIN_PATH'] = '/usr/lib/x86_64-linux-gnu/vlc/plugins'
elif platform.system() == "Darwin":  # macOS
    log_directory = os.path.expanduser("~/Library/Logs/IPTVAPP")
    # Set environment variables
    os.environ['VLC_PLUGIN_PATH'] = '/Applications/VLC.app/Contents/MacOS/plugins'
else:
    print("Système d'Exploitation Inconnu, utilisation du répertoire temporaire")
    log_directory = "/tmp"  # Utiliser un répertoire temporaire comme secours

# Tenter de créer le répertoire s'il n'existe pas
try:
    os.makedirs(log_directory, exist_ok=True)
except Exception as e:
    print(f"Échec de la création du répertoire de log: {str(e)}")
    # Essayer un autre emplacement de secours selon l'OS si le premier échoue
    if platform.system() == "Windows":
        log_directory = os.path.expanduser("~/AppData/Local/IPTVAPP/logs")
    elif platform.system() == "Linux" or platform.system() == "Darwin":
        log_directory = os.path.expanduser("~/.local/share/IPTVAPP/logs")
    else:
        print("Système d'Exploitation Inconnu, utilisation du répertoire temporaire")
        log_directory = "/tmp"  # Dernier recours: utiliser un répertoire temporaire

    try:
        os.makedirs(log_directory, exist_ok=True)
    except Exception as e:
        print(f"Échec de la création du répertoire de log de secours: {str(e)}")
        log_directory = "/tmp"  # Utiliser un répertoire temporaire comme dernier secours

# Configuration du gestionnaire de fichiers de log avec rotation
log_file_path = os.path.join(log_directory, 'IPTVAPP.log')
file_handler = RotatingFileHandler(log_file_path, maxBytes=10**6, backupCount=10)
file_handler.setLevel(logging.DEBUG)

# Formatter pour les logs
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Configurer le logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)

def get_config_path(app_name):
    if os.name == 'nt':  # Windows
        config_path = os.path.join(os.getenv('LOCALAPPDATA'), app_name)
    elif os.name == 'posix':  # Linux et macOS
        home = os.path.expanduser('~')
        if sys.platform == 'darwin':
            config_path = os.path.join(home, 'Library', 'Application Support', app_name)
        else:
            config_path = os.path.join(home, '.local', 'share', app_name)
    else:
        raise Exception("Système d'exploitation non supporté")

    os.makedirs(config_path, exist_ok=True)  # Crée le dossier s'il n'existe pas
    return config_path

app_name = 'IPTVAPP'
config_directory = get_config_path(app_name)
config_file_path = os.path.join(config_directory, 'config.json')

def load_config():
    default_config = {
        "hdhomerun_url": "http://hdhomerun.local/lineup.m3u",
        "auto_detect": True
    }
    try:
        with open(config_file_path, 'r') as config_file:
            config = json.load(config_file)
            return {**default_config, **config}  # Utilise les valeurs par défaut pour les clés manquantes
    except (FileNotFoundError, json.JSONDecodeError):
        return default_config

config = load_config()  # Gardez cette variable globale ou dans une instance pour accès à travers l'application

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

class VLCStateMonitor(QObject):
    error_detected = pyqtSignal(str)

    def __init__(self, media_player, parent=None):
        super().__init__(parent)
        self.media_player = media_player

    def check_state(self):
        player_state = self.media_player.get_state()

        if player_state == vlc.State.Ended:
            self.error_detected.emit("Erreur lors de la lecture du flux vidéo.")

class DataLoadThread(QThread):
    data_loaded = pyqtSignal(dict)
    # channels_loaded = pyqtSignal(dict)

    def __init__(self, ordered_uuids, parent=None):
        super(DataLoadThread, self).__init__(parent)
        self.ordered_uuids = ordered_uuids

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
            logger.error(f"Failed to load channel info: {e}", exc_info=True)
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
            logger.error(f"Failed to load EPG data: {e}", exc_info=True)
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
                logger.error(f"Missing program data for UUID: {uuid_ordered}")
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
            icon_path = os.path.join(application_path, 'logos', f'{sanitized_name}.{fmt}')
            if os.path.exists(icon_path):
                return icon_path
        return os.path.join(application_path, 'image', 'missing_icon.png')

class EPGTable(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dataLoaded = False
        self.setColumnCount(25)  # 24 heures + 1 colonne pour les logos et noms
        self.setup_table()
        self.setRowCount(0)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.itemClicked.connect(self.handle_item_click)
        self.channel_info_cache = {}
        self.call = 1
        self.channel_rows = {}
        
    def get_start_hour(self):
        now = datetime.datetime.now()
        start_hour = now.hour - 2 if now.hour > 0 else 22
        return start_hour

    def setup_table(self):
        start_hour = self.get_start_hour()
        hours = [f"{hour}:00" for hour in range(start_hour, 24)] + [f"{hour}:00" for hour in range(0, start_hour)]
        self.setHorizontalHeaderLabels([''] + hours)
        self.verticalHeader().setVisible(False)
        self.initialize_rows()

        # Style général du tableau
        self.setStyleSheet("""
            * {
                color: #dddddd;
                background-color: #00000000;
                border: none;
            }
            QTableWidget {
                gridline-color: #444444;
                border: none;
                color: #dddddd;
                background-color: #00000000;
            }
            QTableWidget::item {
                color: #dddddd;
                padding: 10px;
            }
        """)

    def initialize_rows(self):
        self.setColumnCount(24)  # Ajustez en fonction du nombre d'heures à afficher
        self.setRowCount(10)  # Ajustez en fonction du nombre de chaînes ou de lignes nécessaires

    def initialize_rows(self):
        # Supposons que vous avez une idée du nombre de lignes, ou vous les ajoutez dynamiquement ailleurs
        initial_row_count = 10  # Exemple de nombre de lignes initial
        self.setRowCount(initial_row_count)
        
        for row in range(initial_row_count):
            self.setRowHeight(row, 100)  # Définit la hauteur de chaque ligne à 100 pixels

        for column in range(25):
            self.setColumnWidth(column, 450) 
        self.setColumnWidth(0, 150) 

    def is_column_empty(self, col_index):       
        for row in range(self.rowCount()):
            item = self.item(row, col_index)
            if item and item.text().strip():
                return False
            widget = self.cellWidget(row, col_index)
            if widget:
                return False
        return True

    def remove_empty_columns(self):
        col_count = self.columnCount()
        for col in range(1, col_count):  # Ignorer la première colonne des logos
            empty = True
            for row in range(self.rowCount()):
                if self.item(row, col) and self.item(row, col).text().strip() != '':
                    empty = False
                    break
            if empty:
                self.removeColumn(col)

    def add_channel(self, channel_info, logo, name):
        row_count = self.rowCount()
        self.insertRow(row_count)
        self.setRowHeight(row_count, 100)  # Définir la hauteur pour la nouvelle ligne

        # Ajouter le logo et le nom de la chaîne
        widget = QtWidgets.QLabel(f"<img src='{logo}'><br>{name}")
        widget.setMargin(10)  # Ajuster la marge pour l'esthétique
        self.setCellWidget(row_count, 0, widget)

        # Initialiser les cellules pour les horaires de programmes
        for i in range(1, 25):
            self.setItem(row_count, i, QtWidgets.QTableWidgetItem(''))

    def update_program(self, row, col, start_time):
        if row < self.rowCount():
            self.item(row, col).setText(f'{start_time}')

    def handle_item_click(self, item):
        channel_uuid = item.data(Qt.ItemDataRole.UserRole)
        if channel_uuid:
            self.load_channel(channel_uuid)

    def load_channel(self, channel_uuid):
        logger.debug(f"Chargement de la chaîne avec UUID: {channel_uuid}")
        pass

    def calculate_column_index(self, epoch):
        hour = datetime.datetime.fromtimestamp(epoch).hour
        return hour

    def create_program_label(self, program_start, program):
        # Utilisation du style 'display: inline-block;' pour mieux contrôler l'alignement
        icon_html = f"<div style='font-size: 15px; vertical-align: middle; display: inline-block;'><img src='{program['channel_icon']}' height='35' width='35' style='height : 35px; vertical-align: middle; margin-right: 5px;'> {program['title']} </div><br />"
        # Ajustement de 'margin-top' pour aligner le texte avec l'icône
        text = f"<span style='vertical-align: top; font-size: 12px; display: inline-block;'>{program_start.strftime('%H:%M')} {program.get('desc', '')}</span>"
        label = QLabel(f"{icon_html}{text}")
        label.setMargin(0)  # Réduire la marge externe
        label.setWordWrap(True)
        label.setStyleSheet("""
            * {
                color: #dddddd;
                border: none;
            }
            QLabel {
                padding: 2px;          /* Réduire l'espacement interne */
                text-align: left;      /* Alignement du texte */
                line-height: 1;      /* Ajustement de l'espacement entre les lignes */
                font-size: 12px;       /* Ajustement de la taille de la police si nécessaire */
            }
        """)
        return label

    def populate_table_with_ordered_info(self, channel_data):
        if not self.dataLoaded:
            now = datetime.datetime.now(pytz.timezone('Europe/Paris'))
            start_hour = now.hour - 2 if now.hour > 0 else 22  # Début une heure avant l'heure actuelle
            self.clearContents()
            self.setRowCount(0)
            for channel_uuid, programs in channel_data.items():
                for program_key, program_details in programs.items():
                    row = self.find_or_create_row(channel_uuid, program_details)
                    epoch_time = program_key.split('_')[0] if program_key.split('_')[0].isdigit() else program_key.split('_')[1]
                    program_start = self.epoch_to_localtime_french(int(epoch_time))
                    if (program_start.hour >= start_hour or program_start.hour < start_hour - 1):
                        col = (program_start.hour - start_hour) % 24 + 1  # +1 pour les logos/noms
                        program_label = self.create_program_label(program_start, program_details)
                        self.setCellWidget(row, col, program_label)
                        # self.setItem(row, col, QtWidgets.QTableWidgetItem(self.format_program_info(program_start, program_details)))
            self.dataLoaded = True
            self.set_style_cells()
            
    def set_style_cells(self):
        dark_color = QColor('#152535')
        light_color = QColor('#102030')
        text_color = QColor('#dddddd')
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item is None:  # Si l'item n'existe pas, créez-en un nouveau pour cette cellule
                    item = QTableWidgetItem()
                    self.setItem(row, col, item)
                if row % 2 == 0:
                    item.setBackground(dark_color)
                else:
                    item.setBackground(light_color)
                item.setForeground(text_color)
                        
    def ensureColumnExists(self, col_index):
        if col_index >= self.columnCount():
            self.setColumnCount(col_index + 1)
            self.setHorizontalHeaderItem(col_index, QtWidgets.QTableWidgetItem(f"{col_index}:00"))

    def epoch_to_localtime_french(self, epoch_time):
        tz = pytz.timezone('Europe/Paris')
        local_time = datetime.datetime.fromtimestamp(epoch_time, tz)
        return local_time

    def seconds_to_duration(self, seconds):
        hours = seconds // 3600
        minutes = "{:02}".format((seconds % 3600) // 60)
        return f"{hours}h{minutes}"

    def format_program_info(self, program_start, program):
        icon_html = f"<img src='{program['channel_icon']}' height='20' width='20'>"
        return f"{icon_html} {program_start.strftime('%H:%M')} {program['title']} {program.get('desc', '')}"

    def find_or_create_row(self, channel_uuid, program_details):
        # Vérifiez que toutes les clés nécessaires sont présentes
        if 'channel_number' in program_details and 'channel_icon' in program_details and 'channel_name' in program_details:
            if channel_uuid not in self.channel_rows:
                row = self.rowCount()
                self.insertRow(row)
                self.channel_rows[channel_uuid] = row
                self.setRowHeight(row, 150)
                widget = self.create_channel_widget(program_details['channel_number'], program_details['channel_name'], program_details['channel_icon'])
                self.setCellWidget(row, 0, widget)
            return self.channel_rows[channel_uuid]
        else:
            # Log l'erreur si les données sont incomplètes
            logger.error(f"Missing channel information for program {program_details.get('title', 'Unknown')} on channel {channel_uuid}")
            return None

    def create_channel_widget(self, channel_number, channel_name, channel_icon_url):
        logo_item = QtWidgets.QLabel()
        logo_pixmap = QPixmap(channel_icon_url)

        if logo_pixmap.isNull():
            logger.error(f"Failed to load image from {channel_icon_url}")
            logo_pixmap = QPixmap(os.path.join(application_path, 'image/missing_icon.png'))  # Chemin vers une image par défaut
        
        logo_item.setPixmap(logo_pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo_item.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignCenter)
        name_item = QtWidgets.QLabel(f"{channel_number} - {channel_name}")
        name_item.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignCenter)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(logo_item)
        layout.addWidget(name_item)
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        return widget

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

class SemiTransparentBlurWidget(QWidget):
    def __init__(self, duration=30, channel_name=None, program_name=None, program_desc=None, program_picture_url=None, icon_path=None, program_start_date=None, program_duration=None, has_service=None, has_abo=None, available=None):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self.setMinimumWidth(800)
        self.setFixedHeight(200)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 0);")  # Fond complètement transparent
        self.duration = duration

        self.setupUI(icon_path, channel_name, program_name, program_desc, program_picture_url, program_start_date, program_duration, has_service, has_abo, available)
        
        self.show()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        if painter.isActive():
            painter.setBrush(QColor(0, 0, 0, 150))
            painter.drawRect(self.rect())
        else:
            logger.debug("Painter is not active")

    def epoch_to_localtime_french(self, epoch_time):
        tz = pytz.timezone('Europe/Paris')  # Définit le fuseau horaire pour la France
        local_time = datetime.datetime.fromtimestamp(epoch_time, tz)
        return local_time.strftime('%d/%m/%Y %H:%M:%S')  # Format jour/mois/année heure:minute:seconde

    def seconds_to_duration(self, seconds):
        hours = seconds // 3600
        minutes = "{:02}".format((seconds % 3600) // 60)
        return f"{hours}h{minutes}"
    
    def setupUI(self, channel_icon, channel_name, program_name, program_description, program_image_url, program_start_date, program_duration, has_service, has_abo, available):
        self.setWindowTitle('Effet de Flou sur le Fond')
        # Layout pour le contenu de premier plan
        layout = QHBoxLayout()
        layoutV = QVBoxLayout()

        # Ajouter les autres éléments sans flou
        layoutH = QHBoxLayout()
        channel_icon_lbl = QLabel()
        channel_icon_lbl.setPixmap(QPixmap(channel_icon).scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        layoutH.addWidget(channel_icon_lbl)

        channel_name_lbl = QLabel(channel_name)
        channel_name_lbl.setStyleSheet("font-weight: bold; font-size: 28px;")
        channel_name_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layoutH.addWidget(channel_name_lbl)

        date_layout = QVBoxLayout()
        # Réduire l'espacement entre les éléments
        date_layout.setSpacing(1)
        start_date_fr = self.epoch_to_localtime_french(program_start_date)
        logger.debug(f"Heure de début : {start_date_fr}")
        duration_fr = self.seconds_to_duration(program_duration)
        logger.debug(f"Durée : {duration_fr}")
        end_date_fr = self.epoch_to_localtime_french(program_start_date + program_duration)
        logger.debug(f"Heure de Fin : {end_date_fr}")
        start_date_lbl = QLabel()
        start_date_lbl.setText(f"Début : {start_date_fr}")
        start_date_lbl.setStyleSheet("font-size: 10px;")
        start_date_lbl.setAlignment(Qt.AlignmentFlag.AlignTop)
        duration_lbl = QLabel()
        duration_lbl.setText(f"Durée : {duration_fr}")
        duration_lbl.setStyleSheet("font-size: 10px;")
        duration_lbl.setAlignment(Qt.AlignmentFlag.AlignTop)
        end_date_lbl = QLabel()
        end_date_lbl.setText(f"Fin : {end_date_fr}")
        end_date_lbl.setStyleSheet("font-size: 10px;")
        end_date_lbl.setAlignment(Qt.AlignmentFlag.AlignTop)
        date_layout.addWidget(start_date_lbl)
        date_layout.addWidget(duration_lbl)
        date_layout.addWidget(end_date_lbl)
        date_layout.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        layoutH.addLayout(date_layout)
        layoutH.setSpacing(2)
        
        # Informations sur la disponibilité du service et sur l'abonnement
        service_layout = QHBoxLayout()
        service_title_layout = QVBoxLayout()
        service_status_layout = QVBoxLayout()
        
        # Réduire l'espacement entre les éléments
        service_title_layout.setSpacing(1)
        service_status_layout.setSpacing(1)
        service_layout.setSpacing(2)

        service_status_title_lbl = QLabel("Service disponible : ")
        service_status_title_lbl.setStyleSheet("font-size: 10px;")
        service_status_title_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        abo_status_title_lbl = QLabel("Abonné à la chaîne : ")
        abo_status_title_lbl.setStyleSheet("font-size: 10px;")
        abo_status_title_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        available_status_title_lbl = QLabel("Droit lié la chaîne : ")
        available_status_title_lbl.setStyleSheet("font-size: 10px;")
        available_status_title_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        service_title_layout.addWidget(service_status_title_lbl)
        service_title_layout.addWidget(abo_status_title_lbl)
        service_title_layout.addWidget(available_status_title_lbl)
        service_title_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignCenter)

        service_status_lbl = QLabel('🟢' if has_service else '🔴')
        service_status_lbl.setStyleSheet("font-size: 10px;")
        service_status_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        abo_status_lbl = QLabel('🟢' if has_abo else '🔴')
        abo_status_lbl.setStyleSheet("font-size: 10px;")
        abo_status_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        available_status_lbl = QLabel('🟢' if has_abo else '🔴')
        available_status_lbl.setStyleSheet("font-size: 10px;")
        available_status_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        service_status_layout.addWidget(service_status_lbl)
        service_status_layout.addWidget(abo_status_lbl)
        service_status_layout.addWidget(available_status_lbl)
        service_status_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignCenter)

        # Ajouter des espaces pour pousser les layouts vers les bords opposés
        service_layout.addLayout(service_title_layout)
        service_layout.addLayout(service_status_layout)
        
        layoutH.addLayout(service_layout)
        layoutV.addLayout(layoutH)
        
        program_name_lbl = QLabel(f"Nom du Programme : {program_name}")
        program_name_lbl.setStyleSheet("font-weight: bold; font-size: 14px;")
        program_name_lbl.setMinimumWidth(850)
        # program_name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignLeft)
        layoutV.addWidget(program_name_lbl)

        program_description_lbl = QLabel(program_description)
        program_description_lbl.setStyleSheet("font-size: 11px;")
        program_description_lbl.setWordWrap(True)
        program_description_lbl.setMinimumWidth(850)
        program_description_lbl.setMinimumHeight(100)
        program_description_lbl.setAlignment(Qt.AlignmentFlag.AlignBottom)
        layoutV.addWidget(program_description_lbl)

        layoutV.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        program_image_lbl = QLabel()
        program_image_lbl.setPixmap(QPixmap(ImageCache.get_pixmap(program_image_url)).scaled(240, 135, Qt.AspectRatioMode.KeepAspectRatio))
        program_image_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addLayout(layoutV)
        layout.addWidget(program_image_lbl)
        
        self.setLayout(layout)

class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
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
        with open(config_file_path, 'w') as config_file:
            json.dump(self.config, config_file, indent=4)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("App IPTV")
        self.setGeometry(100, 100, 1200, 800)
        self.centerWindow()
        
        # Réglages et configurations
        self.config = load_config()    
        self.hdhomerun_url = self.config.get("hdhomerun_url")    
        self.setup_ui()

        # Joindre le chemin du répertoire du script avec le nom du fichier image
        window_icon_path = os.path.join(application_path, "image", "missing_icon.png")
        
        # Charger l'icône de fenêtre
        window_icon = QIcon(window_icon_path)
        self.setWindowIcon(window_icon)

        # Charger l'icône de l'application (pour le gestionnaire de tâches, etc.)
        app_icon = QIcon(window_icon_path)
        QApplication.instance().setWindowIcon(app_icon)

        # Initialize VLC player
        instance = vlc.Instance()
        self.player = instance.media_player_new()
        
        # Création de l'objet de surveillance d'état VLC
        self.state_monitor = VLCStateMonitor(self.player)
        self.state_monitor.error_detected.connect(self.handle_vlc_error)
        
        # Création du QTimer pour vérifier l'état VLC périodiquement
        self.timer = QTimer()
        self.timer.timeout.connect(self.state_monitor.check_state)
        self.timer.start(1000) 
        
        # Initialisation du SemiTransparentBlurWidget mais non ajouté immédiatement
        self.semitransparent_widget = None  # Initialisé à None

        # Define the video frame
        self.videoframe = QtWidgets.QFrame()
        self.videoframe.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.videoframe.setAutoFillBackground(True)


        # Create a palette object and apply it to the video frame
        self.palette = QPalette()
        self.palette.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0))
        self.videoframe.setPalette(self.palette)
        self.videoframe.setStyleSheet("""
            * {
                color: white;
                background-color: black;
                border: none;
            }
        """
        )

        # Bind VLC to the video frame
        if sys.platform == "win32":  # Windows
            self.player.set_hwnd(self.videoframe.winId())
        elif sys.platform == "linux":  # Linux
            self.player.set_xwindow(int(self.videoframe.winId()))
        elif sys.platform == "darwin":  # MacOS
            self.player.set_nsobject(int(self.videoframe.winId()))
            
        # Initialize error label
        self.error_label = QLabel("Channel not available", self)
        self.error_label.setStyleSheet("QLabel { color : red; background-color: black; text-align: center;}")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self.videoframe)
        self.stacked_widget.addWidget(self.error_label)
        self.stacked_widget.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        
        # Définir la taille initiale de la barre latérale à zéro
        self.initial_sidebar_width = 0

        # stocker temporairement l'image capturée de la vidéo
        self.temporary_label = None 
        
        self.image = None

        self.isPlaying = True
        
        self.epg_table = None
        
        self.data_thread = None
        
        self.clock_label = None
        
        self.initUI()
        self.setupClock()

    def centerWindow(self):
        # Obtenir la taille de l'écran depuis l'application
        screen = QApplication.primaryScreen().geometry()
        windowSize = self.geometry()  # Obtient la taille de la fenêtre courante
        # Calculer la position x et y pour centrer la fenêtre
        x = int((screen.width() - windowSize.width()) / 2)
        y = int((screen.height() - windowSize.height()) / 2)
        self.setGeometry(x, y, windowSize.width(), windowSize.height())

    def setup_ui(self):
        # Bouton de configuration
        self.settings_button = QPushButton("⚙️")
        self.settings_button.clicked.connect(self.open_settings_dialog)

    def open_settings_dialog(self):
        settings_dialog = SettingsDialog(self.config, self)
        if settings_dialog.exec():
            print("Nouvelle configuration sauvegardée.")
            self.config = load_config()  # Recharger la configuration
            self.update_hdhomerun_url()

    def update_hdhomerun_url(self):
        self.hdhomerun_url = self.config.get("hdhomerun_url")
        print(f"HDHomeRun URL updated to {self.hdhomerun_url}")
        # Rafraîchissez ici tout ce qui doit l'être avec la nouvelle URL

    def show_semitransparent_blur_widget(self, channel_name, program_name, program_desc, program_picture_url, icon_path, program_start_date, program_duration, has_service, has_abo, available):
        self.remove_semibransparent_widget()
        
        # Création du widget avec les nouvelles données    
        self.semitransparent_widget = SemiTransparentBlurWidget(duration=30, channel_name=channel_name, program_name=program_name, program_desc=program_desc, program_picture_url=program_picture_url, icon_path=icon_path, program_start_date=program_start_date, program_duration=program_duration, has_service=has_service, has_abo=has_abo, available=available)
        
        # Ajout du widget au layout destiné à l'affichage d'informations
        self.info_widget_area.layout().addWidget(self.semitransparent_widget)
        self.semitransparent_widget.show()  # Assurez-vous que le widget est visible
        
        logger.debug("Widget should be visible now")  # Journalisation pour le débogage

        # Start the timer to remove the widget after duration
        QTimer.singleShot(self.semitransparent_widget.duration * 1000, self.remove_semibransparent_widget)

    def remove_semibransparent_widget(self):
        if self.epg_table is not None:
            self.remove_epg_display_widget() 
            
        if self.semitransparent_widget is not None:
            # Étape 1: Masquer le widget
            self.semitransparent_widget.hide()

            # Étape 2: Détacher le widget de tout layout parent (si attaché)
            if self.semitransparent_widget.parent() is not None:
                self.semitransparent_widget.setParent(None)
                
            # Étape 3: Supprimer tous les enfants du widget (si nécessaire)
            for child in self.semitransparent_widget.findChildren(QWidget):
                child.deleteLater()
                
            # Étape 4: Supprimer le widget
            self.semitransparent_widget.deleteLater()
            self.semitransparent_widget = None
            
            # Nettoyer le layout qui contenait le widget si nécessaire
            while self.info_widget_area.layout().count():
                item = self.info_widget_area.layout().takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

    def get_ordered_uuids(self):
        channels_list_url = 'http://mafreebox.freebox.fr/api/v8/tv/channels'
        try:
            response = requests.get(channels_list_url)
            response.raise_for_status()
            data = response.json()
            ordered_uuids = []
            channel_number = 0
            # Parcourir les chaînes et construire la liste de tuples
            for uuid, info in data['result'].items():
                channel_name = info['name']
                if channel_name.lower() in self.channels_name:
                    channel_number, icon_path = self.channels_name[channel_name.lower()]
                    # Ajouter le tuple à la liste
                    ordered_uuids.append((channel_number, channel_name, icon_path, uuid))
                if channel_name == "France 3" and channel_number != 301:
                    ordered_uuids.append(("3", channel_name, os.path.join(application_path, 'logos/France_3.png'), uuid))
                    
            ordered_uuids = sorted(ordered_uuids, key=lambda x: int(x[0]))
            return ordered_uuids
        except requests.RequestException as e:
            logger.error(f"Erreur de réseau survenue : {e}", exc_info=True)
            return []

    def handle_vlc_error(self, error_message):
        # Gestion de l'erreur VLC
        self.showError(" non disponible")
        
    def showError(self, message):
        # Récupérer le nom de la chaîne courante
        current_channel_name = getattr(self, 'current_channel_name', 'Channel Name')

        # Créer un QLabel pour afficher le logo et le nom de la chaîne
        error_layout = QVBoxLayout()
        error_label = QLabel(self)
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setStyleSheet("QLabel { font-size: 42px; font-weight: bold; color : black; background-color: grey}")
        error_label.setText(current_channel_name + message)
        
        # Charger le logo de la chaîne
        channel_logo = QLabel(self)
        sanitized_name = current_channel_name.replace(" ", "_").replace("-", "_").replace("'", "")
        logo_path = os.path.join(application_path, f'logos/{sanitized_name}.png')
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
        else:
            pixmap = QPixmap(os.path.join(application_path, 'image/missing_icon.png'))
        pixmap_resized = QPixmap(pixmap).scaled(125,125, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        channel_logo.setPixmap(pixmap_resized)
        channel_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        channel_logo.setStyleSheet("QLabel { background-color: grey}")
        
        # Ajouter les éléments au layout vertical
        error_layout.addWidget(channel_logo)
        error_layout.addWidget(error_label)
        error_widget = QWidget()
        error_widget.setLayout(error_layout)
        error_widget.setStyleSheet("QWidget { background-color: grey}")

        # Définir le widget d'erreur dans le stacked widget
        self.stacked_widget.addWidget(error_widget)
        self.stacked_widget.setCurrentWidget(error_widget)
        
        # Arrêter la lecture vidéo
        self.player.stop()
        
        # Réinitialiser le contenu du QFrame en recréant un widget vidéo
        self.initVideoFrame()

    def hideErrorMessage(self):
        self.stacked_widget.setCurrentWidget(self.videoframe)

    def initVideoFrame(self):        
        # Effacer le contenu du QFrame
        for widget in self.videoframe.findChildren(QWidget):
            widget.deleteLater()
        
        # Effacer le QFrame   
        self.videoframe.deleteLater()
        
        # Define the video frame
        self.videoframe = QtWidgets.QFrame()
        self.videoframe.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.videoframe.setAutoFillBackground(True)
        self.videoframe.setPalette(self.palette)
        
        # Bind VLC au nouveau widget vidéo
        if os.name == 'nt':  # Windows
            self.player.set_hwnd(self.videoframe.winId())
        elif os.name == 'posix':  # Linux and macOS
            self.player.set_xwindow(int(self.videoframe.winId()))

        # Ajouter le QFrame au splitter
        self.stacked_widget.addWidget(self.videoframe)

    def initUI(self):
        self.splitter = QSplitter(Qt.Orientation.Horizontal)  # Create a horizontal splitter
        
        # Create the fixed sidebar
        sidebar = QScrollArea()
        sidebar.setFixedWidth(self.initial_sidebar_width)  # Utiliser la taille initiale définie
        sidebar.setWidgetResizable(True)

        # Add channel buttons to the sidebar
        sidebar_widget = QWidget()
        sidebar_layout = QGridLayout(sidebar_widget)
        sidebar_widget.setLayout(sidebar_layout)
        sidebar.setWidget(sidebar_widget)

        self.button_layout = sidebar_layout
        
        # Ajouter un QLabel pour l'heure actuelle
        self.clock_label = QLabel("Heure actuelle: --:--")
        self.layout_widget_info = QVBoxLayout()
        self.layout_widget_info.addWidget(self.clock_label)
        self.clock_label.hide()
        
        # Zone d'information initialisée pour recevoir les widgets d'informations
        vertical_layout = QVBoxLayout()
        self.info_widget_area = QWidget()
        self.info_widget_area.setLayout(QVBoxLayout())
        vertical_layout.addWidget(self.stacked_widget, 1000)
        self.layout_widget_info.addWidget(self.info_widget_area)
        vertical_layout.addLayout(self.layout_widget_info, 1) 
        
        # Create a container widget and set the vertical layout
        self.container_widget = QWidget()
        self.container_widget.setLayout(vertical_layout)   
        
        self.splitter.addWidget(sidebar)  # Add the sidebar to the splitter
        self.splitter.addWidget(self.container_widget)  # Add the video frame to the splitter

        # Set initial size proportion
        self.splitter.setSizes([300, 900])
        self.initial_sidebar_width = 300

        # Set initial size proportion
        self.splitter.setSizes([self.initial_sidebar_width, 900])  # Utiliser la taille initiale définie
        
        self.central_widget = QWidget()

        self.central_widget.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.central_widget.installEventFilter(self)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.splitter)
        self.central_widget.setLayout(main_layout)
        self.setCentralWidget(self.central_widget)
        
        # Initialisation de la détection
        self.hover_enabled = True
        
        # Initialisation d'un QTimer pour désactiver temporairement la détection de survol
        self.hover_timer = QTimer(self)
        self.hover_timer.setSingleShot(True)
        self.hover_timer.timeout.connect(self.enable_hover_detection)  # Réactiver la détection de survol après le délai
        
        # Initialiser les animations
        self.show_sidebar_animation = QPropertyAnimation(self.splitter.widget(0), b'maximumWidth')
        self.show_sidebar_animation.setDuration(100)  # Durée de l'animation en millisecondes (1 seconde)
        self.show_sidebar_animation.setStartValue(0)
        self.show_sidebar_animation.setEndValue(self.initial_sidebar_width)
        self.show_sidebar_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)  # Courbe d'accélération pour une transition en douceur

        self.hide_sidebar_animation = QPropertyAnimation(self.splitter.widget(0), b'maximumWidth')
        self.hide_sidebar_animation.setDuration(1000)  # Durée de l'animation en millisecondes (1 seconde)
        self.hide_sidebar_animation.setStartValue(self.splitter.widget(0).maximumWidth())
        self.hide_sidebar_animation.setEndValue(0)
        self.hide_sidebar_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)  # Courbe d'accélération pour une transition en douceur

        # S'assurer que le widget de la barre latérale peut être réduit à une largeur minimale de zéro
        self.splitter.widget(0).setMinimumWidth(0)
        
        # Création des boutons pour le contrôle des vues
        self.current_program_button = QtWidgets.QPushButton("Programme Actuel")
        self.all_programs_button = QtWidgets.QPushButton("Programme Complet pour Toutes les Chaînes")

        # Connecter les boutons à leurs méthodes respectives
        self.current_channel_name = None
        self.current_program_button.clicked.connect(lambda checked: self.get_uuid_of_current_channel(self.current_channel_name))
        self.all_programs_button.clicked.connect(self.toggle_epg_display)
        
        control_layout = QHBoxLayout()
        
        # Bouton Play/Pause
        self.playPauseButton = QtWidgets.QPushButton("▶️")
        self.playPauseButton.setEnabled(False)
        self.playPauseButton.clicked.connect(self.togglePlayPause)
        
        self.volume_label = QLabel()
        self.volume_label.setText('Volume')
        self.volumeSlider = QtWidgets.QSlider(Qt.Orientation.Horizontal, self)
        self.volumeSlider.setMaximum(100)  # Le volume est généralement entre 0 et 100
        self.player.audio_set_volume(80)
        self.volumeSlider.setValue(self.player.audio_get_volume())
        self.volumeSlider.valueChanged.connect(self.changeVolume)
        
        # Ajouter les controleur de lecture à la fenêtre principale
        control_layout.addWidget(self.playPauseButton)
        control_layout.addWidget(self.volume_label) 
        control_layout.addWidget(self.volumeSlider) 
        control_layout.addWidget(self.settings_button) 
        main_layout.addLayout(control_layout) 

        # Ajouter les boutons à un layout horizontal
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.current_program_button)
        button_layout.addWidget(self.all_programs_button)

        # Ajouter le layout de boutons à la fenêtre principale
        main_layout.addLayout(button_layout) 
        
        # Load the playlists
        self.loadPlaylists()
        self.ordered_uuids = self.get_ordered_uuids()

    # Pour afficher et masquer la grille EPG
    def toggle_epg_display(self):
        if self.epg_table:
            self.remove_epg_display_widget()
        else:
            self.remove_semibransparent_widget()
            self.add_epg_display_widget()
            self.epg_table.show()

    def is_widget_in_layout(self, layout, widget):
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item.widget() == widget:
                return True
        return False
            
    def add_epg_display_widget(self):
        if self.epg_table is None:
            self.epg_table = EPGTable(self)
            self.data_thread = DataLoadThread(self.ordered_uuids)
            self.data_thread.data_loaded.connect(self.epg_table.populate_table_with_ordered_info)
            self.data_thread.start()

        if not self.is_widget_in_layout(self.info_widget_area.layout(), self.epg_table):
            self.layout_widget_info.addWidget(self.epg_table)
        
        # self.update_epg_order()
        self.epg_table.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.epg_table.setMinimumHeight(800)
        self.clock_label.show()
        self.epg_table.show()
        logger.debug(f"EPG Table added, is visible: {self.epg_table.isVisible()} with dimensions: {self.epg_table.size()}")

    def setupClock(self):
        # Timer pour mettre à jour l'heure chaque minute
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateClock)
        self.timer.start(1000)

    def updateClock(self):
        # Obtenir l'heure actuelle et la formater
        now = datetime.datetime.now()
        formatted_time = now.strftime('%d/%m/%Y - %H:%M:%S')
        self.clock_label.setText("Heure actuelle: " + formatted_time)

    def remove_epg_display_widget(self):
        if self.epg_table is not None:
            # Étape 1: Masquer le widget
            self.epg_table.hide()
            self.clock_label.hide()

            # Étape 2: Détacher le widget de tout layout parent (si attaché)
            if self.epg_table.parent() is not None:
                self.epg_table.setParent(None)
                
            # Étape 3: Supprimer tous les enfants du widget (si nécessaire)
            for child in self.epg_table.findChildren(QWidget):
                child.deleteLater()
                
            # Étape 4: Supprimer le widget
            self.epg_table.deleteLater()
            self.epg_table = None

    def togglePlayPause(self):
        if self.isPlaying:
            self.player.pause()
            self.playPauseButton.setText("▶")
            self.playPauseButton.setStyleSheet("QPushButton { color: green; }")
            self.showError(" Chaîne en Arrêt")
        else:
            self.player.play()
            self.playPauseButton.setText("■")
            self.playPauseButton.setStyleSheet("QPushButton { color: red; }")
            self.hideErrorMessage()  # Masquer l'erreur lors de la reprise de la lecture
        self.isPlaying = not self.isPlaying

    def changeVolume(self, value):
        self.player.audio_set_volume(value)

    def createProgramWidget(self, program_info):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        title = QtWidgets.QLabel(program_info.get('title', 'Unknown Title'))
        desc = QtWidgets.QLabel(program_info.get('desc', 'No Description Available'))
        layout.addWidget(title)
        layout.addWidget(desc)
        return widget
    
    def disable_hover_detection(self):
        self.hover_enabled = False

    def enable_hover_detection(self):
        self.hover_enabled = True

    def adjust_sidebar_width_on_hover(self, show):
        # Ajuster la taille de la colonne du splitter pour faire apparaître/disparaître la barre latérale
        if show:  # Si la barre latérale est caché
            self.show_sidebar_animation.start()
        else:  # Si la barre latérale est visible
            self.hide_sidebar_animation.start()
        # Mettre à jour le dernier état de survol
        self.last_hover_state = show

    def eventFilter(self, obj, event):
        if obj is self.central_widget:
            if event.type() == QEvent.Type.Enter and self.hover_enabled:
                self.adjust_sidebar_width_on_hover(True)
            elif event.type() == QEvent.Type.Leave:
                self.adjust_sidebar_width_on_hover(False)
                self.disable_hover_detection()  # Désactiver temporairement la détection de survol
                self.hover_timer.start(200)  # Délai d'une seconde avant de réactiver la détection de survol
        return super().eventFilter(obj, event)

    def loadPlaylists(self):
        freebox_channels = self.loadFreeboxPlaylist()
        hdhomerun_channels = self.loadHDHomeRunPlaylist()

        # Merge channels while giving preference to Freebox channels and adding unique HDHomeRun channels
        merged_channels = freebox_channels.copy()
        
        for channel, url in hdhomerun_channels.items():
            channel_number = channel.split(" - ")[0]
            # Gérer spécifiquement la chaîne numéro 3
            if channel_number == '3':
                merged_channels["3 - France 3"] = url
            else:
                # Vérifiez si ce numéro de chaîne n'existe pas déjà dans les chaînes freebox
                if not any(c.split(" - ")[0] == channel_number for c in freebox_channels.keys()):
                    merged_channels[channel] = url

        self.displayChannels(merged_channels)
    
    def mouseMoveEvent(self, event):
        # Mettre à jour la position de la souris à chaque mouvement
        self.last_mouse_position = event.globalPosition().toPoint()
        super().mouseMoveEvent(event)
    
    def check_hover_status(self):
        # Vérifier si le survol est toujours désactivé après 1 seconde
        if not self.is_hovered:
            self.mouse_position_timer.stop()
            logger.debug("Attendre avant de redétecter le survol")
    
    def displayChannels(self, channels):
        row, col = 0, 0
        self.channels_name = {}
        for name, url in sorted(channels.items(), key=lambda x: int(x[0].split(" - ")[0])):
            channel_number = name.split(' - ')[0]
            channel_name = ' - '.join(name.split(" - ")[1:])
            tool_button = QToolButton()
            tool_button.setText(channel_name)
            tool_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            tool_button.setIconSize(QSize(50, 50))
            tool_button.setFixedSize(80, 80)
            tool_button.clicked.connect(lambda checked, url=url, name=name: self.playStream(url, ' - '.join(name.split(" - ")[1:])))
            
            icon_path = self.get_channel_icon(name)
            if icon_path:
                tool_button.setIcon(QIcon(icon_path))
                self.channels_name[channel_name.lower()] = channel_number, icon_path
                
            channel_name = ' - '.join(name.split(" - ")[1:]).replace(' ', '_').replace('-', '_').replace('\'', '')
            
            self.button_layout.addWidget(tool_button, row, col)
            
            col += 1
            if col > 2:  # Three buttons per row
                col = 0
                row += 1

    def get_channel_icon(self, channel_name):
        parts = channel_name.split(' - ')
        if len(parts) < 2:
            parts = channel_name.split(' ')
            if len(parts) >= 2:
                parts.pop(0)  # Remove the first element
                channel_name = ' '.join(parts)
        else:
            channel_name = channel_name.split(' - ')[1]
            
        sanitized_name = channel_name.replace(" ", "_").replace("-", "_").replace("'", "")
        icon_formats = ['svg', 'png']
        for fmt in icon_formats:
            icon_path = os.path.join(application_path, 'logos', f'{sanitized_name}.{fmt}')
            if os.path.exists(icon_path):
                return icon_path

        # Fallback to a generic icon
        return os.path.join(application_path, 'image/missing_icon.png')

    def playStream(self, url, name):
        try:
            # Arrêter la lecture vidéo actuelle
            self.player.stop()

            # Définir le nouvel emplacement média sans créer de nouvelle instance de lecteur multimédia
            self.player.set_mrl(url)
            
            # Lancer la lecture
            self.player.play()
            self.playPauseButton.setEnabled(True)
            self.playPauseButton.setText("■")
            self.playPauseButton.setStyleSheet("QPushButton { color: red; }")

            # Afficher le nom de la chaîne
            self.current_channel_name = name
            
            # Masquer l'étiquette d'erreur
            self.hideErrorMessage()
            
            # Afficher l'EPG
            self.get_uuid_of_current_channel(name)
            
        except Exception as e:
            logger.error(f"Erreur lors de la lecture du flux : {str(e)}", exc_info=True)
            self.showError(" non disponible")

    def loadFreeboxPlaylist(self):
        playlist_url = "http://mafreebox.freebox.fr/freeboxtv/playlist.m3u"
        try:
            response = requests.get(playlist_url, timeout=10)
            response.raise_for_status()  # This will raise an exception for 4XX/5XX status codes
            return self.filter_freebox_playlist(response.text.splitlines())
        except requests.RequestException as e:
            logger.error(f"Erreur de réseau survenue : {e}", exc_info=True)
            return {}

    def loadHDHomeRunPlaylist(self):
        hdhomerun_url = self.hdhomerun_url
        
        try:
            response = requests.get(hdhomerun_url, timeout=10)
            response.raise_for_status()
            try:
                text = response.content.decode('utf-8')
            except UnicodeDecodeError:
                text = response.content.decode('iso-8859-1')
            return self.filter_hdhomerun_playlist(text.splitlines())
        except requests.RequestException as e:
            logger.error(f"Erreur de réseau survenue : {e}", exc_info=True)
            return {}

    def filter_freebox_playlist(self, playlist_lines):
        channels = {}

        for i, line in enumerate(playlist_lines):
            if line.startswith("#EXTINF:"):
                info = line.strip()
                if i + 1 < len(playlist_lines):
                    url = playlist_lines[i + 1].strip()
                else:
                    continue

                # Extract the channel information
                parts = info.split(",", 1)
                if len(parts) < 2:
                    continue
                channel_info = parts[1]
                number_name = channel_info.rsplit("(", 1)
                channel_name = number_name[0].strip()
                quality = number_name[1][:-1].strip() if len(number_name) > 1 else "standard"  # Default to "standard"

                # Initialize the dictionary entry for the channel name if it doesn't exist
                if channel_name not in channels:
                    channels[channel_name] = {"HD": None, "standard": None, "bas débit": None}

                # Assign URL to the appropriate quality category
                if quality in channels[channel_name]:
                    channels[channel_name][quality] = url

        filtered_channels = {}
        for name, qualities in channels.items():
            # Pick the best quality available
            url = qualities["HD"] or qualities["standard"] or qualities["bas débit"]
            if url:
                filtered_channels[name] = url

        return filtered_channels
    
    def filter_hdhomerun_playlist(self, playlist_lines):
        channels = {}

        for i, line in enumerate(playlist_lines):
            if line.startswith("#EXTINF:"):
                info = line.strip()
                if i + 1 < len(playlist_lines):
                    url = playlist_lines[i + 1].strip()
                else:
                    continue

                # Extract the channel information
                parts = info.split(",", 1)
                if len(parts) < 2:
                    continue
                channel_info = parts[1]
                # Format the channel name to match Freebox's style
                parts = channel_info.split(" ", 1)
                channel_number = parts[0]
                channel_name = parts[1] if len(parts) > 1 else "Unknown"
                formatted_name = f"{channel_number} - {channel_name}"

                # Store the URL for this formatted channel name
                channels[formatted_name] = url

        return channels

    def get_default_program_details(self):
        return "Programme non disponible", "Description non disponible", "https://leseng.rosselcdn.net/sites/default/files/dpistyles_v2/ls_16_9_864w/2023/04/24/node_509239/30068567/public/2023/04/24/b9733237119z.1_20230119131757_000%2Bgrsm2a085.1-0.jpeg", int(time.time()), 3600

    def get_uuid_of_current_channel(self, channel_name):       
        # Obtenez le JSON depuis l'API de la Freebox
        channels_list_url = 'http://mafreebox.freebox.fr/api/v8/tv/channels'
        try:
            response = requests.get(channels_list_url)#, timeout=60)
            response.raise_for_status()  # Lever une exception pour les codes de statut 4XX/5XX
            data = response.json()
        except requests.RequestException as e:
            logger.error(f"Erreur de réseau survenue : {e}", exc_info=True)
            return {}  # Retourner un dictionnaire vide ou une valeur par défaut
        find = False
        for uuid, channel_info in data['result'].items():
            print("channel_info['name'] :", channel_info['name'])
            print("channel_name :", channel_name)
            if channel_name == channel_info['name'][:14] or channel_name == channel_info['name']:
                find = True
                program_name, program_desc, program_picture_url, program_start_date, program_duration = self.get_current_program(uuid)
                sanitized_name = channel_name.replace(" ", "_").replace("-", "_").replace("'", "")
                icon_path = os.path.join(application_path, 'logos', f'{sanitized_name}.png')
                if not icon_path:
                    icon_path = os.path.join(application_path, 'image/missing_icon.png')
                has_service = channel_info.get('has_service', False)  # Par défaut False si non spécifié
                has_abo = channel_info.get('has_abo', False)  # Par défaut False si non spécifié
                available = channel_info.get('available', False)  # Par défaut False si non spécifié
                if channel_name == 'TF1 Séries Fil':
                    channel_name += 'm'
                if program_name:
                    logger.debug(f"Programme actuel sur la chaîne : {program_name}")
                    logger.debug(f"Description : {program_desc}")
                    logger.debug(f"URL de l'image du programme : {program_picture_url}")
                    logger.debug(f"Service disponible : {'Oui' if has_service else 'Non'}")
                    logger.debug(f"Abonné à la chaine : {'Oui' if has_abo else 'Non'}")
                    logger.debug(f"Chaine disponible: {'Oui' if available else 'Non'}")
                else:
                    logger.debug("Aucun programme actuel trouvé pour cette chaîne.")

                logger.debug(f"Chemin d'accès au Logo : {icon_path}")
                logger.debug(f"Heure de début du programme : {program_start_date}")
                logger.debug(f"Durée du programme : {program_duration}")
                
                self.show_semitransparent_blur_widget(channel_name, program_name, program_desc, program_picture_url, icon_path, program_start_date, program_duration, has_service, has_abo, available)
        if not find:
            program_name, program_desc, program_picture_url, program_start_date, program_duration = self.get_default_program_details()
            icon_path = os.path.join(application_path, 'image/missing_icon.png')
            self.show_semitransparent_blur_widget(channel_name, program_name, program_desc, program_picture_url, icon_path, program_start_date, program_duration, False, False, False)
                
    # Fonction pour récupérer les informations sur le programme actuel d'une chaîne
    def get_current_program(self, channel_uuid):
        default_program_name, default_program_desc, default_picture_url, default_program_start_date, default_program_duration = self.get_default_program_details()

        epoch_time = int(time.time())
        logger.debug(f"Epoch Time: {epoch_time}")
        epg_url = f'http://mafreebox.freebox.fr/api/v8/tv/epg/by_channel/{channel_uuid}/{epoch_time}'
        logger.debug(f"epg_url : {epg_url}")
        try:
            epg_response = requests.get(epg_url, timeout=30)
            epg_response.raise_for_status()
            epg_data = epg_response.json()
            programs = epg_data.get('result', {})
        except requests.RequestException as e:
            logger.error(f"Erreur lors de la récupération de l'EPG: {e}", exc_info=True)
            return default_program_name, default_program_desc, default_picture_url, default_program_start_date, default_program_duration

        sorted_keys = sorted(programs.keys(), key=lambda x: int(x.split('_')[-1]) if x.split('_')[-1].isdigit() else int(x.split('_')[0]))
        actual_program = None
        program_start_date = default_program_start_date
        
        for key in sorted_keys:
            key_parts = key.split('_')
            if key.startswith('fake'):
                key_int = int(key_parts[-1])
            else:
                key_int = int(key_parts[0])
            if epoch_time >= key_int:
                actual_program = programs[key]
                program_start_date = key_int
            else:
                break
            
        if actual_program:
            program_name = actual_program.get('title', default_program_name)
            program_desc = actual_program.get('desc', default_program_desc)
            program_picture_url = f"http://mafreebox.freebox.fr{actual_program['picture_big']}" if 'picture_big' in actual_program else default_picture_url
            program_duration = int(actual_program.get('duration', default_program_duration))
        else:
            program_name, program_desc, program_picture_url, program_duration = default_program_name, default_program_desc, default_picture_url, default_program_duration

        return program_name, program_desc, program_picture_url, program_start_date, program_duration

class CustomSplashScreen(QSplashScreen):
    def __init__(self, pixmap, *args, **kwargs):
        super(CustomSplashScreen, self).__init__(pixmap, *args, **kwargs)
        self.progressBar = QProgressBar(self)
        self.progressBar.setGeometry(100, 350, 500, 20)  # Ajuster la position et la taille

    def setProgress(self, value):
        self.progressBar.setValue(value)
        QApplication.instance().processEvents()

def main():
    app = QApplication(sys.argv)
    # Application du thème sombre
    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
    
    splash_pix = QPixmap(os.path.join(application_path, './image/splash_screen.png'))
    splash = CustomSplashScreen(splash_pix)
    splash.show()

    # Simuler le chargement de l'application
    for i in range(1, 101):
        splash.setProgress(i)
        time.sleep(0.03)  # Simuler le temps de chargement

    mainWindow = MainWindow()  # Supposons que vous avez une fenêtre principale
    mainWindow.show()
    splash.finish(mainWindow)

    sys.exit(app.exec())

if __name__ == '__main__':
    if platform.system() == "Linux":
        os.environ["QT_QPA_PLATFORM"] = "xcb"
    main()