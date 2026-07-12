"""
common.py — Petits composants réutilisés dans plusieurs onglets pour garder
une interface visuellement cohérente (cartes, badges de statut, boutons).
"""
from PyQt6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy
)
from PyQt6.QtCore import Qt


class Card(QFrame):
    """Conteneur avec en-tête (titre + actions) et corps, style 'carte'."""

    def __init__(self, title="", subtitle="", parent=None):
        super().__init__(parent)
        self.setObjectName("Card")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 16)
        outer.setSpacing(10)

        self._header = QHBoxLayout()
        self._header.setSpacing(8)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("CardTitle")
        title_box.addWidget(self.title_label)

        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setObjectName("CardSubtitle")
        self.subtitle_label.setVisible(bool(subtitle))
        title_box.addWidget(self.subtitle_label)

        self._header.addLayout(title_box)
        self._header.addStretch()

        outer.addLayout(self._header)

        self.body = QVBoxLayout()
        self.body.setSpacing(8)
        outer.addLayout(self.body)

        if not title:
            self.title_label.setVisible(False)
            self.subtitle_label.setVisible(False)

    def add_header_widget(self, widget):
        """Ajoute un widget (bouton, badge...) aligné à droite de l'en-tête."""
        self._header.addWidget(widget)

    def set_subtitle(self, text):
        self.subtitle_label.setText(text)
        self.subtitle_label.setVisible(bool(text))


class Pill(QLabel):
    """Badge de statut coloré (ex: 'Prêt', 'Erreur', 'Compilation...')."""

    STATUSES = {
        "ok": "PillOk",
        "error": "PillError",
        "warn": "PillWarn",
        "muted": "PillMuted",
        "running": "PillRunning",
    }

    def __init__(self, text="", status="muted", parent=None):
        super().__init__(text, parent)
        self.setObjectName("Pill")
        self.set_status(status)

    def set_status(self, status: str, text: str | None = None):
        if text is not None:
            self.setText(text)
        self.setProperty("_status", status)
        self.setObjectName(self.STATUSES.get(status, "PillMuted"))
        style = self.style()
        style.unpolish(self)
        style.polish(self)


def make_button(text, object_name=None, tooltip=None, checkable=False):
    """Fabrique un QPushButton pré-stylé (utilise les objectName du QSS)."""
    btn = QPushButton(text)
    if object_name:
        btn.setObjectName(object_name)
    if tooltip:
        btn.setToolTip(tooltip)
    btn.setCheckable(checkable)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


def spacer_widget():
    w = QWidget()
    w.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    return w
