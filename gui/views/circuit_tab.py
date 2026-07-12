"""
circuit_tab.py — Visualisation graphique du circuit quantique compilé.

Le circuit est dessiné avec Matplotlib sur un canevas clair (façon feuille
de schéma), quel que soit le thème de l'application, pour garder une bonne
lisibilité des portes quantiques. Le cadre qui l'entoure, lui, suit le
thème actif de l'application.
"""
import re

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFileDialog, QMessageBox, QScrollArea, QFrame, QSizePolicy
)

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch

from widgets.common import Card, Pill, make_button, spacer_widget


class CircuitRenderer:
    """Dessine un circuit quantique avec Matplotlib."""

    COLORS = {
        'h': {'bg': '#E8F5E9', 'border': '#2E7D32', 'text': '#1B5E20'},
        'x': {'bg': '#FFEBEE', 'border': '#C62828', 'text': '#B71C1C'},
        'y': {'bg': '#E3F2FD', 'border': '#1565C0', 'text': '#0D47A1'},
        'z': {'bg': '#F3E5F5', 'border': '#6A1B9A', 'text': '#4A148C'},
        's': {'bg': '#FFF3E0', 'border': '#E65100', 'text': '#BF360C'},
        't': {'bg': '#FBE9E7', 'border': '#BF360C', 'text': '#8D6E63'},
        'rx': {'bg': '#E0F7FA', 'border': '#00695C', 'text': '#004D40'},
        'ry': {'bg': '#E0F2F1', 'border': '#00695C', 'text': '#004D40'},
        'rz': {'bg': '#E8EAF6', 'border': '#283593', 'text': '#1A237E'},
        'cx': {'bg': '#FFF8E1', 'border': '#F57F17', 'text': '#E65100'},
        'cz': {'bg': '#FCE4EC', 'border': '#880E4F', 'text': '#4A148C'},
        'swap': {'bg': '#EFEBE9', 'border': '#4E342E', 'text': '#3E2723'},
        'toffoli': {'bg': '#ECEFF1', 'border': '#37474F', 'text': '#263238'},
        'measure': {'bg': '#FAFAFA', 'border': '#616161', 'text': '#424242'},
        'barrier': {'bg': '#F5F5F5', 'border': '#9E9E9E', 'text': '#757575'},
        'default': {'bg': '#F5F5F5', 'border': '#757575', 'text': '#424242'},
    }

    DISPLAY_NAMES = {
        'h': 'H', 'x': 'X', 'y': 'Y', 'z': 'Z', 's': 'S', 't': 'T',
        'rx': 'R_x', 'ry': 'R_y', 'rz': 'R_z',
        'cx': 'CNOT', 'cz': 'CZ', 'swap': 'SWAP', 'toffoli': 'CCX',
        'measure': 'M', 'barrier': '∥',
    }

    def __init__(self):
        self.qubits_data = {}
        self.nb_qubits = 0
        self.max_portes = 0
        self.circuit_name = ""

    def set_circuit(self, circuit_data):
        self.qubits_data = {}
        self.nb_qubits = 0
        self.max_portes = 0

        if not circuit_data:
            return

        for qubit_data in circuit_data:
            qubit = qubit_data.get("qubit", 0)
            portes = qubit_data.get("portes", [])
            self.qubits_data[qubit] = portes
            if qubit >= self.nb_qubits:
                self.nb_qubits = qubit + 1
            if len(portes) > self.max_portes:
                self.max_portes = len(portes)

        for i in range(self.nb_qubits):
            if i not in self.qubits_data:
                self.qubits_data[i] = []

    def draw(self, fig):
        ax = fig.add_subplot(111)

        if self.nb_qubits == 0 or not self.qubits_data:
            ax.text(0.5, 0.5, "Aucun circuit à afficher\n\nCompilez d'abord un code QuantL",
                    ha='center', va='center', fontsize=14, color='#9E9E9E',
                    transform=ax.transAxes)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_frame_on(False)
            return

        qubit_spacing = 0.4
        porte_width = 0.25
        porte_height = 0.20
        padding_top = 0.4
        padding_left = 0.8

        n_portes = self.max_portes
        total_width = padding_left + n_portes * (porte_width + 0.2) + 0.5
        total_height = self.nb_qubits * qubit_spacing + padding_top + 0.5

        # Taille de figure basée sur la géométrie réelle du circuit, plus une
        # marge fixe (en pouces) réservée en bas pour la légende, qui est
        # dessinée hors de la zone des axes (voir _draw_legend).
        fig_width = max(8.0, total_width * 1.15)
        fig_height = max(3.2, total_height * 1.3) + 0.9
        fig.set_size_inches(fig_width, fig_height)

        # Réserve l'espace nécessaire autour du tracé : le bas est dimensionné
        # pour que la bande de légende (~0.9 pouce) reste toujours visible,
        # quelle que soit la hauteur totale de la figure.
        bottom_margin = max(0.14, 0.9 / fig_height)
        top_margin = 0.90 if self.circuit_name else 0.95
        fig.subplots_adjust(left=0.05, right=0.98, top=top_margin, bottom=bottom_margin)

        for i in range(self.nb_qubits):
            y = padding_top + i * qubit_spacing
            ax.plot([0, total_width], [y, y], color='#37474F', linewidth=2.5, alpha=0.7, zorder=1)
            ax.text(-0.1, y, f'$q_{i}$', va='center', ha='right',
                    fontsize=12, fontweight='bold', color='#1A237E', zorder=2)
            circle = Circle((0.02, y), 0.04, facecolor='#1A237E', edgecolor='#1A237E', zorder=2)
            ax.add_patch(circle)

        for qubit, portes in self.qubits_data.items():
            y = padding_top + qubit * qubit_spacing

            for col, porte in enumerate(portes):
                x = padding_left + col * (porte_width + 0.2) + porte_width / 2

                nom = porte.get("nom", "").lower()
                params = porte.get("params", "")
                target = porte.get("target", -1)

                colors = self.COLORS.get(nom, self.COLORS['default'])

                if nom == 'barrier':
                    self._draw_barrier(ax, x, padding_top, colors, self.nb_qubits, qubit_spacing)
                    continue
                if nom == 'measure':
                    self._draw_measure(ax, x, y, porte_width, porte_height, colors, params)
                    continue
                if nom in ('cx', 'cz'):
                    self._draw_cnot(ax, x, y, porte_width, porte_height, nom, colors, target, padding_top, qubit_spacing)
                    continue
                if nom == 'swap':
                    self._draw_swap(ax, x, y, colors, target, padding_top, qubit_spacing)
                    continue
                if nom == 'toffoli':
                    self._draw_toffoli(ax, x, y, porte_width, porte_height, colors, qubit, padding_top, qubit_spacing)
                    continue

                self._draw_gate(ax, x, y, porte_width, porte_height, nom, colors, params)

        ax.set_xlim(-0.5, total_width + 0.5)
        ax.set_ylim(-0.2, self.nb_qubits * qubit_spacing + padding_top + 0.3)
        ax.set_aspect('equal')
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_frame_on(False)

        self._draw_legend(fig)

        if self.circuit_name:
            ax.set_title(self.circuit_name, fontsize=14, fontweight='bold', color='#1A237E', pad=15)

    def _draw_gate(self, ax, x, y, w, h, nom, colors, params):
        rect = FancyBboxPatch(
            (x - w / 2, y - h / 2), w, h,
            boxstyle="round,pad=0.05,rounding_size=0.08",
            facecolor=colors['bg'], edgecolor=colors['border'], linewidth=2, alpha=0.9, zorder=3
        )
        ax.add_patch(rect)
        inner_rect = FancyBboxPatch(
            (x - w / 2 + 0.03, y - h / 2 + 0.03), w - 0.06, h - 0.06,
            boxstyle="round,pad=0.02,rounding_size=0.05",
            facecolor='none', edgecolor=colors['border'], linewidth=0.5, alpha=0.3, zorder=4
        )
        ax.add_patch(inner_rect)

        display_name = self.DISPLAY_NAMES.get(nom, nom.upper())
        ax.text(x, y, display_name, va='center', ha='center',
                fontsize=11, fontweight='bold', color=colors['text'], zorder=5)

        if params and nom in ('rx', 'ry', 'rz'):
            ax.text(x, y - h / 2 - 0.08, f'θ={params}', va='top', ha='center',
                    fontsize=7, color='#757575', style='italic', zorder=3)

    def _draw_cnot(self, ax, x, y, w, h, nom, colors, target, padding_top, spacing):
        target_y = padding_top + target * spacing

        circle = Circle((x - w / 2 - 0.02, y), 0.1,
                         facecolor=colors['border'], edgecolor=colors['border'], linewidth=2, zorder=3)
        ax.add_patch(circle)
        ax.plot([x - w / 2 - 0.02, x - w / 2 - 0.02], [y, target_y],
                color=colors['border'], linewidth=2, alpha=0.6, zorder=2)

        rect = FancyBboxPatch(
            (x - w / 3, target_y - h / 3), w * 2 / 3, h * 2 / 3,
            boxstyle="round,pad=0.05,rounding_size=0.06",
            facecolor=colors['bg'], edgecolor=colors['border'], linewidth=2, alpha=0.9, zorder=3
        )
        ax.add_patch(rect)

        display_name = self.DISPLAY_NAMES.get(nom, nom.upper())
        ax.text(x, target_y, display_name, va='center', ha='center',
                fontsize=9, fontweight='bold', color=colors['text'], zorder=4)
        ax.plot([x - w / 2 - 0.02, x - w / 3], [target_y, target_y],
                color=colors['border'], linewidth=1.5, alpha=0.5, zorder=2)

    def _draw_swap(self, ax, x, y, colors, qubit2, padding_top, spacing):
        target_y = padding_top + qubit2 * spacing
        ax.plot([x, x], [y, target_y], color=colors['border'], linewidth=1.5, alpha=0.4, zorder=2)

        size = 0.1
        for y_pos in (y, target_y):
            ax.plot([x - size, x + size], [y_pos - size, y_pos + size],
                    color=colors['border'], linewidth=2.5, zorder=3)
            ax.plot([x - size, x + size], [y_pos + size, y_pos - size],
                    color=colors['border'], linewidth=2.5, zorder=3)

        rect = FancyBboxPatch(
            (x - 0.15, (y + target_y) / 2 - 0.08), 0.3, 0.16,
            boxstyle="round,pad=0.02",
            facecolor='white', edgecolor=colors['border'], linewidth=1, alpha=0.9, zorder=4
        )
        ax.add_patch(rect)
        ax.text(x, (y + target_y) / 2, 'SWAP', va='center', ha='center',
                fontsize=7, fontweight='bold', color=colors['text'], zorder=5)

    def _draw_toffoli(self, ax, x, y, w, h, colors, qubit, padding_top, spacing):
        for q_offset in (-1, 1):
            if 0 <= qubit + q_offset < self.nb_qubits:
                y_ctrl = padding_top + (qubit + q_offset) * spacing
                circle = Circle((x, y_ctrl), 0.06,
                                 facecolor=colors['border'], edgecolor=colors['border'], linewidth=1.5, zorder=3)
                ax.add_patch(circle)
                ax.plot([x, x], [y_ctrl, y], color=colors['border'], linewidth=1.5, alpha=0.4, zorder=2)

        rect = FancyBboxPatch(
            (x - w / 4, y - h / 4), w, h,
            boxstyle="round,pad=0.05,rounding_size=0.08",
            facecolor=colors['bg'], edgecolor=colors['border'], linewidth=2, alpha=0.9, zorder=3
        )
        ax.add_patch(rect)
        ax.text(x, y, 'CCX', va='center', ha='center', fontsize=10, fontweight='bold',
                color=colors['text'], zorder=4)
        circle = Circle((x, y), 0.05, facecolor='white', edgecolor=colors['border'], linewidth=1.5, zorder=4)
        ax.add_patch(circle)

    def _draw_measure(self, ax, x, y, w, h, colors, params):
        rect = FancyBboxPatch(
            (x - w / 2, y - h / 2), w, h,
            boxstyle="round,pad=0.05,rounding_size=0.08",
            facecolor=colors['bg'], edgecolor=colors['border'], linewidth=2, alpha=0.9, zorder=3
        )
        ax.add_patch(rect)
        ax.text(x, y, 'M', va='center', ha='center', fontsize=13, fontweight='bold',
                color=colors['text'], zorder=4)
        if params:
            ax.text(x + w / 2 + 0.08, y, f'→ {params}', va='center', ha='left',
                    fontsize=8, color='#757575', style='italic', zorder=3)

    def _draw_barrier(self, ax, x, padding_top, colors, nb_qubits, spacing):
        y_start = padding_top - 0.1
        y_end = padding_top + (nb_qubits - 1) * spacing + 0.1
        ax.plot([x, x], [y_start, y_end], '--', color=colors['border'], linewidth=2, alpha=0.5, zorder=2)
        ax.plot([x - 0.08, x + 0.08], [y_start, y_start], color=colors['border'], linewidth=1.5, alpha=0.4, zorder=2)
        ax.plot([x - 0.08, x + 0.08], [y_end, y_end], color=colors['border'], linewidth=1.5, alpha=0.4, zorder=2)

    def _draw_legend(self, fig):
        """Dessine la légende directement sur la figure (et non sur les
        axes du circuit), en coordonnées relatives à la figure entière.
        Elle reste ainsi toujours visible dans la marge basse réservée par
        `fig.subplots_adjust(bottom=...)`, sans jamais être rognée ni
        pousser le circuit hors de vue."""
        legend_y = 0.045

        rect = FancyBboxPatch(
            (0.02, legend_y - 0.035), 0.96, 0.07,
            boxstyle="round,pad=0.02,rounding_size=0.02",
            facecolor='white', edgecolor='#E0E0E0', linewidth=1, alpha=0.95, zorder=10,
            transform=fig.transFigure, figure=fig, clip_on=False,
        )
        fig.add_artist(rect)
        fig.text(0.04, legend_y, 'Légende :', va='center', ha='left', fontsize=8, fontweight='bold',
                  color='#37474F', zorder=11)

        gate_list = [('H', '#2E7D32'), ('X', '#C62828'), ('Y', '#1565C0'),
                     ('Z', '#6A1B9A'), ('CX', '#F57F17'), ('SWAP', '#4E342E'), ('M', '#616161')]

        x_start = 0.16
        step = min(0.11, 0.80 / len(gate_list))
        for i, (name, color) in enumerate(gate_list):
            x_pos = x_start + i * step
            rect = Rectangle((x_pos - 0.012, legend_y - 0.018), 0.024, 0.036,
                              facecolor=color, edgecolor=color, alpha=0.3, linewidth=1,
                              transform=fig.transFigure, figure=fig, clip_on=False, zorder=11)
            fig.add_artist(rect)
            fig.text(x_pos + 0.016, legend_y, name, va='center', ha='left', fontsize=7,
                      color='#424242', zorder=11)


class CircuitTab(QWidget):
    def __init__(self):
        super().__init__()
        self.renderer = CircuitRenderer()
        self.circuit_data = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("Visualisation du circuit quantique")
        title.setObjectName("CardTitle")
        header.addWidget(title)
        header.addWidget(spacer_widget())
        self.info_pill = Pill("Compilez un code QuantL", status="muted")
        header.addWidget(self.info_pill)
        layout.addLayout(header)

        card = Card()
        card.body.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        canvas_host = QWidget()
        canvas_host.setStyleSheet("background-color: white; border-radius: 8px;")
        canvas_layout = QVBoxLayout(canvas_host)
        canvas_layout.setContentsMargins(8, 8, 8, 8)

        self.figure = Figure(figsize=(12, 6), dpi=100)
        self.figure.patch.set_facecolor('white')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(380)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        canvas_layout.addWidget(self.canvas)

        scroll.setWidget(canvas_host)
        card.body.addWidget(scroll)
        layout.addWidget(card, stretch=1)

        toolbar = QHBoxLayout()
        toolbar.addWidget(spacer_widget())
        toolbar.addWidget(QLabel("Exporter :"))
        for fmt in ("png", "svg", "pdf"):
            btn = make_button(fmt.upper(), object_name="GhostButton")
            btn.clicked.connect(lambda _checked, f=fmt: self._exporter(f))
            toolbar.addWidget(btn)
        layout.addLayout(toolbar)

    def update_content(self, resultat):
        circuit_data = resultat.get("circuit", [])
        if circuit_data:
            self.circuit_data = circuit_data
        elif resultat.get("ir"):
            self.circuit_data = self._construire_depuis_ir(resultat["ir"])
        else:
            self.circuit_data = []

        if self.circuit_data:
            nb_qubits = len(self.circuit_data)
            nb_portes = sum(len(q.get("portes", [])) for q in self.circuit_data)
            self.renderer.circuit_name = f"Circuit : {nb_qubits} qubits, {nb_portes} portes"
            self.info_pill.set_status("ok", f"{nb_qubits} qubit(s) • {nb_portes} porte(s)")
        else:
            self.info_pill.set_status("muted", "Compilez un code QuantL")

        self._redessiner()

    @staticmethod
    def _construire_depuis_ir(ir_text):
        circuit_data = {}
        for line in ir_text.split('\n'):
            if not line.strip():
                continue

            # BUGFIX (double comptage) : voir compiler_bridge.py pour l'explication
            # complète. Les motifs sont maintenant mutuellement exclusifs (measure
            # -> porte 2 qubits -> repli 1 qubit), avec `continue` après chaque
            # correspondance, pour qu'une ligne d'IR ne soit jamais comptée deux fois.

            match = re.search(r'\[IR\]\s*MEASURE\s+q\[(\d+)\]\s+->\s+c\[(\d+)\]', line)
            if match:
                qubit, bit = int(match.group(1)), int(match.group(2))
                circuit_data.setdefault(qubit, {"qubit": qubit, "portes": []})
                circuit_data[qubit]["portes"].append({"nom": "measure", "params": f"c[{bit}]", "target": -1})
                continue

            match = re.search(r'\[IR\]\s*([A-Z_]+)\s+q\[(\d+)\],\s+q\[(\d+)\]', line)
            if match:
                porte = match.group(1).lower()
                q1, q2 = int(match.group(2)), int(match.group(3))
                circuit_data.setdefault(q1, {"qubit": q1, "portes": []})
                circuit_data.setdefault(q2, {"qubit": q2, "portes": []})
                circuit_data[q1]["portes"].append({"nom": porte, "params": "", "target": q2})
                continue

            match = re.search(r'\[IR\]\s*([A-Z_]+)\s+q\[(\d+)\]', line)
            if match:
                porte = match.group(1).lower()
                qubit = int(match.group(2))
                circuit_data.setdefault(qubit, {"qubit": qubit, "portes": []})
                if porte not in ("print_probs", "print_state"):
                    circuit_data[qubit]["portes"].append({"nom": porte, "params": "", "target": -1})

        return list(circuit_data.values())

    def _redessiner(self):
        self.figure.clear()
        if self.circuit_data:
            self.renderer.set_circuit(self.circuit_data)
            self.renderer.draw(self.figure)
        else:
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, "Aucun circuit à afficher\n\nCompilez d'abord un code QuantL",
                    ha='center', va='center', fontsize=14, color='#9E9E9E', transform=ax.transAxes)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_frame_on(False)
        self.canvas.draw()

    def _exporter(self, format):
        extensions = {
            'png': 'Images PNG (*.png)',
            'svg': 'Images SVG (*.svg)',
            'pdf': 'Documents PDF (*.pdf)',
        }
        path, _ = QFileDialog.getSaveFileName(
            self, f"Exporter le circuit en {format.upper()}", f"circuit.{format}",
            extensions.get(format, "Tous les fichiers (*)")
        )
        if not path:
            return
        try:
            self.figure.savefig(path, dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
            QMessageBox.information(self, "Export réussi", f"Circuit exporté vers :\n{path}")
        except OSError as e:
            QMessageBox.critical(self, "Erreur", f"Impossible d'exporter :\n{e}")
