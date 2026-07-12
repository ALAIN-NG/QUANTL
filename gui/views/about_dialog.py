"""
about_dialog.py — Boîte de dialogue "À propos" de QuantL.

Remplace l'ancien onglet "À propos" : ce contenu est consulté rarement,
il n'a donc pas besoin de monopoliser un onglet permanent dans
l'interface principale. Accessible depuis le menu Aide.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QDialogButtonBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from widgets.common import Card


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("À propos de QuantL")
        self.setMinimumWidth(460)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 20)

        title = QLabel("QuantL")
        title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Compilateur quantique — Version 1.0")
        subtitle.setObjectName("MutedLabel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        desc = QLabel(
            "Conçu et implémenté dans le cadre du module <b>Traduction et "
            "Compilation</b> — Master 1 Informatique<br>Université de Yaoundé I"
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        gates_card = Card("Portes supportées")
        gates_text = QLabel(
            "<b>1 qubit :</b> H, X, Y, Z, S, T, RX, RY, RZ<br>"
            "<b>2 qubits :</b> CX, CZ, SWAP<br>"
            "<b>3 qubits :</b> TOFFOLI (CCX)<br>"
            "<b>Instructions :</b> qreg, creg, measure, if, print, barrier, repeat"
        )
        gates_text.setWordWrap(True)
        gates_card.body.addWidget(gates_text)
        layout.addWidget(gates_card)

        shortcuts_card = Card("Raccourcis clavier")
        shortcuts_layout = QVBoxLayout()
        shortcuts_layout.setSpacing(4)
        for combo, action in [
            ("Ctrl+Entrée", "Compiler"),
            ("Ctrl+O", "Ouvrir un fichier"),
            ("Ctrl+S", "Enregistrer"),
            ("Ctrl+Maj+S", "Enregistrer sous"),
            ("Ctrl+Q", "Quitter"),
        ]:
            row = QHBoxLayout()
            key_label = QLabel(f"<b>{combo}</b>")
            row.addWidget(key_label)
            row.addStretch()
            row.addWidget(QLabel(action))
            shortcuts_layout.addLayout(row)
        shortcuts_card.body.addLayout(shortcuts_layout)
        layout.addWidget(shortcuts_card)

        footer = QLabel("© 2025 — Université de Yaoundé I")
        footer.setObjectName("MutedLabel")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        buttons.button(QDialogButtonBox.StandardButton.Close).clicked.connect(self.accept)
        layout.addWidget(buttons)
