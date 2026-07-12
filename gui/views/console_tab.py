"""
console_tab.py — Journal des compilations : sortie standard, erreurs et
historique horodaté des exécutions du compilateur.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import QDateTime

from widgets.output_panel import OutputPanel
from widgets.common import make_button, Pill, spacer_widget


class ConsoleTab(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("Console de compilation")
        title.setObjectName("CardTitle")
        header.addWidget(title)
        header.addWidget(spacer_widget())

        self.status_pill = Pill("Prêt", status="muted")
        header.addWidget(self.status_pill)

        self.clear_btn = make_button("Effacer", object_name="GhostButton")
        self.clear_btn.clicked.connect(self.clear)
        header.addWidget(self.clear_btn)

        layout.addLayout(header)

        self.panel = OutputPanel(
            placeholder="// La sortie du compilateur s'affichera ici",
            default_filename="console.log",
            show_line_numbers=False,
        )
        layout.addWidget(self.panel, stretch=1)

    def update_content(self, resultat):
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")

        self.panel.append(f"\n{'─' * 64}\n", "#3a3d4d")
        self.panel.append(f"[{timestamp}] Compilation\n", "#7aa2f7")

        if resultat.get("stdout"):
            self.panel.append("\n— STDOUT —\n", "#6c6f82")
            self.panel.append(resultat["stdout"], "#c0caf5")

        if resultat.get("stderr"):
            self.panel.append("\n— STDERR —\n", "#6c6f82")
            self.panel.append(resultat["stderr"], "#f7768e")

        if resultat.get("erreurs"):
            self.panel.append("\n— ERREURS —\n", "#6c6f82")
            for err in resultat["erreurs"]:
                self.panel.append(f"⚠ {err}\n", "#f7768e")

        statut = resultat.get("statut", "unknown")
        if statut == "ok":
            self.panel.append("\n✓ Compilation réussie\n", "#9ece6a")
            self.status_pill.set_status("ok", f"[{timestamp}] Réussie")
        else:
            self.panel.append("\n✗ Compilation échouée\n", "#f7768e")
            self.status_pill.set_status("error", f"[{timestamp}] Échouée")

        self.panel.scroll_to_end()

    def clear(self):
        self.panel.clear()
        self.status_pill.set_status("muted", "Console effacée")
