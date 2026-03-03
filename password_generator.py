"""
KeyVault — Premium Password Generator
PySide6 · Liquid Glass · Real-time generation
"""

import sys

from engine import PasswordEngine

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSlider, QLineEdit, QFrame,
    QGraphicsDropShadowEffect, QSizePolicy
)
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QParallelAnimationGroup,
    QSequentialAnimationGroup, QEasingCurve, QPoint,
    QTimer, Property, QRectF, Signal
)
from PySide6.QtGui import (
    QColor, QPainter, QPainterPath, QLinearGradient,
    QPen, QBrush, QCursor, QRadialGradient, QFont,
    QFontDatabase
)
from PySide6.QtWidgets import QGraphicsOpacityEffect


# ──────────────────────────────────────────────────────
#  TOGGLE PILL  (fully vector-painted, crisp at any DPI)
# ──────────────────────────────────────────────────────
class TogglePill(QWidget):
    toggled = Signal(bool)

    def __init__(self, label="", checked=True, parent=None):
        super().__init__(parent)
        self._checked  = checked
        self._label    = label
        self._anim_val = 1.0 if checked else 0.0
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFixedHeight(34)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self._anim = QPropertyAnimation(self, b"knob_pos", self)
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.InOutCubic)

    def _get_knob(self):  return self._anim_val
    def _set_knob(self, v):
        self._anim_val = v
        self.update()
    knob_pos = Property(float, _get_knob, _set_knob)

    @property
    def isChecked(self): return self._checked

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._checked = not self._checked
            self._anim.stop()
            self._anim.setStartValue(self._anim_val)
            self._anim.setEndValue(1.0 if self._checked else 0.0)
            self._anim.start()
            self.toggled.emit(self._checked)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        PILL_W, PILL_H = 42, 22
        pill_y = (self.height() - PILL_H) // 2

        # Track
        track = QPainterPath()
        track.addRoundedRect(0.0, float(pill_y),
                             float(PILL_W), float(PILL_H),
                             PILL_H / 2.0, PILL_H / 2.0)
        if self._checked:
            g = QLinearGradient(0, 0, PILL_W, 0)
            g.setColorAt(0, QColor(108, 142, 239))
            g.setColorAt(1, QColor(155, 108, 239))
            p.fillPath(track, QBrush(g))
        else:
            p.fillPath(track, QBrush(QColor(255, 255, 255, 25)))
            p.setPen(QPen(QColor(255, 255, 255, 45), 1))
            p.setBrush(Qt.NoBrush)
            p.drawPath(track)

        # Knob
        KNOB_D = PILL_H - 6
        margin = 3.0
        kx = margin + self._anim_val * (PILL_W - KNOB_D - margin * 2)
        ky = pill_y + (PILL_H - KNOB_D) / 2.0
        p.setPen(Qt.NoPen)
        # knob shadow
        sg = QRadialGradient(kx + KNOB_D / 2, ky + KNOB_D / 2 + 1.5, KNOB_D)
        sg.setColorAt(0, QColor(0, 0, 0, 50))
        sg.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(QBrush(sg))
        p.drawEllipse(QRectF(kx - 2, ky - 1, KNOB_D + 4, KNOB_D + 4))
        # knob face
        p.setBrush(QColor(255, 255, 255, 248))
        p.drawEllipse(QRectF(kx, ky, KNOB_D, KNOB_D))

        # Label
        tx = PILL_W + 12
        alpha = 210 if self._checked else 110
        p.setPen(QColor(255, 255, 255, alpha))
        f = QFont("Segoe UI", 13)
        f.setWeight(QFont.Medium)
        p.setFont(f)
        p.drawText(tx, 0, self.width() - tx, self.height(),
                   Qt.AlignVCenter | Qt.AlignLeft, self._label)


# ──────────────────────────────────────────────────────
#  STRENGTH BAR
# ──────────────────────────────────────────────────────
class StrengthBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(4)
        self._fill  = 0.0
        self._color = QColor("#6C8EEF")
        self._anim  = QPropertyAnimation(self, b"fill", self)
        self._anim.setDuration(400)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

    def get_fill(self):  return self._fill
    def set_fill(self, v):
        self._fill = v; self.update()
    fill = Property(float, get_fill, set_fill)

    def set_strength(self, score, label):
        self._color = {
            "Weak":      QColor("#EF6C6C"),
            "Fair":      QColor("#EFC56C"),
            "Strong":    QColor("#6CEFA0"),
            "Excellent": QColor("#6C8EEF"),
        }.get(label, QColor("#6C8EEF"))
        self._anim.stop()
        self._anim.setStartValue(self._fill)
        self._anim.setEndValue(score / 100.0)
        self._anim.start()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 18))
        p.drawRoundedRect(0, 0, w, h, h / 2, h / 2)
        fw = int(w * self._fill)
        if fw > 0:
            g = QLinearGradient(0, 0, fw, 0)
            g.setColorAt(0, self._color.lighter(130))
            g.setColorAt(1, self._color)
            p.setBrush(QBrush(g))
            p.drawRoundedRect(0, 0, fw, h, h / 2, h / 2)


# ──────────────────────────────────────────────────────
#  COPY BUTTON
# ──────────────────────────────────────────────────────
class CopyButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__("Copy to Clipboard", parent)
        self._glow = 0.0
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFixedHeight(48)
        self._default_style()
        self._hover_anim = QPropertyAnimation(self, b"glow_level", self)
        self._hover_anim.setDuration(200)
        self._hover_anim.setEasingCurve(QEasingCurve.OutCubic)

    def _default_style(self):
        self.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.07);
                color: rgba(255,255,255,0.75);
                border: 1px solid rgba(255,255,255,0.13);
                border-radius: 14px;
                font-family: 'Segoe UI';
                font-size: 14px;
                font-weight: 500;
                letter-spacing: 0.2px;
            }
            QPushButton:disabled {
                background: rgba(255,255,255,0.03);
                color: rgba(255,255,255,0.20);
                border-color: rgba(255,255,255,0.05);
            }
        """)

    def get_glow_level(self):  return self._glow
    def set_glow_level(self, v):
        self._glow = v; self.update()
    glow_level = Property(float, get_glow_level, set_glow_level)

    def enterEvent(self, e):
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._glow)
        self._hover_anim.setEndValue(1.0)
        self._hover_anim.start()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._glow)
        self._hover_anim.setEndValue(0.0)
        self._hover_anim.start()
        super().leaveEvent(e)

    def show_success(self):
        self.setText("✓  Copied!")
        self.setStyleSheet("""
            QPushButton {
                background: rgba(80,220,130,0.13);
                color: rgba(100,245,155,0.90);
                border: 1px solid rgba(100,245,155,0.25);
                border-radius: 14px;
                font-family: 'Segoe UI';
                font-size: 14px;
                font-weight: 600;
            }
        """)

    def show_default(self):
        self.setText("Copy to Clipboard")
        self._default_style()


# ──────────────────────────────────────────────────────
#  MAIN WINDOW
# ──────────────────────────────────────────────────────
class KeyVaultWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        # WA_TranslucentBackground = the OS composites our alpha channel,
        # so only pixels we actually paint are visible — no sharp corner fill.
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(460, 582)

        self._drag_pos   = None
        self._copy_timer = QTimer(self)
        self._copy_timer.setSingleShot(True)
        self._copy_timer.timeout.connect(self._on_copy_reset)

        scr = QApplication.primaryScreen().geometry()
        self.move((scr.width() - self.width()) // 2,
                  (scr.height() - self.height()) // 2)

        self._build_ui()
        self._connect_signals()
        self._regenerate()

        self.setWindowOpacity(0.0)
        self._launch()

    # ── UI ──────────────────────────────────────────
    def _build_ui(self):
        # Outer margin gives the drop-shadow room to render
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)

        # Transparent container that receives the drop shadow
        self.card = QWidget()
        self.card.setAttribute(Qt.WA_TranslucentBackground)
        root.addWidget(self.card)

        shadow = QGraphicsDropShadowEffect(self.card)
        shadow.setBlurRadius(52)
        shadow.setOffset(0, 12)
        shadow.setColor(QColor(0, 0, 0, 115))
        self.card.setGraphicsEffect(shadow)

        lay = QVBoxLayout(self.card)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(0)

        self._build_header(lay)
        lay.addSpacing(22)
        self._build_password_section(lay)
        lay.addSpacing(8)
        self._build_strength_row(lay)
        lay.addSpacing(24)
        self._build_slider_section(lay)
        lay.addSpacing(22)
        self._build_toggles(lay)
        lay.addSpacing(24)
        self._build_copy_button(lay)
        lay.addSpacing(14)
        self._build_footer(lay)

    def _build_header(self, lay):
        row = QHBoxLayout(); row.setSpacing(0)
        icon = QLabel("⌘")
        icon.setStyleSheet(
            "font-size: 20px; color: rgba(150,175,255,0.85); background: transparent;")
        icon.setFixedWidth(30)
        row.addWidget(icon)
        col = QVBoxLayout(); col.setSpacing(1)
        t1 = QLabel("KeyVault")
        t1.setStyleSheet(
            "color: rgba(255,255,255,0.95); font-family: 'Segoe UI'; font-size: 19px; "
            "font-weight: 700; background: transparent; letter-spacing: -0.4px;")
        col.addWidget(t1)
        row.addLayout(col); row.addStretch()
        close = QPushButton("✕")
        close.setFixedSize(26, 26)
        close.setCursor(QCursor(Qt.PointingHandCursor))
        close.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.06);
                color: rgba(255,255,255,0.35);
                border: 1px solid rgba(255,255,255,0.09);
                border-radius: 13px; font-size: 9px;
            }
            QPushButton:hover {
                background: rgba(235,90,90,0.60);
                color: white; border-color: transparent;
            }
        """)
        close.clicked.connect(self.close)
        row.addWidget(close)
        lay.addLayout(row)

    def _build_password_section(self, lay):
        box = QWidget()
        box.setFixedHeight(66)
        box.setStyleSheet("""
            QWidget {
                background: rgba(255,255,255,0.055);
                border-radius: 15px;
                border: 1px solid rgba(255,255,255,0.09);
            }
        """)
        cl = QHBoxLayout(box); cl.setContentsMargins(18, 0, 14, 0); cl.setSpacing(8)

        self.pw_field = QLineEdit()
        self.pw_field.setReadOnly(True)
        self.pw_field.setStyleSheet("""
            QLineEdit {
                background: transparent; border: none;
                color: rgba(255,255,255,0.93);
                font-family: 'Cascadia Code','Consolas','Courier New',monospace;
                font-size: 15px; font-weight: 500; letter-spacing: 1.6px;
                selection-background-color: rgba(108,142,239,0.32);
            }
        """)
        self._pw_opacity = QGraphicsOpacityEffect(self.pw_field)
        self._pw_opacity.setOpacity(1.0)
        self.pw_field.setGraphicsEffect(self._pw_opacity)
        cl.addWidget(self.pw_field)

        self._refresh_btn = QPushButton("↺")
        self._refresh_btn.setFixedSize(30, 30)
        self._refresh_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self._refresh_btn.setToolTip("Regenerate")
        self._refresh_btn.setStyleSheet("""
            QPushButton {
                background: rgba(108,142,239,0.16);
                color: rgba(160,188,255,0.80);
                border: 1px solid rgba(108,142,239,0.22);
                border-radius: 15px; font-size: 15px; font-weight: 700;
            }
            QPushButton:hover {
                background: rgba(108,142,239,0.32); color: white;
            }
        """)
        cl.addWidget(self._refresh_btn)
        lay.addWidget(box)

    def _build_strength_row(self, lay):
        row = QHBoxLayout(); row.setSpacing(0)
        self.strength_bar = StrengthBar()
        self.strength_label = QLabel("")
        self.strength_label.setFixedWidth(64)
        self.strength_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.strength_label.setStyleSheet(
            "color: rgba(255,255,255,0.38); font-family: 'Segoe UI'; "
            "font-size: 11px; letter-spacing: 0.3px; background: transparent;")
        row.addWidget(self.strength_bar)
        row.addSpacing(10)
        row.addWidget(self.strength_label)
        lay.addLayout(row)

    def _build_slider_section(self, lay):
        hdr = QHBoxLayout()
        lbl = QLabel("LENGTH")
        lbl.setStyleSheet(
            "color: rgba(255,255,255,0.38); font-family: 'Segoe UI'; "
            "font-size: 10px; font-weight: 600; letter-spacing: 1.2px; background: transparent;")
        self.len_badge = QLabel("16")
        self.len_badge.setAlignment(Qt.AlignCenter)
        self.len_badge.setFixedWidth(44)
        self.len_badge.setStyleSheet("""
            color: rgba(180,200,255,0.90);
            font-family: 'Segoe UI'; font-size: 16px; font-weight: 700;
            background: rgba(108,142,239,0.14);
            border: 1px solid rgba(108,142,239,0.24);
            border-radius: 9px; padding: 1px 4px;
        """)
        hdr.addWidget(lbl); hdr.addStretch(); hdr.addWidget(self.len_badge)
        lay.addLayout(hdr)
        lay.addSpacing(10)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(6, 64)
        self.slider.setValue(16)
        self.slider.setFixedHeight(26)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px; background: rgba(255,255,255,0.10); border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #6C8EEF, stop:1 #9B6CEF);
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                width: 18px; height: 18px; margin: -7px 0;
                border-radius: 9px; background: white;
                border: 2px solid rgba(108,142,239,0.50);
            }
            QSlider::handle:horizontal:hover {
                background: #EEF2FF; border-color: #9B6CEF;
                width: 20px; height: 20px; margin: -8px 0; border-radius: 10px;
            }
        """)
        lay.addWidget(self.slider)

        rng = QHBoxLayout()
        for v in ["6", "64"]:
            r = QLabel(v)
            r.setStyleSheet(
                "color: rgba(255,255,255,0.20); font-family: 'Segoe UI'; "
                "font-size: 10px; background: transparent;")
            rng.addWidget(r)
            if v == "6": rng.addStretch()
        lay.addLayout(rng)

    def _build_toggles(self, lay):
        sec = QLabel("CHARACTER SETS")
        sec.setStyleSheet(
            "color: rgba(255,255,255,0.38); font-family: 'Segoe UI'; "
            "font-size: 10px; font-weight: 600; letter-spacing: 1.2px; background: transparent;")
        lay.addWidget(sec)
        lay.addSpacing(12)

        self.tog_lower   = TogglePill("Lowercase   a – z", checked=True)
        self.tog_upper   = TogglePill("Uppercase  A – Z",  checked=True)
        self.tog_digits  = TogglePill("Numbers    0 – 9",  checked=True)
        self.tog_special = TogglePill("Symbols    ! @ # …", checked=False)

        grid = QHBoxLayout(); grid.setSpacing(0)
        left  = QVBoxLayout(); left.setSpacing(8)
        right = QVBoxLayout(); right.setSpacing(8)
        left.addWidget(self.tog_lower)
        left.addWidget(self.tog_upper)
        right.addWidget(self.tog_digits)
        right.addWidget(self.tog_special)
        grid.addLayout(left); grid.addSpacing(6); grid.addLayout(right)
        lay.addLayout(grid)

    def _build_copy_button(self, lay):
        self.copy_btn = CopyButton()
        self.copy_btn.setEnabled(False)
        lay.addWidget(self.copy_btn)

    def _build_footer(self, lay):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(
            "background: rgba(255,255,255,0.06); max-height: 1px; border: none;")
        lay.addWidget(line)
        lay.addSpacing(9)
        hint = QLabel("Drag to move  ·  Click ✕ to close")
        hint.setText("Drag to move  ·  Click ✕ to close")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet(
            "color: rgba(255,255,255,0.16); font-family: 'Segoe UI'; "
            "font-size: 10px; letter-spacing: 0.3px; background: transparent;")
        lay.addWidget(hint)

    # ── signals ─────────────────────────────────────
    def _connect_signals(self):
        self.slider.valueChanged.connect(self._on_change)
        self._refresh_btn.clicked.connect(self._regenerate)
        self.copy_btn.clicked.connect(self._on_copy)
        for tog in (self.tog_lower, self.tog_upper,
                    self.tog_digits, self.tog_special):
            tog.toggled.connect(lambda _: self._on_change())

    # ── logic ────────────────────────────────────────
    def _on_change(self):
        self.len_badge.setText(str(self.slider.value()))
        self._regenerate()

    def _regenerate(self):
        pw = PasswordEngine.generate(
            self.slider.value(),
            self.tog_lower.isChecked,
            self.tog_upper.isChecked,
            self.tog_digits.isChecked,
            self.tog_special.isChecked,
        )
        if pw:
            self._animate_swap(pw)
            score, label = PasswordEngine.strength(pw)
            self.strength_bar.set_strength(score, label)
            self.strength_label.setText(label)
            self.copy_btn.setEnabled(True)
        else:
            self.pw_field.clear()
            self.strength_bar.set_strength(0, "")
            self.strength_label.setText("")
            self.copy_btn.setEnabled(False)

    def _animate_swap(self, pw):
        fade_out = QPropertyAnimation(self._pw_opacity, b"opacity", self)
        fade_out.setDuration(90)
        fade_out.setStartValue(1.0); fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.OutQuad)
        fade_in = QPropertyAnimation(self._pw_opacity, b"opacity", self)
        fade_in.setDuration(180)
        fade_in.setStartValue(0.0); fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.OutCubic)
        seq = QSequentialAnimationGroup(self)
        seq.addAnimation(fade_out); seq.addAnimation(fade_in)
        fade_out.finished.connect(lambda: self.pw_field.setText(pw))
        seq.start()

    def _on_copy(self):
        pw = self.pw_field.text()
        if not pw: return
        QApplication.clipboard().setText(pw)
        self.copy_btn.show_success()
        self._copy_timer.start(2000)

    def _on_copy_reset(self):
        self.copy_btn.show_default()

    # ── launch animation ─────────────────────────────
    def _launch(self):
        start = self.pos() + QPoint(0, 16)
        end   = self.pos()
        self.move(start)
        fade  = QPropertyAnimation(self, b"windowOpacity", self)
        fade.setDuration(400); fade.setStartValue(0.0); fade.setEndValue(1.0)
        fade.setEasingCurve(QEasingCurve.OutCubic)
        slide = QPropertyAnimation(self, b"pos", self)
        slide.setDuration(420); slide.setStartValue(start); slide.setEndValue(end)
        slide.setEasingCurve(QEasingCurve.OutCubic)
        grp = QParallelAnimationGroup(self)
        grp.addAnimation(fade); grp.addAnimation(slide)
        grp.start()

    # ── drag ─────────────────────────────────────────
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.LeftButton and self._drag_pos:
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None

    def keyPressEvent(self, e):
        pass

    # ── window painting ──────────────────────────────
    # WA_TranslucentBackground means Qt composites per-pixel alpha.
    # We clip everything to a rounded rect path first, then paint the
    # glass layers — the OS never sees the corner pixels we don't draw,
    # so there are NO sharp corners at all.
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        W, H, R = float(self.width()), float(self.height()), 22.0

        clip = QPainterPath()
        clip.addRoundedRect(0.0, 0.0, W, H, R, R)
        p.setClipPath(clip)          # <-- everything below is clipped to rounded shape

        # Deep glass base
        bg = QLinearGradient(0, 0, W * 0.5, H)
        bg.setColorAt(0.0, QColor(21, 19, 44))
        bg.setColorAt(0.6, QColor(17, 15, 36))
        bg.setColorAt(1.0, QColor(11, 10, 26))
        p.setBrush(QBrush(bg)); p.setPen(Qt.NoPen)
        p.drawPath(clip)

        # Blue-indigo radial bloom
        bloom = QRadialGradient(W * 0.20, H * 0.05, W * 0.55)
        bloom.setColorAt(0, QColor(95, 125, 235, 32))
        bloom.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(QBrush(bloom))
        p.drawPath(clip)

        # Top-edge highlight shimmer
        hi = QLinearGradient(0, 0, 0, 48)
        hi.setColorAt(0, QColor(255, 255, 255, 20))
        hi.setColorAt(1, QColor(255, 255, 255, 0))
        p.setBrush(QBrush(hi))
        p.drawPath(clip)

        p.setClipping(False)

        # 1px border inside the rounded rect
        p.setPen(QPen(QColor(255, 255, 255, 24), 1.0))
        p.setBrush(Qt.NoBrush)
        border = QPainterPath()
        border.addRoundedRect(0.5, 0.5, W - 1.0, H - 1.0, R - 0.5, R - 0.5)
        p.drawPath(border)


# ──────────────────────────────────────────────────────
#  ENTRY
# ──────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("KeyVault")
    app.setStyle("Fusion")
    QFontDatabase.addApplicationFont(":/fonts/CascadiaCode.ttf")
    win = KeyVaultWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
