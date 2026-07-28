#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# AÑO: 2026 CREADOR: Ramírez León Christian Yael

from PySide6.QtCore import QRectF, QSize, Qt, Slot
from PySide6.QtGui import QBrush, QColor, QPainter, QRadialGradient
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ui.theme import PALETTE
from ui.widgets.panel_cinematica import PanelCinematica

# --- --- --- --- --- --- --- --- --- --- ---
# --- 1. WIDGET: Gráfica de Pastel ---
# --- --- --- --- --- --- --- --- --- --- ---


class PieChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.received = 0
        self.lost = 0
        self.setMinimumHeight(80)

    @Slot(int, int)
    def update_stats(self, received: int, lost: int):
        self.received = received
        self.lost = lost
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(80, 80)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        margin = 10
        rect_size = min(self.width(), self.height()) - margin
        rect = QRectF(margin / 2, margin / 2, rect_size, rect_size)
        total = self.received + self.lost
        grados_en_un_circulo = 360 * 16

        if total == 0:
            gradient = QRadialGradient(rect.center(), rect.width() / 2)
            gradient.setColorAt(0, QColor(PALETTE["TEXT"]["DISABLED"]).lighter(120))
            gradient.setColorAt(1, QColor(PALETTE["TEXT"]["DISABLED"]).darker(120))
            painter.setBrush(gradient)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(rect)
            return

        angle_lost = (self.lost / total) * grados_en_un_circulo
        gradient_lost = QRadialGradient(rect.center(), rect.width() / 2)
        gradient_lost.setColorAt(0, QColor(PALETTE["STATUS"]["DANGER"]).lighter(150))
        gradient_lost.setColorAt(1, QColor(PALETTE["STATUS"]["DANGER"]).darker(150))
        painter.setBrush(gradient_lost)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPie(rect, 90 * 16, int(angle_lost))

        angle_received = (self.received / total) * grados_en_un_circulo
        gradient_received = QRadialGradient(rect.center(), rect.width() / 2)
        gradient_received.setColorAt(
            0, QColor(PALETTE["STATUS"]["SUCCESS"]).lighter(150)
        )
        gradient_received.setColorAt(
            1, QColor(PALETTE["STATUS"]["SUCCESS"]).darker(150)
        )
        painter.setBrush(gradient_received)
        painter.setPen(Qt.PenStyle.NoPen)
        start_angle = (90 * 16) + int(angle_lost)
        painter.drawPie(rect, start_angle, int(angle_received))


# --- --- --- --- --- --- --- --- --- --- ---
# --- 2. PANEL INFERIOR LIMPIO ---
# --- --- --- --- --- --- --- --- --- --- ---


class PanelInferior(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("isPanel", True)
        self.setFixedHeight(220)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(20)

        # ==========================================
        # PARTE IZQUIERDA: RESUMEN DE PAQUETES (40%)
        # ==========================================
        panel_izquierdo = QFrame()
        panel_izquierdo.setFrameShape(QFrame.Shape.StyledPanel)
        layout_izq = QVBoxLayout(panel_izquierdo)

        grupo_paquetes = QGroupBox("Resumen de Paquetes y Misión")
        layout_paquetes = QHBoxLayout(grupo_paquetes)

        self.pie_chart_paquetes = PieChartWidget()

        layout_texto_wrapper = QVBoxLayout()
        layout_texto_paquetes = QGridLayout()

        # --- ETIQUETAS ESTÁTICAS ---
        label_rec_static = QLabel("Recibidos:")
        label_per_static = QLabel("Perdidos:")
        label_tiempo_static = QLabel("T. Misión:")

        label_rec_static.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        label_per_static.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        label_tiempo_static.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        # --- ETIQUETAS DE DATOS ---
        self.label_paquetes_recibidos = QLabel("0")
        self.label_paquetes_perdidos = QLabel("0")
        self.label_tiempo_mision = QLabel("0.00 s")

        self.label_paquetes_recibidos.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.label_paquetes_perdidos.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.label_tiempo_mision.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        # --- ENSAMBLAJE DEL GRID ---
        layout_texto_paquetes.addWidget(label_rec_static, 0, 0)
        layout_texto_paquetes.addWidget(self.label_paquetes_recibidos, 0, 1)

        layout_texto_paquetes.addWidget(label_per_static, 1, 0)
        layout_texto_paquetes.addWidget(self.label_paquetes_perdidos, 1, 1)

        layout_texto_paquetes.addWidget(label_tiempo_static, 2, 0)
        layout_texto_paquetes.addWidget(self.label_tiempo_mision, 2, 1)

        layout_texto_wrapper.addStretch(1)
        layout_texto_wrapper.addLayout(layout_texto_paquetes)
        layout_texto_wrapper.addStretch(1)

        layout_paquetes.addWidget(self.pie_chart_paquetes, 1)
        layout_paquetes.addLayout(layout_texto_wrapper, 1)

        layout_izq.addWidget(grupo_paquetes)

        # ==========================================
        # PARTE DERECHA: CINEMÁTICA (60%)
        # ==========================================
        self.panel_cinematica = PanelCinematica()

        # Ensamblamos el layout
        main_layout.addWidget(panel_izquierdo, 40)
        main_layout.addWidget(self.panel_cinematica, 60)

    @Slot(dict)
    def update_cinematica(self, data: dict):
        self.panel_cinematica.update_cinematica(data)

    @Slot(int, int)
    def update_packet_summary(self, received: int, lost: int):
        self.label_paquetes_recibidos.setText(str(received))
        self.label_paquetes_perdidos.setText(str(lost))
        self.pie_chart_paquetes.update_stats(received, lost)

    @Slot(float)
    def update_tiempo_mision(self, tiempo: float):
        """Actualiza el tiempo de misión en el resumen de paquetes."""
        self.label_tiempo_mision.setText(f"{tiempo:.2f} s")
