"""
lexical_tab.py — Affiche les résultats des phases lexicale / syntaxique du
compilateur : arbre syntaxique abstrait (AST), représentation intermédiaire
(IR) et flux de tokens.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget

from widgets.output_panel import OutputPanel
from widgets.code_editor import ASTHighlighter, IRHighlighter
from widgets.common import spacer_widget


class LexicalTab(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("Analyse lexicale et syntaxique")
        title.setObjectName("CardTitle")
        header.addWidget(title)
        header.addWidget(spacer_widget())
        self.stats_label = QLabel("")
        self.stats_label.setObjectName("MutedLabel")
        header.addWidget(self.stats_label)
        layout.addLayout(header)

        self.inner_tabs = QTabWidget()
        self.inner_tabs.setDocumentMode(True)
        layout.addWidget(self.inner_tabs, stretch=1)

        self.ast_panel = OutputPanel(
            highlighter_cls=ASTHighlighter,
            placeholder="// Aucun AST généré — compilez un code QuantL",
            default_filename="ast.txt",
        )
        self.inner_tabs.addTab(self.ast_panel, "Arbre syntaxique (AST)")

        self.ir_panel = OutputPanel(
            highlighter_cls=IRHighlighter,
            placeholder="// Aucun IR généré — compilez un code QuantL",
            default_filename="ir.txt",
        )
        self.inner_tabs.addTab(self.ir_panel, "Représentation intermédiaire (IR)")

        self.tokens_panel = OutputPanel(
            placeholder="// Aucun token trouvé",
            default_filename="tokens.txt",
            show_line_numbers=False,
        )
        self.inner_tabs.addTab(self.tokens_panel, "Tokens")

    def update_content(self, resultat):
        ast = resultat.get("ast", "")
        self.ast_panel.set_text(ast if ast else "// Aucun AST généré")

        ir = resultat.get("ir", "")
        self.ir_panel.set_text(ir if ir else "// Aucun IR généré")

        self.tokens_panel.set_text(self._generer_tokens(ast))

        nb_ast_lines = len(ast.split('\n')) if ast else 0
        nb_ir_lines = len(ir.split('\n')) if ir else 0
        self.stats_label.setText(f"AST : {nb_ast_lines} lignes   •   IR : {nb_ir_lines} lignes")

    @staticmethod
    def _generer_tokens(ast):
        """Reconstruit une vue simplifiée des tokens à partir de l'AST."""
        tokens = []
        if ast:
            for line in ast.split('\n'):
                if 'DECL_QREG' in line:
                    tokens.append(f"QREG      {line.split('DECL_QREG')[1].strip()}")
                elif 'DECL_CREG' in line:
                    tokens.append(f"CREG      {line.split('DECL_CREG')[1].strip()}")
                elif 'PORTE_1Q' in line:
                    parts = line.split('PORTE_1Q')[1].strip().split()
                    if parts:
                        tokens.append(f"PORTE_1Q  {parts[0]}")
                elif 'PORTE_2Q' in line:
                    parts = line.split('PORTE_2Q')[1].strip().split()
                    if parts:
                        tokens.append(f"PORTE_2Q  {parts[0]}")

        if not tokens:
            return "// Aucun token trouvé"

        return "\n".join(["=== TOKENS ===", ""] + tokens)
