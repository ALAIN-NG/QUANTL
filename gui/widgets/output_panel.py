"""
output_panel.py — Panneau générique pour afficher un contenu texte en lecture
seule (AST, IR, tokens, QASM, console...) avec actions Copier / Sauvegarder.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QApplication, QFileDialog, QMessageBox
)

from widgets.code_editor import CodeEditor
from widgets.common import make_button


class OutputPanel(QWidget):
    """En-tête (titre + actions) + zone de texte en lecture seule."""

    def __init__(self, title="", highlighter_cls=None, placeholder="",
                 default_filename="export.txt", file_filter="Tous les fichiers (*)",
                 show_line_numbers=True, parent=None):
        super().__init__(parent)
        self._default_filename = default_filename
        self._file_filter = file_filter

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        header = QHBoxLayout()
        if title:
            title_label = QLabel(title)
            title_label.setObjectName("SectionTitle")
            header.addWidget(title_label)
        header.addStretch()

        self.copy_btn = make_button("Copier", object_name="GhostButton", tooltip="Copier dans le presse-papier")
        self.copy_btn.clicked.connect(self._copy)
        header.addWidget(self.copy_btn)

        self.save_btn = make_button("Enregistrer", object_name="GhostButton", tooltip="Enregistrer dans un fichier")
        self.save_btn.clicked.connect(self._save)
        header.addWidget(self.save_btn)

        layout.addLayout(header)

        self.view = CodeEditor(read_only=True, show_line_numbers=show_line_numbers)
        self.view.setPlaceholderText(placeholder)
        if highlighter_cls is not None:
            self._highlighter = highlighter_cls(self.view.document())
        layout.addWidget(self.view)

    def set_text(self, text):
        self.view.setPlainText(text)

    def text(self):
        return self.view.toPlainText()

    def append(self, text, color=None):
        from PyQt6.QtGui import QTextCharFormat, QColor
        cursor = self.view.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        fmt = QTextCharFormat()
        if color:
            fmt.setForeground(QColor(color))
        cursor.insertText(text, fmt)
        self.view.setTextCursor(cursor)

    def clear(self):
        self.view.clear()

    def scroll_to_end(self):
        cursor = self.view.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.view.setTextCursor(cursor)

    def _copy(self):
        QApplication.clipboard().setText(self.view.toPlainText())

    def _save(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer", self._default_filename, self._file_filter
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.view.toPlainText())
        except OSError as e:
            QMessageBox.critical(self, "Erreur", f"Impossible d'enregistrer :\n{e}")
