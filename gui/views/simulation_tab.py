"""
simulation_tab.py — Lance des simulations (shots/seed) et affiche les
probabilités de mesure sous forme de graphique et de tableau.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from widgets.common import Card, Pill, make_button, spacer_widget
from resources.theme import mpl_palette


class SimulationTab(QWidget):
    simulate_requested = pyqtSignal(int, int)

    def __init__(self):
        super().__init__()
        self.probabilites = {}
        self.mesures = {}
        self._theme = "dark"
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # --- Barre de contrôle ---
        controls = QHBoxLayout()
        controls.setSpacing(10)

        title = QLabel("Simulation")
        title.setObjectName("CardTitle")
        controls.addWidget(title)
        controls.addWidget(spacer_widget())

        controls.addWidget(QLabel("Shots"))
        self.shots_spin = QSpinBox()
        self.shots_spin.setRange(1, 100000)
        self.shots_spin.setValue(10)
        self.shots_spin.setFixedWidth(90)
        controls.addWidget(self.shots_spin)

        controls.addWidget(QLabel("Seed"))
        self.seed_spin = QSpinBox()
        self.seed_spin.setRange(0, 999999)
        self.seed_spin.setValue(42)
        self.seed_spin.setFixedWidth(90)
        controls.addWidget(self.seed_spin)

        self.run_btn = make_button("▶  Exécuter", object_name="SuccessButton",
                                    tooltip="Relancer la simulation avec ces paramètres")
        self.run_btn.clicked.connect(self._on_run)
        controls.addWidget(self.run_btn)

        layout.addLayout(controls)

        # --- Contenu (graphique + tableau) ---
        splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(splitter, stretch=1)

        graph_card = Card("Probabilités de mesure")
        self.figure = Figure(figsize=(10, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        graph_card.body.addWidget(self.canvas)
        splitter.addWidget(graph_card)

        results_card = Card("Résultats détaillés")
        self.summary_pill = Pill("Aucune mesure effectuée", status="muted")
        results_card.add_header_widget(self.summary_pill)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["État", "Probabilité", "Fréquence estimée"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        results_card.body.addWidget(self.table)
        splitter.addWidget(results_card)

        splitter.setSizes([380, 280])

        self._draw_placeholder()

    # ---------------------------------------------------------------- Thème
    def apply_theme(self, theme_name):
        self._theme = theme_name
        if self.probabilites:
            self._afficher_graphique()
        else:
            self._draw_placeholder()

    # ---------------------------------------------------------------- Slots
    def _on_run(self):
        self.simulate_requested.emit(self.shots_spin.value(), self.seed_spin.value())

    def update_content(self, resultat):
        sim = resultat.get("simulation", {})
        self.probabilites = sim.get("probabilites", {})
        self.mesures = sim.get("mesures_obtenues", {})

        self._afficher_graphique()
        self._afficher_tableau()

        if self.mesures:
            texte = " | ".join(f"c{idx}={val}" for idx, val in sorted(self.mesures.items()))
            self.summary_pill.set_status("ok", f"Mesures : {texte}")
        elif self.probabilites:
            self.summary_pill.set_status(
                "running", f"{len(self.probabilites)} états possibles — cliquez sur Exécuter pour mesurer"
            )
        else:
            self.summary_pill.set_status("muted", "Aucune mesure effectuée")

    # -------------------------------------------------------------- Dessin
    def _draw_placeholder(self):
        pal = mpl_palette(self._theme)
        self.figure.clear()
        self.figure.patch.set_facecolor(pal["figure_bg"])
        ax = self.figure.add_subplot(111)
        ax.set_facecolor(pal["axes_bg"])
        ax.text(0.5, 0.5, "Compilez et exécutez un code QuantL\npour visualiser les probabilités",
                ha='center', va='center', fontsize=12, color=pal["muted"], transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_frame_on(False)
        self.canvas.draw()

    def _afficher_graphique(self):
        pal = mpl_palette(self._theme)
        self.figure.clear()
        self.figure.patch.set_facecolor(pal["figure_bg"])
        ax = self.figure.add_subplot(111)
        ax.set_facecolor(pal["axes_bg"])

        if self.probabilites:
            etats = sorted(self.probabilites.keys())
            probs = [self.probabilites[e] for e in etats]
            colors = [pal["accent"] if p > 0.01 else pal["muted"] for p in probs]

            bars = ax.bar(etats, probs, color=colors, alpha=0.9, edgecolor=pal["grid"], linewidth=0.6)
            for bar, prob in zip(bars, probs):
                if prob > 0.01:
                    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                            f'{prob:.3f}', ha='center', va='bottom', fontsize=9, color=pal["text"])

            ax.set_xlabel("État", fontsize=11, color=pal["text"])
            ax.set_ylabel("Probabilité", fontsize=11, color=pal["text"])
            ax.set_ylim(0, 1.15)
            ax.grid(axis='y', alpha=0.3, linestyle='--', color=pal["grid"])
            ax.tick_params(colors=pal["text"])
            for spine in ax.spines.values():
                spine.set_color(pal["grid"])
            self.figure.tight_layout()
        else:
            ax.text(0.5, 0.5, "Aucune donnée de simulation", ha='center', va='center',
                    fontsize=13, color=pal["muted"], transform=ax.transAxes)
            ax.set_xticks([])
            ax.set_yticks([])

        self.canvas.draw()

    def _afficher_tableau(self):
        self.table.setRowCount(0)

        if not self.probabilites:
            self.table.setRowCount(1)
            item = QTableWidgetItem("Aucune donnée")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(0, 0, item)
            return

        etats = sorted(self.probabilites.keys())
        total_shots = self.shots_spin.value() if self.mesures else 100

        self.table.setRowCount(len(etats))
        for i, etat in enumerate(etats):
            prob = self.probabilites[etat]

            item = QTableWidgetItem(f"|{etat}⟩")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 0, item)

            prob_item = QTableWidgetItem(f"{prob:.4f}")
            prob_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 1, prob_item)

            freq_item = QTableWidgetItem(str(int(round(prob * total_shots))))
            freq_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 2, freq_item)

        self.table.resizeColumnsToContents()
