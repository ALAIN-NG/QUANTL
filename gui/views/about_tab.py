from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QGroupBox, QHBoxLayout, QTabWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QFont

class AboutTab(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Titre
        title = QLabel("🧪 QuantL")
        title.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("Compilateur Quantique - Version 1.0")
        subtitle.setFont(QFont("Arial", 14))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #888;")
        layout.addWidget(subtitle)
        
        # Description
        desc = QLabel(
            "Conçu et implémenté dans le cadre du module "
            "<b>Traduction et Compilation</b> - Master 1 Informatique\n"
            "Université de Yaoundé I"
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Tableau des portes
        gates_group = QGroupBox("🔬 Portes supportées")
        gates_layout = QVBoxLayout()
        
        gates_text = QLabel(
            "<b>Portes 1 qubit :</b> H, X, Y, Z, S, T, RX, RY, RZ<br>"
            "<b>Portes 2 qubits :</b> CX, CZ, SWAP<br>"
            "<b>Portes 3 qubits :</b> TOFFOLI<br>"
            "<b>Instructions :</b> qreg, creg, measure, if, print, barrier, repeat"
        )
        gates_text.setWordWrap(True)
        gates_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gates_layout.addWidget(gates_text)
        
        gates_group.setLayout(gates_layout)
        layout.addWidget(gates_group)
        
        # Raccourcis clavier
        shortcuts_group = QGroupBox("⌨️ Raccourcis clavier")
        shortcuts_layout = QVBoxLayout()
        
        shortcuts_text = QLabel(
            "<b>Ctrl+Enter</b> : Compiler<br>"
            "<b>Ctrl+O</b> : Ouvrir un fichier<br>"
            "<b>Ctrl+S</b> : Sauvegarder<br>"
            "<b>Ctrl+Q</b> : Quitter"
        )
        shortcuts_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        shortcuts_layout.addWidget(shortcuts_text)
        
        shortcuts_group.setLayout(shortcuts_layout)
        layout.addWidget(shortcuts_group)
        
        # Boutons de thème
        theme_group = QGroupBox("🎨 Thème")
        theme_layout = QHBoxLayout()
        
        self.dark_btn = QPushButton("🌙 Sombre")
        self.dark_btn.clicked.connect(lambda: self._switch_theme("dark"))
        theme_layout.addWidget(self.dark_btn)
        
        self.light_btn = QPushButton("☀️ Clair")
        self.light_btn.clicked.connect(lambda: self._switch_theme("light"))
        theme_layout.addWidget(self.light_btn)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # Footer
        footer = QLabel("© 2025 - Université de Yaoundé I")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("color: #888; padding-top: 20px;")
        layout.addWidget(footer)
        
        layout.addStretch()
    
    def _switch_theme(self, theme):
        """Change le thème de l'application"""
        # Signaler le changement de thème
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            # Appliquer le style
            if theme == "dark":
                style = """
                    QMainWindow { background-color: #1e1e1e; }
                    QTabWidget::pane { background-color: #252526; }
                    QTabBar::tab { background-color: #2d2d30; color: #cccccc; }
                    QTabBar::tab:selected { background-color: #1e1e1e; }
                """
            else:
                style = """
                    QMainWindow { background-color: #f5f5f5; }
                    QTabWidget::pane { background-color: #ffffff; }
                """
            app.setStyleSheet(style)