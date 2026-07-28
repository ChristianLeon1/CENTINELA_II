#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# AÑO: 2025 CREADOR: Christian Yael Ramírez León


# ui/widgets/compass_widget.py

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QApplication, QSlider, QVBoxLayout, QWidget

from ui.theme import PALETTE


class Compass(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # SE ELIMINÓ EL setMinimumSize(400, 400) para permitir que sea 100% adaptativo

        # Rumbo inicial (grados)
        self._heading = 0

        # Mapeo de colores usando la nueva PALETA
        self.track_color = QColor(PALETTE["BORDER"]["DEFAULT"])
        self.glow_color = QColor(PALETTE["ACCENT"]["ACTIVE"])
        self.text_color = QColor(PALETTE["TEXT"]["PRIMARY"])
        self.north_color = QColor(PALETTE["STATUS"]["DANGER"])

    def set_heading(self, val):
        self._heading = val % 360
        self.update()

    def get_cardinal_direction(self):
        dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW", "N"]
        ix = int((self._heading + 22.5) / 45)
        return dirs[ix]

    def set_color_from_palette(self, category, key):
        if category in PALETTE and key in PALETTE[category]:
            self.glow_color = QColor(PALETTE[category][key])
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Centro geométrico y tamaño adaptativo
        rect = self.rect()
        size = min(rect.width(), rect.height())
        center = rect.center()
        painter.translate(center)

        # Radio base dinámico: ocupa el 40% del tamaño disponible (deja márgenes)
        radius = size * 0.45

        # Si el widget se hace minúsculo, evitamos que rompa el renderizado
        if radius < 10:
            return

        self._draw_rings(painter, radius)
        self._draw_ticks_and_cardinals(painter, radius)
        self._draw_center_text(painter, radius)
        self._draw_needle(painter, radius)

    def _draw_rings(self, painter, radius):
        # Grosor de anillo adaptativo
        outer_pen_width = max(1, int(radius * 0.02))
        inner_pen_width = max(1, int(radius * 0.01))

        pen_outer = QPen(self.track_color, outer_pen_width, Qt.PenStyle.SolidLine)
        painter.setPen(pen_outer)
        # Anillo exterior
        painter.drawEllipse(QPointF(0, 0), radius * 1.05, radius * 1.05)

        glow_base = QColor(self.glow_color)
        glow_base.setAlpha(40)
        pen_inner = QPen(glow_base, inner_pen_width)
        painter.setPen(pen_inner)
        # Anillo interior
        painter.drawEllipse(QPointF(0, 0), radius * 0.75, radius * 0.75)

    def _draw_ticks_and_cardinals(self, painter, radius):
        # Tamaños de fuente adaptativos
        font_cardinal = QFont("Segoe UI", max(6, int(radius * 0.12)), QFont.Weight.Bold)
        font_numbers = QFont("Segoe UI", max(5, int(radius * 0.06)))

        for i in range(0, 360, 5):
            rad = math.radians(i - 90)
            cos_a = math.cos(rad)
            sin_a = math.sin(rad)

            is_major = i % 30 == 0
            is_cardinal = i % 90 == 0

            # Dibujar Ticks proporcionalmente
            inner_r = radius * (0.88 if is_major else 0.95)
            outer_r = radius

            p1 = QPointF(inner_r * cos_a, inner_r * sin_a)
            p2 = QPointF(outer_r * cos_a, outer_r * sin_a)

            pen = QPen(
                self.text_color,
                (
                    max(1, int(radius * 0.015))
                    if is_major
                    else max(1, int(radius * 0.005))
                ),
            )

            if not is_major:
                pen.setColor(
                    QColor(PALETTE["BORDER"]["DEFAULT"])
                )  # Rayas menores integradas al diseño

            painter.setPen(pen)
            painter.drawLine(p1, p2)

            # Dibujar Letras o Números adaptativos
            if is_cardinal:
                text_r = radius * 0.65
                tx = text_r * cos_a
                ty = text_r * sin_a

                painter.setFont(font_cardinal)
                if i == 0:
                    text = "N"
                    painter.setPen(self.north_color)
                elif i == 90:
                    text = "E"
                    painter.setPen(self.text_color)
                elif i == 180:
                    text = "S"
                    painter.setPen(self.text_color)
                elif i == 270:
                    text = "W"
                    painter.setPen(self.text_color)

                fm = painter.fontMetrics()
                tr = fm.boundingRect(text)
                painter.drawText(tx - tr.width() / 2, ty + tr.height() / 3, text)

            elif is_major:
                text_r = radius * 0.65
                tx = text_r * cos_a
                ty = text_r * sin_a

                painter.setFont(font_numbers)
                painter.setPen(QColor(PALETTE["TEXT"]["SECONDARY"]))
                text = str(i)
                fm = painter.fontMetrics()
                tr = fm.boundingRect(text)
                painter.drawText(tx - tr.width() / 2, ty + tr.height() / 3, text)

    def _draw_center_text(self, painter, radius):
        large_font = QFont("Gotham", 10, QFont.Weight.Bold)
        painter.setFont(large_font)

        text_val = f"{int(self._heading)}°"
        fm_large = painter.fontMetrics()
        br = fm_large.boundingRect(text_val)

        # Posicionamiento dinámico central
        y_offset_large = br.height() / 4 - (radius * 0.1)

        painter.setPen(self.glow_color)
        painter.drawText(-br.width() / 2, y_offset_large, text_val)
        painter.setPen(self.text_color)
        painter.drawText(-br.width() / 2, y_offset_large, text_val)

        small_font = QFont("Segoe UI", max(6, int(radius * 0.12)), QFont.Weight.Medium)
        painter.setFont(small_font)
        painter.setPen(QColor(PALETTE["TEXT"]["SECONDARY"]))

        dir_text = self.get_cardinal_direction()
        fm_small = painter.fontMetrics()
        sbr = fm_small.boundingRect(dir_text)

        y_offset_small = br.height() / 4 + (radius * 0.15)
        painter.drawText(-sbr.width() / 2, y_offset_small, dir_text)

    def _draw_needle(self, painter, radius):
        rad = math.radians(self._heading - 90)

        # La forma del triángulo ahora es proporcional al radio
        inner_r = radius * 0.35
        outer_r = radius * 1.02

        point_tip = QPointF(outer_r * math.cos(rad), outer_r * math.sin(rad))

        rad_left = rad - math.radians(5)
        rad_right = rad + math.radians(5)

        point_left = QPointF(inner_r * math.cos(rad_left), inner_r * math.sin(rad_left))
        point_right = QPointF(
            inner_r * math.cos(rad_right), inner_r * math.sin(rad_right)
        )

        arrow = QPolygonF([point_tip, point_left, point_right])

        # Grosor del glow dinámico
        base_glow_width = max(1, int(radius * 0.015))

        for i in range(4, 0, -1):
            alpha = int(255 / (i * 2.5))
            glow_color = QColor(self.glow_color)
            glow_color.setAlpha(alpha)
            glow_pen = QPen(
                glow_color,
                i * base_glow_width,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
            painter.setPen(glow_pen)
            painter.drawPolyline(arrow)

        # Relleno y borde
        painter.setPen(QPen(self.glow_color, max(1, int(radius * 0.01))))
        painter.setBrush(self.glow_color)
        painter.drawPolygon(arrow)
