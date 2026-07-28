#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# AÑO: 2025 CREADOR: Christian Yael Ramírez León

# ui/widgets/panel_altimetro.py

import sys

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Slot
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QApplication, QFrame, QVBoxLayout, QWidget

from ui.theme import PALETTE


class PanelAltimetro(QFrame):
    """
    Panel de altímetro vertical moderno dibujado con QPainter.
    Integra la paleta de colores global.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("isPanel", True)

        # Valores del altímetro (en metros)
        self._value = 0
        self._min_value = 0
        self._max_value = 500  # Límite ajustado a 500

        # Asignación de colores utilizando el diccionario PALETTE
        self.bg_color = QColor(PALETTE["BACKGROUND"]["MAIN"])
        self.track_color = QColor(PALETTE["BORDER"]["DEFAULT"])
        self.glow_color = QColor(
            PALETTE["ACCENT"]["ACTIVE"]
        )  # Puedes cambiarlo a PALETTE['STATUS']['DANGER']
        self.text_color = QColor(PALETTE["TEXT"]["PRIMARY"])
        self.tick_color = QColor(PALETTE["TEXT"]["SECONDARY"])

    @Slot(int)
    def update_altitud(self, altitud: float):
        """
        Slot público para actualizar la altitud.
        """
        # LÍMITE ACTUALIZADO A 500
        val_limitado = max(0, min(altitud, 500))
        self._value = val_limitado

        # Llamamos a update() para que paintEvent se encargue de redibujar la barra y el texto modificado.
        self.update()

    def set_color_from_palette(self, category, key):
        """
        Permite actualizar el color principal (brillo) directamente desde la PALETTE
        """
        if category in PALETTE and key in PALETTE[category]:
            self.glow_color = QColor(PALETTE[category][key])
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Fondo general
        painter.fillRect(self.rect(), self.bg_color)

        width = self.width()
        height = self.height()

        bar_width = 10
        bar_x = width / 2 + 10
        bar_y_top = 40
        bar_y_bottom = height - 120
        bar_height = bar_y_bottom - bar_y_top

        rect_bg = QRectF(bar_x, bar_y_top, bar_width, bar_height)

        self._draw_ticks_and_scale(painter, bar_x, bar_y_top, bar_y_bottom, bar_height)
        self._draw_background_bar(painter, rect_bg)
        self._draw_active_bar(painter, rect_bg, bar_y_bottom, bar_height)
        self._draw_indicator_arrow(painter, bar_x, bar_width, bar_y_bottom, bar_height)
        self._draw_footer_text(painter, width, bar_y_bottom)

    def _draw_ticks_and_scale(self, painter, bar_x, y_top, y_bottom, bar_height):
        font = QFont("Gotham", 9)
        painter.setFont(font)

        for val in range(self._min_value, self._max_value + 1, 50):
            ratio = (val - self._min_value) / (self._max_value - self._min_value)
            y = y_bottom - (bar_height * ratio)

            is_major = val % 100 == 0

            tick_length = 12 if is_major else 6
            pen = QPen(
                self.text_color if is_major else self.tick_color, 2 if is_major else 1
            )
            painter.setPen(pen)

            tick_x_end = bar_x - 10
            tick_x_start = tick_x_end - tick_length
            painter.drawLine(QPointF(tick_x_start, y), QPointF(tick_x_end, y))

            if is_major:
                text = str(val)
                fm = painter.fontMetrics()
                tr = fm.boundingRect(text)

                text_x = tick_x_start - tr.width() - 8
                text_y = y + tr.height() / 3

                painter.setPen(self.tick_color)
                painter.drawText(text_x, text_y, text)

    def _draw_background_bar(self, painter, rect):
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self.track_color)
        painter.drawRoundedRect(rect, rect.width() / 2, rect.width() / 2)

    def _draw_active_bar(self, painter, rect, y_bottom, bar_height):
        ratio = (self._value - self._min_value) / (self._max_value - self._min_value)
        active_height = bar_height * ratio

        if active_height <= 0.5:
            return

        active_rect = QRectF(
            rect.x(), y_bottom - active_height, rect.width(), active_height
        )

        painter.setBrush(Qt.BrushStyle.NoBrush)
        for i in range(4, 0, -1):
            alpha = int(255 / (i * 2.5))
            glow_color = QColor(self.glow_color)
            glow_color.setAlpha(alpha)
            glow_pen = QPen(glow_color, 4 + (i * 4))
            glow_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(glow_pen)
            painter.drawRoundedRect(
                active_rect, active_rect.width() / 2, active_rect.width() / 2
            )

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self.glow_color)
        painter.drawRoundedRect(
            active_rect, active_rect.width() / 2, active_rect.width() / 2
        )

    def _draw_indicator_arrow(self, painter, bar_x, bar_width, y_bottom, bar_height):
        ratio = (self._value - self._min_value) / (self._max_value - self._min_value)
        y = y_bottom - (bar_height * ratio)

        arrow_size = 10
        arrow_x = bar_x + bar_width + 8

        p1 = QPointF(arrow_x, y)
        p2 = QPointF(arrow_x + arrow_size, y - arrow_size / 1.5)
        p3 = QPointF(arrow_x + arrow_size, y + arrow_size / 1.5)

        arrow_poly = QPolygonF([p1, p2, p3])

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self.glow_color)
        painter.drawPolygon(arrow_poly)

    def _draw_footer_text(self, painter, width, y_bottom):
        # Usamos una fuente monoespaciada para evitar saltos tal como lo pedías en el segundo bloque
        font_value = QFont("Gotham", 13)
        font_value.setStyleHint(QFont.StyleHint.Monospace)
        painter.setFont(font_value)

        val_text = f"ALTURA: {round(self._value, 2)} m"
        fm_v = painter.fontMetrics()
        tr_v = fm_v.boundingRect(val_text)
        val_y = y_bottom + 60

        # Sombra del texto (basada en el color de brillo)
        painter.setPen(self.glow_color)
        painter.drawText(width / 2 - tr_v.width() / 2, val_y, val_text)

        # Texto principal
        painter.setPen(self.text_color)
        painter.drawText(width / 2 - tr_v.width() / 2, val_y, val_text)
