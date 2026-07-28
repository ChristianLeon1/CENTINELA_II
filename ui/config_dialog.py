import sys
from pathlib import Path

from PySide6.QtCore import QObject, Qt, QUrl, Slot
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from core.config_manager import load_config, save_config
from ui.theme import PALETTE
from ui.widgets.panel_visor_3d import PanelVisor3D

BASE_DIR = Path(__file__).resolve().parent.parent


class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CENTINELA I - Pre-Flight Check & Configuration")
        self.setFixedSize(1000, 700)
        self.config_data = load_config()

        self._last_known_ports = []

        self.setStyleSheet(
            f"""
            QDialog {{ 
                background-color: {PALETTE['BACKGROUND']['MAIN']}; 
                color: {PALETTE['TEXT']['PRIMARY']}; 
            }}
            QLabel {{ 
                color: {PALETTE['TEXT']['PRIMARY']}; 
                font-family: 'Gotham'; 
            }}
            QFrame[isQuadrant="true"] {{ 
                background-color: {PALETTE['BACKGROUND']['PANEL']}; 
                border: 1px solid {PALETTE['BORDER']['DEFAULT']}; 
                border-radius: 8px; 
            }}
            QPushButton {{ 
                background-color: {PALETTE['ACCENT']['ACTIVE']}; 
                color: {PALETTE['BACKGROUND']['MAIN']}; 
                border-radius: 4px; 
                padding: 10px; 
                font-weight: bold;
            }}
            QPushButton:hover {{ 
                background-color: {PALETTE['ACCENT']['HOVER']}; 
            }}
            QPlainTextEdit {{ 
                background-color: {PALETTE['BACKGROUND']['MAIN']}; 
                border: 1px solid {PALETTE['BORDER']['DEFAULT']}; 
                color: {PALETTE['STATUS']['SUCCESS']}; 
                font-family: 'Monospace'; 
                font-size: 9pt;
            }}
            QLineEdit, QComboBox, QDoubleSpinBox {{
                background-color: {PALETTE['BACKGROUND']['MAIN']}; 
                border: 1px solid {PALETTE['BORDER']['DEFAULT']}; 
                color: {PALETTE['TEXT']['PRIMARY']}; 
                padding: 5px; 
                border-radius: 4px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
        """
        )
        main_layout = QGridLayout(self)
        main_layout.setSpacing(15)

        # ---------------------------------------------------------
        # CUADRANTE 1: CONFIGURACIÓN 3D (REDISEÑADO CON MAPEOS)
        # ---------------------------------------------------------
        q1 = QFrame()
        q1.setProperty("isQuadrant", True)
        lay1 = QVBoxLayout(q1)
        lay1.addWidget(QLabel("<b><i class='fa fa-cube'></i> CONFIGURACIÓN 3D</b>"))

        grid_3d = QGridLayout()
        grid_3d.setSpacing(10)

        # Encabezados
        grid_3d.addWidget(QLabel("<b>Sensor</b>"), 0, 0)
        grid_3d.addWidget(QLabel("<b>Mapear a</b>"), 0, 1)
        grid_3d.addWidget(QLabel("<b>Offset (°)</b>"), 0, 2)
        grid_3d.addWidget(QLabel("<b>Invertir</b>"), 0, 3)

        # Fila PITCH
        grid_3d.addWidget(QLabel("Pitch:"), 1, 0)
        self.cb_map_p = QComboBox()
        self.cb_map_p.addItems(["X", "Y", "Z"])
        self.cb_map_p.setCurrentText(self.config_data.get("map_pitch", "X"))
        grid_3d.addWidget(self.cb_map_p, 1, 1)

        self.sp_p = QDoubleSpinBox()
        self.sp_p.setRange(-360, 360)
        self.sp_p.setSingleStep(5)
        self.sp_p.setValue(self.config_data.get("offset_pitch", 0))
        grid_3d.addWidget(self.sp_p, 1, 2)

        self.chk_inv_p = QCheckBox("Inv.")
        self.chk_inv_p.setChecked(self.config_data.get("invert_pitch", False))
        grid_3d.addWidget(self.chk_inv_p, 1, 3)

        # Fila ROLL
        grid_3d.addWidget(QLabel("Roll:"), 2, 0)
        self.cb_map_r = QComboBox()
        self.cb_map_r.addItems(["X", "Y", "Z"])
        self.cb_map_r.setCurrentText(self.config_data.get("map_roll", "Y"))
        grid_3d.addWidget(self.cb_map_r, 2, 1)

        self.sp_r = QDoubleSpinBox()
        self.sp_r.setRange(-360, 360)
        self.sp_r.setSingleStep(5)
        self.sp_r.setValue(self.config_data.get("offset_roll", 0))
        grid_3d.addWidget(self.sp_r, 2, 2)

        self.chk_inv_r = QCheckBox("Inv.")
        self.chk_inv_r.setChecked(self.config_data.get("invert_roll", False))
        grid_3d.addWidget(self.chk_inv_r, 2, 3)

        # Fila YAW
        grid_3d.addWidget(QLabel("Yaw:"), 3, 0)
        self.cb_map_y = QComboBox()
        self.cb_map_y.addItems(["X", "Y", "Z"])
        self.cb_map_y.setCurrentText(self.config_data.get("map_yaw", "Z"))
        grid_3d.addWidget(self.cb_map_y, 3, 1)

        self.sp_y = QDoubleSpinBox()
        self.sp_y.setRange(-360, 360)
        self.sp_y.setSingleStep(5)
        self.sp_y.setValue(self.config_data.get("offset_yaw", 0))
        grid_3d.addWidget(self.sp_y, 3, 2)

        self.chk_inv_y = QCheckBox("Inv.")
        self.chk_inv_y.setChecked(self.config_data.get("invert_yaw", False))
        grid_3d.addWidget(self.chk_inv_y, 3, 3)

        lay1.addLayout(grid_3d)

        # Altura Inicial
        lay1.addWidget(QLabel("<b>Calibrar Altura Inicial (m):</b>"))
        self.sp_alt = QDoubleSpinBox()
        self.sp_alt.setRange(0, 10000)
        self.sp_alt.setValue(self.config_data.get("altitud_inicial", 2240.0))
        lay1.addWidget(self.sp_alt)

        main_layout.addWidget(q1, 0, 0)

        # ---------------------------------------------------------
        # CUADRANTE 2: MODELO 3D (RESTAURADO CON PanelVisor3D)
        # ---------------------------------------------------------
        q2 = QFrame()
        q2.setProperty("isQuadrant", True)
        lay2 = QVBoxLayout(q2)

        self.preview_3d = PanelVisor3D()  # <-- Aquí utilizamos tu clase personalizada
        lay2.addWidget(self.preview_3d)

        main_layout.addWidget(q2, 0, 1)

        # ---------------------------------------------------------
        # CUADRANTE 3: COMUNICACIÓN & MODO
        # ---------------------------------------------------------
        q3 = QFrame()
        q3.setProperty("isQuadrant", True)
        lay3 = QVBoxLayout(q3)
        lay3.addWidget(QLabel("<b><i class='fa fa-wifi'></i> COMUNICACIÓN SERIAL</b>"))

        self.cb_port = QComboBox()
        lay3.addWidget(QLabel("Puerto COM:"))
        lay3.addWidget(self.cb_port)

        self.cb_baud = QComboBox()
        self.cb_baud.addItems(
            [
                "9600",
                "19200",
                "31250",
                "38400",
                "57600",
                "74880",
                "115200",
                "230400",
                "250000",
                "460800",
                "500000",
                "921600",
                "1000000",
                "2000000",
            ]
        )
        self.cb_baud.setCurrentText(str(self.config_data.get("baudrate", 115200)))

        lay3.addWidget(QLabel("Baudrate:"))
        lay3.addWidget(self.cb_baud)

        lay3.addWidget(QLabel("Modo de Operación:"))
        self.rb_mision = QRadioButton("Misión Real (Serial Live)")
        self.rb_sim = QRadioButton("Simulación (CSV/Internal)")

        if self.config_data.get("is_simulation", False):
            self.rb_sim.setChecked(True)
        else:
            self.rb_mision.setChecked(True)

        lay3.addWidget(self.rb_mision)
        lay3.addWidget(self.rb_sim)

        self.widget_archivo = QWidget()
        lay_archivo = QHBoxLayout(self.widget_archivo)
        lay_archivo.setContentsMargins(0, 0, 0, 0)

        self.txt_csv = QLineEdit()
        self.txt_csv.setReadOnly(True)
        self.txt_csv.setPlaceholderText("Seleccionar archivo de simulación...")
        self.txt_csv.setText(self.config_data.get("archivo_simulacion", ""))

        self.btn_browse = QPushButton("Explorar")
        self.btn_browse.clicked.connect(self._seleccionar_archivo)

        lay_archivo.addWidget(self.txt_csv)
        lay_archivo.addWidget(self.btn_browse)
        lay3.addWidget(self.widget_archivo)

        self.rb_sim.toggled.connect(self.widget_archivo.setVisible)
        self.widget_archivo.setVisible(self.rb_sim.isChecked())

        self.btn_test = QPushButton("PROBAR CONEXIÓN")
        lay3.addWidget(self.btn_test)

        main_layout.addWidget(q3, 1, 0)

        # ---------------------------------------------------------
        # CUADRANTE 4: MONITOR SERIAL
        # ---------------------------------------------------------
        q4 = QFrame()
        q4.setProperty("isQuadrant", True)
        lay4 = QVBoxLayout(q4)
        lay4.addWidget(QLabel("<b><i class='fa fa-terminal'></i> MONITOR SERIAL</b>"))

        self.txt_monitor = QPlainTextEdit()
        self.txt_monitor.setReadOnly(True)
        lay4.addWidget(self.txt_monitor)

        main_layout.addWidget(q4, 1, 1)

        self.btn_main = QPushButton("ESTABLECER CONFIGURACIÓN Y LANZAR")
        self.btn_main.clicked.connect(self.finalizar)
        main_layout.addWidget(self.btn_main, 2, 0, 1, 2)

        self.sp_p.valueChanged.connect(self._update_preview_offsets)
        self.sp_r.valueChanged.connect(self._update_preview_offsets)
        self.sp_y.valueChanged.connect(self._update_preview_offsets)

    @Slot(list)
    def actualizar_lista_puertos(self, puertos_actuales):
        if not puertos_actuales:
            puertos_actuales = ["Ninguno"]

        if puertos_actuales != self._last_known_ports:
            puerto_previo = self.cb_port.currentText()
            puerto_json = self.config_data.get("puerto", "Ninguno")

            self.cb_port.clear()
            self.cb_port.addItems(puertos_actuales)

            if puerto_previo in puertos_actuales:
                self.cb_port.setCurrentText(puerto_previo)
            elif puerto_json in puertos_actuales:
                self.cb_port.setCurrentText(puerto_json)

            self._last_known_ports = puertos_actuales

    @Slot()
    def _seleccionar_archivo(self):
        ruta_inicial = str(BASE_DIR)
        archivo, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar CSV de Simulación",
            ruta_inicial,
            "Archivos CSV (*.csv);;Todos los archivos (*)",
        )
        if archivo:
            self.txt_csv.setText(archivo)

    @Slot()
    def _update_preview_offsets(self):
        # Actualización en vivo del PanelVisor3D
        if hasattr(self.preview_3d, "aplicar_offsets_calibracion"):
            self.preview_3d.aplicar_offsets_calibracion(
                self.sp_p.value(), self.sp_r.value(), self.sp_y.value()
            )

    def update_monitor(self, text):
        self.txt_monitor.appendPlainText(text)
        self.txt_monitor.moveCursor(QTextCursor.MoveOperation.End)

    def finalizar(self):
        self.config_data.update(
            {
                "puerto": self.cb_port.currentText(),
                "baudrate": int(self.cb_baud.currentText()),
                "altitud_inicial": self.sp_alt.value(),
                # Mapeos dinámicos
                "map_pitch": self.cb_map_p.currentText(),
                "map_roll": self.cb_map_r.currentText(),
                "map_yaw": self.cb_map_y.currentText(),
                # Offsets
                "offset_pitch": self.sp_p.value(),
                "offset_roll": self.sp_r.value(),
                "offset_yaw": self.sp_y.value(),
                # Inversiones (renombradas para mayor claridad en el JSON)
                "invert_pitch": self.chk_inv_p.isChecked(),
                "invert_roll": self.chk_inv_r.isChecked(),
                "invert_yaw": self.chk_inv_y.isChecked(),
                "is_simulation": self.rb_sim.isChecked(),
                "archivo_simulacion": self.txt_csv.text(),
            }
        )
        save_config(self.config_data)
        self.accept()
