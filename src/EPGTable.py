import datetime
import os
from PyQt6 import QtWidgets
from PyQt6.QtGui import QPixmap, QColor
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTableWidgetItem, QLabel
import pytz

class EPGTable(QtWidgets.QTableWidget):
    def __init__(self, logger, application_path, parent=None):
        super().__init__(parent)
        self.logger = logger
        self.application_path = application_path
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
        self.logger.debug(f"Chargement de la chaîne avec UUID: {channel_uuid}")
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
            self.logger.error(f"Missing channel information for program {program_details.get('title', 'Unknown')} on channel {channel_uuid}")
            return None

    def create_channel_widget(self, channel_number, channel_name, channel_icon_url):
        logo_item = QtWidgets.QLabel()
        logo_pixmap = QPixmap(channel_icon_url)

        if logo_pixmap.isNull():
            self.logger.error(f"Failed to load image from {channel_icon_url}")
            logo_pixmap = QPixmap(os.path.join(self.application_path, 'assets/image/missing_icon.png'))  # Chemin vers une image par défaut
        
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