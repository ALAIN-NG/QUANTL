"""
code_editor.py — Éditeur de texte avec règle de numéros de ligne, mise en
surbrillance de la ligne courante, marquage d'erreurs, et surligneurs
syntaxiques pour QuantL / IR / AST / OpenQASM 2.0.
"""
import re

from PyQt6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit
from PyQt6.QtCore import Qt, QRect, QSize, pyqtSignal
from PyQt6.QtGui import (
    QFont, QColor, QPainter, QTextFormat, QTextCharFormat,
    QSyntaxHighlighter, QTextCursor
)


# ---------------------------------------------------------------------------
# Surligneurs syntaxiques
# ---------------------------------------------------------------------------
class _RuleHighlighter(QSyntaxHighlighter):
    """Base générique : applique une liste de règles (regex, format)."""

    def __init__(self, document, rules):
        super().__init__(document)
        self._rules = rules

    def highlightBlock(self, text):
        for pattern, fmt in self._rules:
            for match in pattern.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, fmt)


def _fmt(color, bold=False, italic=False):
    f = QTextCharFormat()
    f.setForeground(QColor(color))
    if bold:
        f.setFontWeight(QFont.Weight.Bold)
    if italic:
        f.setFontItalic(True)
    return f


class QuantLHighlighter(_RuleHighlighter):
    """Coloration syntaxique du langage source QuantL (.qtl)."""

    KEYWORDS = [
        "qreg", "creg", "h", "x", "y", "z", "s", "t", "rx", "ry", "rz",
        "cx", "cz", "swap", "toffoli", "measure", "if", "print",
        "barrier", "repeat", "probs", "state",
    ]

    def __init__(self, document):
        keyword_fmt = _fmt("#7aa2f7", bold=True)
        comment_fmt = _fmt("#6c8f5e", italic=True)
        number_fmt = _fmt("#e0af68")
        string_fmt = _fmt("#9ece6a")
        operator_fmt = _fmt("#c0caf5")
        register_fmt = _fmt("#f7768e")

        rules = []
        for kw in self.KEYWORDS:
            rules.append((re.compile(r"\b" + kw + r"\b"), keyword_fmt))
        rules.append((re.compile(r"//[^\n]*"), comment_fmt))
        rules.append((re.compile(r"\b[0-9]+\.[0-9]+\b"), number_fmt))
        rules.append((re.compile(r"\b[0-9]+\b"), number_fmt))
        rules.append((re.compile(r'"[^"]*"'), string_fmt))
        rules.append((re.compile(r"->|==|!=|<=|>="), operator_fmt))
        rules.append((re.compile(r"\b[qc]\[\d+\]"), register_fmt))
        super().__init__(document, rules)


class QASMHighlighter(_RuleHighlighter):
    """Coloration syntaxique pour OpenQASM 2.0."""

    KEYWORDS = [
        "OPENQASM", "include", "qreg", "creg", "gate", "measure",
        "barrier", "if", "h", "x", "y", "z", "s", "t", "sdg", "tdg",
        "rx", "ry", "rz", "cx", "cz", "swap", "ccx", "u", "u1", "u2", "u3",
    ]

    def __init__(self, document):
        keyword_fmt = _fmt("#7aa2f7", bold=True)
        comment_fmt = _fmt("#6c8f5e", italic=True)
        number_fmt = _fmt("#e0af68")
        string_fmt = _fmt("#9ece6a")

        rules = []
        for kw in self.KEYWORDS:
            rules.append((re.compile(r"\b" + kw + r"\b"), keyword_fmt))
        rules.append((re.compile(r"//[^\n]*"), comment_fmt))
        rules.append((re.compile(r'"[^"]*"'), string_fmt))
        rules.append((re.compile(r"\b[0-9]+\.[0-9]+\b"), number_fmt))
        rules.append((re.compile(r"\b[0-9]+\b"), number_fmt))
        super().__init__(document, rules)


class ASTHighlighter(_RuleHighlighter):
    """Coloration des noeuds dans le dump texte de l'AST."""

    NODE_COLORS = {
        "DECL_QREG": "#7dcfff", "DECL_CREG": "#7dcfff",
        "PORTE_1Q": "#9ece6a", "PORTE_2Q": "#e0af68",
        "TOFFOLI": "#bb9af7", "MESURE": "#f7768e",
        "IF": "#7aa2f7", "PRINT": "#bb9af7",
        "BARRIER": "#e0af68", "REPEAT": "#7dcfff",
    }

    def __init__(self, document):
        rules = []
        for node, color in self.NODE_COLORS.items():
            rules.append((re.compile(r"\b" + node + r"\b"), _fmt(color, bold=True)))
        rules.append((re.compile(r"\bq\[\d+\]|\bc\[\d+\]"), _fmt("#f7768e")))
        rules.append((re.compile(r"\(ligne \d+\)"), _fmt("#6c6f82", italic=True)))
        super().__init__(document, rules)


class IRHighlighter(_RuleHighlighter):
    """Coloration des lignes '[IR] OPCODE ...'."""

    OPCODE_COLORS = {
        "H": "#9ece6a", "X": "#f7768e", "Y": "#7dcfff", "Z": "#bb9af7",
        "S": "#e0af68", "T": "#e0af68", "RX": "#7dcfff", "RY": "#7dcfff",
        "RZ": "#7dcfff", "CX": "#e0af68", "CZ": "#e0af68", "SWAP": "#bb9af7",
        "TOFFOLI": "#bb9af7", "MEASURE": "#f7768e", "PRINT_PROBS": "#7aa2f7",
        "PRINT_STATE": "#7aa2f7", "BARRIER": "#6c6f82",
    }

    def __init__(self, document):
        rules = [(re.compile(r"\[IR\]"), _fmt("#6c6f82"))]
        for op, color in self.OPCODE_COLORS.items():
            rules.append((re.compile(r"\b" + op + r"\b"), _fmt(color, bold=True)))
        rules.append((re.compile(r"\bq\[\d+\]|\bc\[\d+\]"), _fmt("#f7768e")))
        rules.append((re.compile(r"\(ligne \d+\)"), _fmt("#6c6f82", italic=True)))
        super().__init__(document, rules)


# ---------------------------------------------------------------------------
# Éditeur avec règle de numéros de ligne
# ---------------------------------------------------------------------------
class _LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self):
        return QSize(self._editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self._editor.paint_line_numbers(event)


class CodeEditor(QPlainTextEdit):
    """QPlainTextEdit enrichi : numéros de ligne, ligne courante en
    surbrillance, marquage d'erreurs de compilation, police monospace."""

    cursor_info_changed = pyqtSignal(int, int)

    def __init__(self, parent=None, read_only=False, show_line_numbers=True):
        super().__init__(parent)
        self._show_line_numbers = show_line_numbers
        self._error_lines = {}  # ligne (1-based) -> message

        font = QFont("JetBrains Mono")
        if not font.exactMatch():
            font = QFont("Consolas")
        if not font.exactMatch():
            font = QFont("Courier New")
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setPointSize(11)
        self.setFont(font)
        self.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(' '))
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setReadOnly(read_only)
        self.setFrameShape(QPlainTextEdit.Shape.NoFrame)

        self._line_area = _LineNumberArea(self)
        self.blockCountChanged.connect(self._update_line_area_width)
        self.updateRequest.connect(self._update_line_area)
        self.cursorPositionChanged.connect(self._on_cursor_changed)
        self.cursorPositionChanged.connect(self._highlight_current_line)

        self._update_line_area_width(0)
        self._highlight_current_line()

    # -- numéros de ligne --------------------------------------------------
    def line_number_area_width(self):
        if not self._show_line_numbers:
            return 0
        digits = max(2, len(str(max(1, self.blockCount()))))
        return 14 + self.fontMetrics().horizontalAdvance('9') * digits

    def _update_line_area_width(self, _=0):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _update_line_area(self, rect, dy):
        if dy:
            self._line_area.scroll(0, dy)
        else:
            self._line_area.update(0, rect.y(), self._line_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_line_area_width()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def paint_line_numbers(self, event):
        if not self._show_line_numbers:
            return
        painter = QPainter(self._line_area)
        bg = self.palette().color(self.backgroundRole())
        painter.fillRect(event.rect(), bg.darker(106) if bg.lightness() > 128 else bg.lighter(112))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        fg = QColor("#6c6f82")
        error_fg = QColor("#f7768e")
        current_line = self.textCursor().blockNumber()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                is_error = (block_number + 1) in self._error_lines
                painter.setPen(error_fg if is_error else (
                    QColor("#e7e7f1") if block_number == current_line else fg))
                painter.drawText(
                    0, int(top), self._line_area.width() - 6, self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight, number
                )
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1
        painter.end()

    # -- ligne courante / erreurs -------------------------------------------
    def _highlight_current_line(self):
        selections = []

        if not self.isReadOnly():
            sel = QTextEdit.ExtraSelection()
            base = self.palette().color(self.backgroundRole())
            line_color = base.lighter(118) if base.lightness() < 128 else base.darker(104)
            sel.format.setBackground(line_color)
            sel.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            sel.cursor = self.textCursor()
            sel.cursor.clearSelection()
            selections.append(sel)

        for line, _msg in self._error_lines.items():
            block = self.document().findBlockByNumber(line - 1)
            if not block.isValid():
                continue
            sel = QTextEdit.ExtraSelection()
            sel.format.setBackground(QColor(247, 118, 142, 40))
            sel.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            cursor = QTextCursor(block)
            sel.cursor = cursor
            selections.append(sel)

        self.setExtraSelections(selections)

    def _on_cursor_changed(self):
        cursor = self.textCursor()
        self.cursor_info_changed.emit(cursor.blockNumber() + 1, cursor.columnNumber() + 1)

    # -- API publique --------------------------------------------------------
    def set_error_line(self, line, message):
        self._error_lines[line] = message
        self._highlight_current_line()
        self._line_area.update()

    def clear_errors(self):
        self._error_lines = {}
        self._highlight_current_line()
        self._line_area.update()

    def goto_line(self, line):
        block = self.document().findBlockByNumber(max(0, line - 1))
        if block.isValid():
            cursor = QTextCursor(block)
            self.setTextCursor(cursor)
            self.centerCursor()
            self.setFocus()
