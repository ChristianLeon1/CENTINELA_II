#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# AÑO: 2026 CREADOR: Ramírez León Christian Yael

import math
import sys

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QApplication, QSlider, QVBoxLayout, QWidget

from ui.theme import PALETTE


class ModernSpeedometer(QWidget):
    def __init__(self, parent=None, max_value=160, unit="km/h", steps=8):
        """
        Inicializa el velocímetro.
        :param max_value: Valor máximo de la escala.
        :param unit: Texto de las unidades (ej. 'km/h', 'RPM', 'mph').
        :param steps: Cantidad de subdivisiones/barras mayores (mínimo 5).
        """
        super().__init__(parent)

        # Variables del velocímetro
        self._value = 0
        self._min_value = 0
        self._max_value = max_value * 100
        self._unit = unit
        self._steps = max(5, steps)  # Garantizamos al menos 5 divisiones principales

        # Ángulos (En Qt, 0 es a las 3 en punto. Positivo es en sentido antihorario)
        self._start_angle = 225  # Empieza en la parte inferior izquierda
        self._sweep_angle = -270  # Se mueve en sentido horario

        # Mapeo de colores usando la PALETA
        self.track_color = QColor(PALETTE["BORDER"]["DEFAULT"])
        self.glow_color = QColor(PALETTE["ACCENT"]["ACTIVE"])
        self.text_color = QColor(PALETTE["TEXT"]["PRIMARY"])

    def set_value(self, val):
        """Actualiza la velocidad y redibuja el widget."""
        self._value = max(self._min_value, min(val, self._max_value)) * 100
        self.update()

    def set_color_from_palette(self, category, key):
        """Permite cambiar el color principal al vuelo."""
        if category in PALETTE and key in PALETTE[category]:
            self.glow_color = QColor(PALETTE[category][key])
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Geometría básica y tamaño adaptativo
        rect = self.rect()
        size = min(rect.width(), rect.height())
        center = rect.center()

        painter.translate(center)

        # El radio ocupa el 45% del espacio disponible
        radius = size * 0.45
        if radius < 10:
            return  # Evita errores si el widget se hace minúsculo

        arc_rect = QRectF(-radius, -radius, radius * 2, radius * 2)

        self._draw_background_track(painter, arc_rect, radius)
        self._draw_active_track(painter, arc_rect, radius)
        self._draw_ticks_and_labels(painter, radius)
        self._draw_needle(painter, radius)
        self._draw_center_text(painter, radius)

    def _draw_background_track(self, painter, rect, radius):
        """Dibuja el arco gris oscuro de fondo."""
        track_width = max(2, int(radius * 0.075))

        pen = QPen(
            self.track_color,
            track_width,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
        )
        painter.setPen(pen)
        painter.drawArc(rect, self._start_angle * 16, self._sweep_angle * 16)

        offset = radius * 0.18
        inner_rect = rect.adjusted(offset, offset, -offset, -offset)
        inner_pen = QPen(
            self.track_color,
            max(1, int(radius * 0.015)),
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
        )
        painter.setPen(inner_pen)
        painter.drawArc(inner_rect, self._start_angle * 16, self._sweep_angle * 16)

    def _draw_active_track(self, painter, rect, radius):
        """Dibuja el arco luminoso según la velocidad actual."""
        ratio = (self._value - self._min_value) / (self._max_value - self._min_value)
        current_sweep = self._sweep_angle * ratio

        base_glow_width = max(2, int(radius * 0.075))

        for i in range(4, 0, -1):
            alpha = int(255 / (i * 2.5))
            glow_color = QColor(self.glow_color)
            glow_color.setAlpha(alpha)

            glow_pen = QPen(
                glow_color,
                base_glow_width + (i * radius * 0.035),
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
            )
            painter.setPen(glow_pen)
            painter.drawArc(rect, self._start_angle * 16, current_sweep * 16)

        solid_pen = QPen(
            self.glow_color,
            max(2, int(radius * 0.05)),
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
        )
        painter.setPen(solid_pen)
        painter.drawArc(rect, self._start_angle * 16, current_sweep * 16)

    def _draw_ticks_and_labels(self, painter, radius):
        """Dibuja las marcas mayores y menores (ticks) y los números adaptativos."""
        font_size = max(5, int(radius * 0.07))
        font = QFont("Segoe UI", font_size)
        painter.setFont(font)

        # Subdivisión para las marcas finas: 5 subdivisiones crean 4 marcas menores por cada paso mayor
        minor_steps = 5
        total_ticks = self._steps * minor_steps

        for i in range(total_ticks + 1):
            is_major = i % minor_steps == 0

            val = (
                self._min_value + i * (self._max_value - self._min_value) / total_ticks
            )
            ratio = i / total_ticks
            angle = self._start_angle + (self._sweep_angle * ratio)
            rad = math.radians(angle)

            cos_a = math.cos(rad)
            sin_a = -math.sin(rad)

            # --- Dibujar Ticks (Marcas) ---
            if is_major:
                inner_r = radius * 0.88
                outer_r = radius * 1.05
                # Grosor mayor
                tick_pen = QPen(self.text_color, max(1, int(radius * 0.015)))
            else:
                inner_r = radius * 0.96  # Más corto por dentro
                outer_r = radius * 1.02  # Más corto por fuera
                # Color atenuado (DISABLED) y grosor más fino
                color_minor = QColor(PALETTE["TEXT"]["DISABLED"])
                tick_pen = QPen(color_minor, max(1, int(radius * 0.008)))

            painter.setPen(tick_pen)

            p1 = QPointF(inner_r * cos_a, inner_r * sin_a)
            p2 = QPointF(outer_r * cos_a, outer_r * sin_a)
            painter.drawLine(p1, p2)

            # --- Dibujar Texto (Solo en marcas mayores) ---
            if is_major:
                text_r = radius * 0.72
                tx = text_r * cos_a
                ty = text_r * sin_a

                text = f"{int(val/100)}"
                fm = painter.fontMetrics()
                tr = fm.boundingRect(text)

                painter.setPen(self.text_color)
                painter.drawText(tx - tr.width() / 2, ty + tr.height() / 3, text)

    def _draw_needle(self, painter, radius):
        """Dibuja la aguja o indicador luminiscente."""
        ratio = (self._value - self._min_value) / (self._max_value - self._min_value)
        angle = self._start_angle + (self._sweep_angle * ratio)
        rad = math.radians(angle)

        cos_a = math.cos(rad)
        sin_a = -math.sin(rad)

        inner_r = radius * 0.75
        outer_r = radius * 0.95

        p1 = QPointF(inner_r * cos_a, inner_r * sin_a)
        p2 = QPointF(outer_r * cos_a, outer_r * sin_a)

        glow_pen = QPen(self.glow_color, max(2, int(radius * 0.04)))
        glow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(glow_pen)
        painter.drawLine(p1, p2)

        core_pen = QPen(Qt.GlobalColor.white, max(1, int(radius * 0.015)))
        core_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(core_pen)
        painter.drawLine(p1, p2)

    def _draw_center_text(self, painter, radius):
        """Dibuja la velocidad en grande en el centro adaptativamente."""
        large_font = QFont("Gotham", 10)
        painter.setFont(large_font)

        text_val = str(round(self._value / 100, 2))
        fm_large = painter.fontMetrics()
        br = fm_large.boundingRect(text_val)

        y_offset_large = br.height() / 4 - (radius * 0.05)

        painter.setPen(self.glow_color)
        painter.drawText(-br.width() / 2, y_offset_large, text_val)

        painter.setPen(self.text_color)
        painter.drawText(-br.width() / 2, y_offset_large, text_val)

        small_font_size = max(5, int(radius * 0.08))
        small_font = QFont("Segoe UI", small_font_size)
        painter.setFont(small_font)
        painter.setPen(QColor(PALETTE["TEXT"]["SECONDARY"]))

        fm_small = painter.fontMetrics()
        sbr = fm_small.boundingRect(self._unit)

        y_offset_small = br.height() / 4 + (radius * 0.18)
        painter.drawText(-sbr.width() / 2, y_offset_small, self._unit)
