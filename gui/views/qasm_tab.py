"""
qasm_tab.py — Affiche le code OpenQASM 2.0 généré par le compilateur,
compatible avec IBM Qiskit.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel

from widgets.output_panel import OutputPanel
from widgets.code_editor import QASMHighlighter
from widgets.common import make_button, Pill, spacer_widget


class QASMTab(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("Export OpenQASM 2.0")
        title.setObjectName("CardTitle")
        header.addWidget(title)
        subtitle = QLabel("Compatible avec IBM Qiskit")
        subtitle.setObjectName("MutedLabel")
        header.addWidget(subtitle)
        header.addWidget(spacer_widget())

        self.validate_btn = make_button("Valider la syntaxe", object_name="GhostButton")
        self.validate_btn.clicked.connect(self._valider)
        header.addWidget(self.validate_btn)

        self.status_pill = Pill("En attente", status="muted")
        header.addWidget(self.status_pill)

        layout.addLayout(header)

        self.panel = OutputPanel(
            highlighter_cls=QASMHighlighter,
            placeholder="// Aucun code QASM généré — compilez un code QuantL",
            default_filename="circuit.qasm",
            file_filter="Fichiers QASM (*.qasm);;Tous les fichiers (*)",
        )
        layout.addWidget(self.panel, stretch=1)

    def update_content(self, resultat):
        qasm = resultat.get("qasm", "")
        if qasm:
            self.panel.set_text(qasm)
            nb_lignes = len(qasm.split(chr(10)))
            self.status_pill.set_status("ok", f"{nb_lignes} lignes générées")
        else:
            self.panel.set_text("// Aucun code QASM généré")
            self.status_pill.set_status("muted", "Aucun code")

    def _valider(self):
        qasm = self.panel.text()
        if not qasm.strip():
            self.status_pill.set_status("error", "Code QASM vide")
            return

        erreurs = []
        if "OPENQASM" not in qasm:
            erreurs.append("déclaration 'OPENQASM' manquante")
        if "include" not in qasm:
            erreurs.append("include 'qelib1.inc' manquant")

        if erreurs:
            self.status_pill.set_status("warn", "Problèmes : " + "; ".join(erreurs))
        else:
            self.status_pill.set_status("ok", "Syntaxe valide")
