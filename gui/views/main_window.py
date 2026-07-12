"""
main_window.py — Fenêtre principale de QuantL.

Disposition : un panneau d'édition toujours visible à gauche (splitter),
et à droite un ensemble d'onglets présentant les différentes étapes de la
compilation (analyse lexicale/syntaxique, circuit, simulation, QASM,
console). Cette organisation remplace l'ancienne interface 100% "à onglets"
où l'éditeur disparaissait dès qu'on consultait un résultat.
"""
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QStatusBar, QWidget, QSplitter,
    QVBoxLayout, QMessageBox, QToolBar, QLabel,
    QProgressBar, QApplication, QSizePolicy
)
from PyQt6.QtCore import Qt, QSettings, QSize
from PyQt6.QtGui import QAction, QKeySequence

from views.editor_tab import EditorTab
from views.lexical_tab import LexicalTab
from views.circuit_tab import CircuitTab
from views.simulation_tab import SimulationTab
from views.qasm_tab import QASMTab
from views.console_tab import ConsoleTab
from views.about_dialog import AboutDialog

from controllers.compile_controller import CompilationController
from widgets.common import Pill, make_button
from resources import theme

ORG_NAME = "Université de Yaoundé I"
APP_NAME = "QuantL"

EXAMPLES = {
    "bell": (
        "État de Bell",
        """// État de Bell
qreg q[2];
creg c[2];

h q[0];
cx q[0], q[1];

measure q[0] -> c[0];
measure q[1] -> c[1];

print probs;""",
    ),
    "ghz": (
        "État GHZ",
        """// État GHZ à 3 qubits
qreg q[3];
creg c[3];

h q[0];
cx q[0], q[1];
cx q[1], q[2];

barrier q[0], q[1], q[2];

measure q[0] -> c[0];
measure q[1] -> c[1];
measure q[2] -> c[2];

print probs;""",
    ),
    "deutsch": (
        "Algorithme de Deutsch",
        """// Algorithme de Deutsch
qreg q[2];
creg c[1];

x q[1];
h q[0];
h q[1];

cx q[0], q[1];

h q[0];
measure q[0] -> c[0];

if (c[0] == 0) print state;
if (c[0] == 1) print state;""",
    ),
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} — Compilateur Quantique")
        self.setMinimumSize(1100, 700)

        self.settings = QSettings(ORG_NAME, APP_NAME)
        self.controller = CompilationController()
        self._theme = self.settings.value("theme", "dark")

        self._setup_ui()
        self._setup_menus()
        self._setup_toolbar()
        self._connect_signals()

        self._restore_geometry()
        self._load_example("bell", silent=True)
        self._apply_theme(self._theme)

    # ------------------------------------------------------------------ UI
    def _setup_ui(self):
        central = QWidget()
        central.setObjectName("CentralHost")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(splitter)

        # --- Panneau gauche : éditeur ---
        editor_host = QWidget()
        editor_layout = QVBoxLayout(editor_host)
        editor_layout.setContentsMargins(12, 12, 6, 12)
        self.editor_tab = EditorTab()
        editor_layout.addWidget(self.editor_tab)
        splitter.addWidget(editor_host)

        # --- Panneau droit : résultats de compilation ---
        results_host = QWidget()
        results_layout = QVBoxLayout(results_host)
        results_layout.setContentsMargins(6, 12, 12, 12)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        results_layout.addWidget(self.tabs)
        splitter.addWidget(results_host)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([600, 700])
        self._splitter = splitter

        self.lexical_tab = LexicalTab()
        self.tabs.addTab(self.lexical_tab, "Lexical / Syntaxique")

        self.circuit_tab = CircuitTab()
        self.tabs.addTab(self.circuit_tab, "Circuit")

        self.simulation_tab = SimulationTab()
        self.tabs.addTab(self.simulation_tab, "Simulation")

        self.qasm_tab = QASMTab()
        self.tabs.addTab(self.qasm_tab, "Export QASM")

        self.console_tab = ConsoleTab()
        self.tabs.addTab(self.console_tab, "Console")

        # --- Barre d'état ---
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.status_pill = Pill("Prêt", status="muted")
        self.status_bar.addPermanentWidget(self.status_pill)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(140)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

        self.position_label = QLabel("Ligne 1, Col 1")
        self.position_label.setObjectName("MutedLabel")
        self.status_bar.addPermanentWidget(self.position_label)

        self.status_bar.showMessage("Prêt")

    def _setup_menus(self):
        menubar = self.menuBar()

        # --- Fichier ---
        file_menu = menubar.addMenu("&Fichier")

        new_action = QAction("&Nouveau", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self._new_file)
        file_menu.addAction(new_action)

        open_action = QAction("&Ouvrir...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.editor_tab.open_file_dialog)
        file_menu.addAction(open_action)

        save_action = QAction("&Enregistrer", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.editor_tab.save_file)
        file_menu.addAction(save_action)

        save_as_action = QAction("Enregistrer &sous...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self.editor_tab.save_file_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        examples_menu = file_menu.addMenu("Exemples")
        for key, (label, _code) in EXAMPLES.items():
            action = QAction(label, self)
            action.triggered.connect(lambda _checked, k=key: self._load_example(k))
            examples_menu.addAction(action)

        file_menu.addSeparator()

        exit_action = QAction("&Quitter", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # --- Compilation ---
        compile_menu = menubar.addMenu("&Compilation")

        compile_action = QAction("&Compiler", self)
        compile_action.setShortcut(QKeySequence("Ctrl+Return"))
        compile_action.triggered.connect(self._compiler)
        compile_menu.addAction(compile_action)

        clear_console_action = QAction("Effacer la console", self)
        clear_console_action.triggered.connect(self.console_tab.clear)
        compile_menu.addAction(clear_console_action)

        # --- Affichage ---
        view_menu = menubar.addMenu("&Affichage")

        dark_action = QAction("Thème sombre", self)
        dark_action.triggered.connect(lambda: self._apply_theme("dark"))
        view_menu.addAction(dark_action)

        light_action = QAction("Thème clair", self)
        light_action.triggered.connect(lambda: self._apply_theme("light"))
        view_menu.addAction(light_action)

        # --- Aide ---
        help_menu = menubar.addMenu("&Aide")
        about_action = QAction("À propos de QuantL", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_toolbar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(18, 18))
        self.addToolBar(toolbar)

        self.compile_btn = make_button("▶  Compiler", object_name="PrimaryButton",
                                        tooltip="Compiler le code (Ctrl+Entrée)")
        self.compile_btn.clicked.connect(self._compiler)
        toolbar.addWidget(self.compile_btn)

        toolbar.addSeparator()

        export_btn = make_button("Exporter QASM", object_name="GhostButton")
        export_btn.clicked.connect(self._exporter_qasm)
        toolbar.addWidget(export_btn)

        # Widget extensible pour pousser le bouton de thème à droite
        stretch = QWidget()
        stretch.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(stretch)

        self.theme_btn = make_button("🌙  Sombre", object_name="GhostButton", checkable=True,
                                      tooltip="Basculer entre thème sombre et clair")
        self.theme_btn.clicked.connect(self._toggle_theme)
        toolbar.addWidget(self.theme_btn)

    def _connect_signals(self):
        self.controller.compilation_started.connect(self._on_compilation_started)
        self.controller.compilation_finished.connect(self._on_compilation_finished)
        self.controller.compilation_error.connect(self._on_compilation_error)
        self.controller.progress_updated.connect(self._on_progress_updated)

        self.editor_tab.compile_requested.connect(self._compiler)
        self.editor_tab.content_modified.connect(self._on_modified_changed)
        self.editor_tab.cursor_moved.connect(
            lambda line, col: self.position_label.setText(f"Ligne {line}, Col {col}")
        )
        self.simulation_tab.simulate_requested.connect(self._relancer_simulation)

    # -------------------------------------------------------------- Thème
    def _apply_theme(self, theme_name):
        self._theme = theme_name
        app = QApplication.instance()
        if app:
            app.setStyleSheet(theme.stylesheet(theme_name))
        self.simulation_tab.apply_theme(theme_name)
        self.settings.setValue("theme", theme_name)

        if theme_name == "dark":
            self.theme_btn.setText("🌙  Sombre")
            self.theme_btn.setChecked(False)
        else:
            self.theme_btn.setText("☀️  Clair")
            self.theme_btn.setChecked(True)

    def _toggle_theme(self):
        self._apply_theme("light" if self._theme == "dark" else "dark")

    # ---------------------------------------------------------- Compilation
    def _compiler(self):
        code = self.editor_tab.get_code()
        if not code.strip():
            QMessageBox.warning(self, "Avertissement", "Le code est vide.")
            return
        self.editor_tab.clear_highlights()
        # BUGFIX (export QASM) : cette action est câblée sur le bouton
        # "Compiler" du menu, de la barre d'outils ET du raccourci de
        # l'éditeur (compile_requested) — c'est donc le chemin de
        # compilation PRINCIPAL. Elle forçait auparavant mode="sim", qui
        # demande à qcompile de NE PAS générer de code QASM du tout (voir
        # main.c : la génération QASM n'a lieu que si mode == "qasm" ou
        # "both"). Or _on_compilation_finished() met à jour l'onglet QASM
        # après CHAQUE compilation, quel que soit le mode demandé : après un
        # clic sur "Compiler", l'onglet QASM affichait donc systématiquement
        # son texte de substitution (aucun code généré), et "Valider la
        # syntaxe" rapportait à tort 'OPENQASM manquante' / 'qelib1.inc
        # manquant'. On utilise donc "both" ici afin que la simulation ET
        # l'export QASM soient toujours disponibles après une compilation.
        self.controller.compile(code, mode="both")

    def _relancer_simulation(self, shots=10, seed=42):
        code = self.editor_tab.get_code()
        if not code.strip():
            QMessageBox.warning(self, "Avertissement", "Le code est vide.")
            return
        self.controller.compile(code, shots=shots, seed=seed)

    def _exporter_qasm(self):
        self.tabs.setCurrentWidget(self.qasm_tab)

    def _on_compilation_started(self):
        self.status_pill.set_status("running", "Compilation en cours…")
        self.status_bar.showMessage("Compilation en cours...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(10)
        self.compile_btn.setEnabled(False)

    def _on_compilation_finished(self, resultat):
        self.progress_bar.setVisible(False)
        self.compile_btn.setEnabled(True)

        self.lexical_tab.update_content(resultat)
        self.circuit_tab.update_content(resultat)
        self.simulation_tab.update_content(resultat)
        self.qasm_tab.update_content(resultat)
        self.console_tab.update_content(resultat)

        if resultat.get("statut") == "ok":
            self.status_pill.set_status("ok", "Compilation réussie")
            self.status_bar.showMessage("Compilation réussie", 4000)
            self.tabs.setCurrentWidget(self.simulation_tab)
        else:
            self.status_pill.set_status("error", "Compilation échouée")
            self.status_bar.showMessage("Compilation échouée", 4000)
            self._signaler_erreurs(resultat)
            self.tabs.setCurrentWidget(self.console_tab)

    def _signaler_erreurs(self, resultat):
        """Surligne dans l'éditeur la première ligne fautive détectée."""
        import re
        for source in (resultat.get("erreurs") or []) + [resultat.get("stderr", "")]:
            match = re.search(r"ligne (\d+)\s*\)?\s*:?\s*(.*)", source)
            if match:
                ligne = int(match.group(1))
                message = match.group(2).strip() or source.strip()
                self.editor_tab.highlight_error(ligne, message)
                break

    def _on_compilation_error(self, erreur):
        self.progress_bar.setVisible(False)
        self.compile_btn.setEnabled(True)
        self.status_pill.set_status("error", "Erreur")
        self.status_bar.showMessage(f"Erreur : {erreur}", 6000)
        QMessageBox.critical(self, "Erreur de compilation", erreur)

    def _on_progress_updated(self, progress, message):
        self.progress_bar.setValue(progress)
        self.status_bar.showMessage(f"{message} ({progress}%)")

    def _on_modified_changed(self, dirty):
        title = f"{APP_NAME} — Compilateur Quantique"
        if self.editor_tab.fichier_courant:
            import os
            title = f"{os.path.basename(self.editor_tab.fichier_courant)} — {title}"
        if dirty:
            title = f"● {title}"
        self.setWindowTitle(title)

    # ------------------------------------------------------------- Fichiers
    def _new_file(self):
        if not self.editor_tab._confirm_discard_changes():
            return
        self.editor_tab.set_code("")
        self.editor_tab.fichier_courant = None
        self.editor_tab._set_dirty(False)
        self.editor_tab.file_label.setText("Nouveau fichier")

    def _load_example(self, key, silent=False):
        if not silent and not self.editor_tab._confirm_discard_changes():
            return
        label, code = EXAMPLES[key]
        self.editor_tab.load_example(label, code)
        if not silent:
            self.status_bar.showMessage(f"Exemple « {label} » chargé", 3000)

    def _show_about(self):
        AboutDialog(self).exec()

    # ---------------------------------------------------------- Fenêtre
    def _restore_geometry(self):
        geometry = self.settings.value("geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)
        else:
            self.setGeometry(100, 100, 1440, 900)

        sizes = self.settings.value("splitter_sizes")
        if sizes:
            try:
                self._splitter.setSizes([int(s) for s in sizes])
            except (TypeError, ValueError):
                pass

    def closeEvent(self, event):
        if not self.editor_tab._confirm_discard_changes():
            event.ignore()
            return
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("splitter_sizes", self._splitter.sizes())
        super().closeEvent(event)
