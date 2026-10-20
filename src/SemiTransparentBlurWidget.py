import datetime
from PyQt6 import QtWidgets
from PyQt6.QtGui import QPixmap, QColor, QPainter
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
import pytz
from src.ImageCache import ImageCache

class SemiTransparentBlurWidget(QWidget):
    def __init__(self, logger, duration=30, channel_name=None, program_name=None, program_desc=None, program_picture_url=None, icon_path=None, program_start_date=None, program_duration=None, has_service=None, has_abo=None, available=None):
        super().__init__()
        self.logger = logger
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self.setMinimumWidth(0)
        self.setMinimumHeight(200)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 0);")  # Fond complètement transparent
        self.duration = duration

        self.setupUI(icon_path, channel_name, program_name, program_desc, program_picture_url, program_start_date, program_duration, has_service, has_abo, available)
        
        
    def paintEvent(self, event):
        painter = QPainter(self)
        if painter.isActive():
            painter.setBrush(QColor(0, 0, 0, 150))
            painter.drawRect(self.rect())
        else:
            self.logger.debug("Painter is not active")

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
        self.logger.debug(f"Heure de début : {start_date_fr}")
        duration_fr = self.seconds_to_duration(program_duration)
        self.logger.debug(f"Durée : {duration_fr}")
        end_date_fr = self.epoch_to_localtime_french(program_start_date + program_duration)
        self.logger.debug(f"Heure de Fin : {end_date_fr}")
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
        available_status_lbl = QLabel('🟢' if available else '🔴')
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
        program_name_lbl.setWordWrap(True)
        # program_name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignLeft)
        layoutV.addWidget(program_name_lbl)

        program_description_lbl = QLabel(program_description)
        program_description_lbl.setStyleSheet("font-size: 11px;")
        program_description_lbl.setWordWrap(True)
        program_description_lbl.setMinimumWidth(0)
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
        for label in (channel_name_lbl, program_name_lbl, program_description_lbl):
            label.setTextFormat(Qt.TextFormat.PlainText)
            label.setWordWrap(True)
            label.setMinimumWidth(0)
            label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored,
                                QtWidgets.QSizePolicy.Policy.Preferred)
