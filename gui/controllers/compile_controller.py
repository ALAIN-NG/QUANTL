"""
compile_controller.py — Orchestration de la compilation dans un thread
séparé pour ne jamais bloquer l'interface graphique.
"""
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from model.compiler_bridge import CompilerBridge, CompilerBridgeError


class CompilationWorker(QThread):
    """Exécute une compilation dans un thread séparé."""

    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, str)

    def __init__(self, code, mode="both", shots=1, seed=None):
        super().__init__()
        self.code = code
        self.mode = mode
        self.shots = shots
        self.seed = seed
        self.bridge = CompilerBridge()

    def run(self):
        try:
            self.progress.emit(15, "Analyse lexicale et syntaxique...")
            resultat = self.bridge.executer(
                self.code, mode=self.mode, shots=self.shots, seed=self.seed
            )
            self.progress.emit(100, "Compilation terminée")
            self.finished.emit(resultat)
        except CompilerBridgeError as e:
            self.error.emit(str(e))


class CompilationController(QObject):
    """Gère le cycle de vie des compilations demandées par l'interface."""

    compilation_started = pyqtSignal()
    compilation_finished = pyqtSignal(dict)
    compilation_error = pyqtSignal(str)
    progress_updated = pyqtSignal(int, str)

    def __init__(self):
        super().__init__()
        self.worker = None
        self.dernier_resultat = None

    def compile(self, code, mode="both", shots=1, seed=None):
        """Lance une compilation, en annulant toute compilation en cours."""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()

        self.worker = CompilationWorker(code, mode, shots, seed)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.progress.connect(self.progress_updated.emit)

        self.compilation_started.emit()
        self.worker.start()

    def _on_finished(self, resultat):
        self.dernier_resultat = resultat
        self.compilation_finished.emit(resultat)

    def _on_error(self, erreur):
        self.compilation_error.emit(erreur)
