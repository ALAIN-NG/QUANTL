"""
editor_tab.py — Panneau d'édition du code source QuantL (.qtl).

Ce panneau reste visible en permanence à gauche de la fenêtre principale
(voir main_window.py) afin que l'utilisateur puisse modifier son code tout
en consultant les résultats de compilation dans les onglets de droite.
"""
import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFileDialog, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, Qt

from widgets.code_editor import CodeEditor, QuantLHighlighter
from widgets.common import make_button, spacer_widget


class EditorTab(QWidget):
    compile_requested = pyqtSignal()
    content_modified = pyqtSignal(bool)     # True si des changements non sauvegardés existent
    cursor_moved = pyqtSignal(int, int)     # ligne, colonne

    def __init__(self):
        super().__init__()
        self.fichier_courant = None
        self._dirty = False
        self._loading = False
        self._setup_ui()
        self._connect_signals()

    # ------------------------------------------------------------------ UI
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # --- Barre d'outils ---
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        self.file_label = QLabel("Nouveau fichier")
        self.file_label.setObjectName("SectionTitle")
        toolbar.addWidget(self.file_label)

        self.dirty_dot = QLabel("●")
        self.dirty_dot.setStyleSheet("color: #e0af68; font-size: 16px;")
        self.dirty_dot.setVisible(False)
        toolbar.addWidget(self.dirty_dot)

        toolbar.addWidget(spacer_widget())

        self.load_btn = make_button("Ouvrir", object_name="GhostButton", tooltip="Ouvrir un fichier .qtl (Ctrl+O)")
        toolbar.addWidget(self.load_btn)

        self.save_btn = make_button("Enregistrer", object_name="GhostButton", tooltip="Enregistrer (Ctrl+S)")
        toolbar.addWidget(self.save_btn)

        self.compile_btn = make_button("▶  Compiler", object_name="PrimaryButton",
                                        tooltip="Compiler le code (Ctrl+Entrée)")
        toolbar.addWidget(self.compile_btn)

        layout.addLayout(toolbar)

        # --- Éditeur ---
        self.editor = CodeEditor()
        self.editor.setPlaceholderText(
            "Écrivez votre code QuantL ici...\n\n"
            "Exemple :\n"
            "qreg q[2];\n"
            "creg c[2];\n"
            "h q[0];\n"
            "cx q[0], q[1];\n"
            "measure q[0] -> c[0];\n"
            "print probs;"
        )
        self.highlighter = QuantLHighlighter(self.editor.document())
        layout.addWidget(self.editor, stretch=1)

        # --- Barre de statut basse ---
        footer = QHBoxLayout()
        self.status_label = QLabel("Prêt")
        self.status_label.setObjectName("MutedLabel")
        footer.addWidget(self.status_label)
        footer.addWidget(spacer_widget())
        self.position_label = QLabel("Ligne 1, Col 1")
        self.position_label.setObjectName("MutedLabel")
        footer.addWidget(self.position_label)
        layout.addLayout(footer)

    def _connect_signals(self):
        self.editor.cursor_info_changed.connect(self._update_cursor_info)
        self.editor.textChanged.connect(self._on_text_changed)
        self.load_btn.clicked.connect(self.open_file_dialog)
        self.save_btn.clicked.connect(self.save_file)
        self.compile_btn.clicked.connect(self.compile_requested.emit)

    # -------------------------------------------------------------- Slots
    def _update_cursor_info(self, line, col):
        self.position_label.setText(f"Ligne {line}, Col {col}")
        self.cursor_moved.emit(line, col)

    def _on_text_changed(self):
        if self._loading:
            return
        self.editor.clear_errors()
        self._set_dirty(True)

    def _set_dirty(self, dirty):
        self._dirty = dirty
        self.dirty_dot.setVisible(dirty)
        self.status_label.setText("Modifié" if dirty else "Prêt")
        self.content_modified.emit(dirty)

    # ------------------------------------------------------------- Fichiers
    def open_file_dialog(self):
        if not self._confirm_discard_changes():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Ouvrir un fichier QuantL", "", "Fichiers QuantL (*.qtl);;Tous les fichiers (*)"
        )
        if path:
            self.load_file(path)

    def load_file(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                code = f.read()
        except OSError as e:
            QMessageBox.critical(self, "Erreur", f"Impossible d'ouvrir le fichier :\n{e}")
            return False
        self.set_code(code)
        self.fichier_courant = path
        self._set_dirty(False)
        self.file_label.setText(os.path.basename(path))
        self.status_label.setText(f"Fichier chargé : {path}")
        return True

    def save_file(self):
        if not self.fichier_courant:
            return self.save_file_as()
        return self._write_to(self.fichier_courant)

    def save_file_as(self):
        default_name = self.fichier_courant or "circuit.qtl"
        path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer le fichier QuantL", default_name, "Fichiers QuantL (*.qtl)"
        )
        if not path:
            return False
        return self._write_to(path)

    def _write_to(self, path):
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.editor.toPlainText())
        except OSError as e:
            QMessageBox.critical(self, "Erreur", f"Impossible d'enregistrer :\n{e}")
            return False
        self.fichier_courant = path
        self._set_dirty(False)
        self.file_label.setText(os.path.basename(path))
        self.status_label.setText(f"Enregistré : {path}")
        return True

    def _confirm_discard_changes(self):
        """Retourne False si l'utilisateur annule l'action en cours."""
        if not self._dirty:
            return True
        reponse = QMessageBox.question(
            self, "Modifications non enregistrées",
            "Le fichier courant contient des modifications non enregistrées.\n"
            "Voulez-vous les enregistrer avant de continuer ?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
        )
        if reponse == QMessageBox.StandardButton.Cancel:
            return False
        if reponse == QMessageBox.StandardButton.Save:
            return self.save_file()
        return True

    def has_unsaved_changes(self):
        return self._dirty

    # ---------------------------------------------------------------- API
    def get_code(self):
        return self.editor.toPlainText()

    def set_code(self, code):
        self._loading = True
        self.editor.setPlainText(code)
        self._loading = False
        self.editor.clear_errors()

    def load_example(self, nom, code):
        self.set_code(code)
        self.fichier_courant = None
        self._set_dirty(False)
        self.file_label.setText(f"Exemple : {nom}")

    def highlight_error(self, ligne, message):
        self.editor.set_error_line(ligne, message)
        self.editor.goto_line(ligne)
        self.status_label.setText(f"Erreur ligne {ligne} : {message}")

    def clear_highlights(self):
        self.editor.clear_errors()
        self.status_label.setText("Prêt")
