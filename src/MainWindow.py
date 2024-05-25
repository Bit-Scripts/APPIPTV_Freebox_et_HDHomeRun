import re
import sys
import os
import requests
import time
from unidecode import unidecode
import datetime
from PyQt6 import QtWidgets
from PyQt6.QtGui import QPixmap, QColor, QPalette, QIcon
from PyQt6.QtCore import Qt, QSize, QEvent, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtWidgets import QPushButton, QApplication, QMainWindow, QStackedWidget, QVBoxLayout, QScrollArea, QWidget, QGridLayout, QToolButton, QSplitter, QHBoxLayout, QLabel
import vlc
from src.VLCStateMonitor import VLCStateMonitor
from src.SettingsDialog import SettingsDialog
from src.SemiTransparentBlurWidget import SemiTransparentBlurWidget
from src.EPGTable import EPGTable
from src.DataLoadThread import DataLoadThread

class MainWindow(QMainWindow):
    def __init__(self, config, config_file_path, config_path, logger, application_path):
        super().__init__()
        self.logger = logger
        self.application_path = application_path

        self.setWindowTitle("App IPTV")
        self.setGeometry(100, 100, 1200, 800)
        self.centerWindow()
        
        # Réglages et configurations
        self.config_path = config_path
        self.config_file_path = config_file_path
        self.config = config
        self.hdhomerun_url = self.config.get("hdhomerun_url")    
        self.setup_ui()

        # Joindre le chemin du répertoire du script avec le nom du fichier image
        window_icon_path = os.path.join(self.application_path, "assets", "image", "missing_icon.png")
        
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
        settings_dialog = SettingsDialog(self.config_file_path, self.config, self)
        if settings_dialog.exec():
            print("Nouvelle configuration sauvegardée.")
            self.update_hdhomerun_url()

    def update_hdhomerun_url(self):
        self.hdhomerun_url = self.config.get("hdhomerun_url")
        print(f"HDHomeRun URL updated to {self.hdhomerun_url}")
        # Rafraîchissez ici tout ce qui doit l'être avec la nouvelle URL

    def show_semitransparent_blur_widget(self, channel_name, program_name, program_desc, program_picture_url, icon_path, program_start_date, program_duration, has_service, has_abo, available):
        self.remove_semibransparent_widget()
        
        # Création du widget avec les nouvelles données    
        self.semitransparent_widget = SemiTransparentBlurWidget(self.logger, duration=30, channel_name=channel_name, program_name=program_name, program_desc=program_desc, program_picture_url=program_picture_url, icon_path=icon_path, program_start_date=program_start_date, program_duration=program_duration, has_service=has_service, has_abo=has_abo, available=available)
        
        # Ajout du widget au layout destiné à l'affichage d'informations
        self.info_widget_area.layout().addWidget(self.semitransparent_widget)
        self.semitransparent_widget.show()  # Assurez-vous que le widget est visible
        self.semitransparent_widget.show()  # Assurez-vous que le widget est visible
        
        self.logger.debug("Widget should be visible now")  # Journalisation pour le débogage

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
                if channel_name.lower() == "france 3" and channel_number != 301:
                    ordered_uuids.append(("3", channel_name, os.path.join(self.application_path, 'assets/logos/France_3.png'), uuid))
                    
            ordered_uuids = sorted(ordered_uuids, key=lambda x: int(x[0]))
            return ordered_uuids
        except requests.RequestException as e:
            self.logger.error(f"Erreur de réseau survenue : {e}", exc_info=True)
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
        sanitized_name = unidecode(current_channel_name.lower()).replace(' ', '_').replace('-', '_').replace("'", '').replace("/","-")
        logo_path = os.path.join(self.application_path, f'assets/logos/{sanitized_name}.png')
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
        else:
            pixmap = QPixmap(os.path.join(self.application_path, 'assets/image/missing_icon.png'))
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
            self.epg_table = EPGTable(self, self.logger)
            self.data_thread = DataLoadThread(self.ordered_uuids, self.logger, self.application_path)
            self.data_thread.data_loaded.connect(self.epg_table.populate_table_with_ordered_info)
            self.data_thread.start()

        if not self.is_widget_in_layout(self.info_widget_area.layout(), self.epg_table):
            self.layout_widget_info.addWidget(self.epg_table)
        
        # self.update_epg_order()
        self.epg_table.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.epg_table.setMinimumHeight(800)
        self.clock_label.show()
        self.epg_table.show()
        self.logger.debug(f"EPG Table added, is visible: {self.epg_table.isVisible()} with dimensions: {self.epg_table.size()}")

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
            self.logger.debug("Attendre avant de redétecter le survol")

    def get_channel_number(self, name):
        match = re.match(r'^(\d+)', name)
        return int(match.group(1)) if match else None

    def displayChannels(self, channels):
        row, col = 0, 0
        self.channels_name = {}

        def get_sort_key(name):
            channel_number = self.get_channel_number(name)
            return channel_number if channel_number is not None else float('inf')

        for name, url in sorted(channels.items(), key=lambda x: get_sort_key(x[0])):
            channel_number = self.get_channel_number(name)
            if channel_number is None:
                continue

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

    def extract_channel_number(self, channel_name):
        try:
            return int(channel_name.split(" - ")[0])
        except ValueError:
            return float('inf') 

    def get_channel_icon(self, channel_name):
        parts = channel_name.split(' - ')
        if len(parts) < 2:
            parts = channel_name.split(' ')
            if len(parts) >= 2:
                parts.pop(0)  # Remove the first element
                channel_name = ' '.join(parts)
        else:
            channel_name = channel_name.split(' - ')[1]
            
        sanitized_name = unidecode(channel_name.lower()).replace(" ", "_").replace("-", "_").replace("'", "")
        icon_formats = ['svg', 'png']
        for fmt in icon_formats:
            icon_path = os.path.join(self.application_path, 'assets', 'logos', f'{sanitized_name}.{fmt}')
            if os.path.exists(icon_path):
                return icon_path

        # Fallback to a generic icon
        return os.path.join(self.application_path, 'assets/image/missing_icon.png')

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
            self.logger.error(f"Erreur lors de la lecture du flux : {str(e)}", exc_info=True)
            self.showError(" non disponible")

    def loadFreeboxPlaylist(self):
        playlist_url = "http://mafreebox.freebox.fr/freeboxtv/playlist.m3u"
        try:
            response = requests.get(playlist_url, timeout=10)
            response.raise_for_status()  # This will raise an exception for 4XX/5XX status codes
            return self.filter_freebox_playlist(response.text.splitlines())
        except requests.RequestException as e:
            self.logger.error(f"Erreur de réseau survenue : {e}", exc_info=True)
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
            self.logger.error(f"Erreur de réseau survenue : {e}", exc_info=True)
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
            self.logger.error(f"Erreur de réseau survenue : {e}", exc_info=True)
            return {}  # Retourner un dictionnaire vide ou une valeur par défaut
        find = False
        for uuid, channel_info in data['result'].items():
            print("channel_info['name'] :", channel_info['name'])
            print("channel_name :", channel_name)
            if channel_name == channel_info['name'][:14] or channel_name == channel_info['name']:
                find = True
                program_name, program_desc, program_picture_url, program_start_date, program_duration = self.get_current_program(uuid)
                sanitized_name = unidecode(channel_name.lower()).replace(" ", "_").replace("-", "_").replace("'", "")
                icon_path = os.path.join(self.application_path, 'assets', 'logos', f'{sanitized_name}.png')
                if not icon_path:
                    icon_path = os.path.join(self.application_path, 'assets/image/missing_icon.png')
                has_service = channel_info.get('has_service', False)  # Par défaut False si non spécifié
                has_abo = channel_info.get('has_abo', False)  # Par défaut False si non spécifié
                available = channel_info.get('available', False)  # Par défaut False si non spécifié
                if channel_name == 'TF1 Séries Fil':
                    channel_name += 'm'
                if program_name:
                    self.logger.debug(f"Programme actuel sur la chaîne : {program_name}")
                    self.logger.debug(f"Description : {program_desc}")
                    self.logger.debug(f"URL de l'image du programme : {program_picture_url}")
                    self.logger.debug(f"Service disponible : {'Oui' if has_service else 'Non'}")
                    self.logger.debug(f"Abonné à la chaine : {'Oui' if has_abo else 'Non'}")
                    self.logger.debug(f"Chaine disponible: {'Oui' if available else 'Non'}")
                else:
                    self.logger.debug("Aucun programme actuel trouvé pour cette chaîne.")

                self.logger.debug(f"Chemin d'accès au Logo : {icon_path}")
                self.logger.debug(f"Heure de début du programme : {program_start_date}")
                self.logger.debug(f"Durée du programme : {program_duration}")
                
                self.show_semitransparent_blur_widget(channel_name, program_name, program_desc, program_picture_url, icon_path, program_start_date, program_duration, has_service, has_abo, available)
        if not find:
            program_name, program_desc, program_picture_url, program_start_date, program_duration = self.get_default_program_details()
            icon_path = os.path.join(self.application_path, 'assets/image/missing_icon.png')
            self.show_semitransparent_blur_widget(channel_name, program_name, program_desc, program_picture_url, icon_path, program_start_date, program_duration, False, False, False)
                
    # Fonction pour récupérer les informations sur le programme actuel d'une chaîne
    def get_current_program(self, channel_uuid):
        default_program_name, default_program_desc, default_picture_url, default_program_start_date, default_program_duration = self.get_default_program_details()

        epoch_time = int(time.time())
        self.logger.debug(f"Epoch Time: {epoch_time}")
        epg_url = f'http://mafreebox.freebox.fr/api/v8/tv/epg/by_channel/{channel_uuid}/{epoch_time}'
        self.logger.debug(f"epg_url : {epg_url}")
        try:
            epg_response = requests.get(epg_url, timeout=30)
            epg_response.raise_for_status()
            epg_data = epg_response.json()
            programs = epg_data.get('result', {})
        except requests.RequestException as e:
            self.logger.error(f"Erreur lors de la récupération de l'EPG: {e}", exc_info=True)
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