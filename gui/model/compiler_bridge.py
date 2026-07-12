import subprocess
import json
import os
import tempfile
import re

class CompilerBridgeError(Exception):
    pass

class CompilerBridge:
    def __init__(self, chemin_compilateur=None):
        if chemin_compilateur is None:
            # BUGFIX (résolution du binaire qcompile) : l'ancienne liste de
            # candidats se terminait par un chemin ABSOLU codé en dur,
            # spécifique à la machine de développement d'origine
            # ("/home/alain/.../bin/qcompile"). Cela signifie que si aucun
            # des chemins relatifs plausibles n'existait (par exemple juste
            # après avoir décompressé une copie fraîche du projet ailleurs,
            # ou avant d'avoir lancé `make` dans CETTE copie), la recherche
            # retombait silencieusement sur l'exécutable de l'ANCIEN
            # répertoire de travail — potentiellement un binaire obsolète,
            # construit avant des corrections ultérieures du compilateur.
            # Aucune erreur n'était levée : le mauvais binaire était utilisé
            # sans avertissement, ce qui pouvait faire réapparaître des bugs
            # pourtant déjà corrigés dans les sources actuelles. On ne
            # considère désormais que des chemins RELATIFS à l'emplacement
            # réel de ce fichier (donc à la copie du projet réellement en
            # cours d'exécution), sans aucun repli propre à une machine
            # particulière.
            gui_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            project_root = os.path.dirname(gui_dir)
            possible_paths = [
                os.path.join(project_root, "bin", "qcompile"),
                os.path.join(project_root, "qcompile"),
                os.path.join(os.getcwd(), "bin", "qcompile"),
                os.path.join(os.getcwd(), "qcompile"),
            ]

            self.chemin_compilateur = None
            for path in possible_paths:
                abs_path = os.path.abspath(path)
                if os.path.exists(abs_path) and os.access(abs_path, os.X_OK):
                    self.chemin_compilateur = abs_path
                    break

            if self.chemin_compilateur is None:
                # Aucun binaire valide trouvé : on fixe un chemin par défaut
                # explicite (celui attendu après un `make` à la racine du
                # projet) afin que _verifier_compilateur() lève un message
                # d'erreur clair et actionnable, plutôt que d'utiliser un
                # binaire non lié à cette copie du projet.
                self.chemin_compilateur = os.path.join(project_root, "bin", "qcompile")
        else:
            self.chemin_compilateur = chemin_compilateur

        self._verifier_compilateur()

    def _verifier_compilateur(self):
        if not os.path.exists(self.chemin_compilateur):
            raise CompilerBridgeError(
                f"Compilateur '{self.chemin_compilateur}' non trouvé.\n"
                "Vérifiez que vous avez compilé le projet avec 'make' "
                "à la racine du dépôt (le binaire est attendu dans bin/qcompile)."
            )
        if not os.access(self.chemin_compilateur, os.X_OK):
            raise CompilerBridgeError(
                f"Compilateur '{self.chemin_compilateur}' n'est pas exécutable."
            )
    
    def executer(self, source_code, mode="sim", shots=1, seed=None):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.qtl', delete=False, encoding='utf-8') as f:
            f.write(source_code)
            temp_file = f.name

        # BUGFIX (export QASM) : le compilateur qcompile écrit son fichier
        # QASM par défaut sous le nom relatif "output.qasm", donc dans le
        # RÉPERTOIRE COURANT (cwd) du processus au moment de l'exécution —
        # cwd qui dépend d'où l'utilisateur a lancé l'appli GUI (souvent
        # gui/), et n'a AUCUN rapport avec l'emplacement du binaire
        # qcompile. L'ancien code reconstruisait pourtant le chemin attendu
        # à partir de `self.chemin_compilateur` (deux niveaux au-dessus du
        # binaire), un chemin qui ne correspondait presque jamais au fichier
        # réellement écrit. Résultat : resultat["qasm"] restait vide, l'onglet
        # QASM affichait le texte de substitution, et "Valider la syntaxe"
        # rapportait à tort 'OPENQASM manquante' et 'include qelib1.inc
        # manquant'. On force maintenant un chemin de sortie ABSOLU et
        # unique via --output, à côté du fichier source temporaire, et on
        # relit exactement ce chemin : aucune dépendance au cwd.
        qasm_path = temp_file[:-len('.qtl')] + '.qasm' if temp_file.endswith('.qtl') else temp_file + '.qasm'

        try:
            cmd = [
                self.chemin_compilateur, "--source", temp_file,
                "--mode", mode, "--debug", "--output", qasm_path
            ]
            if shots > 1:
                cmd.extend(["--shots", str(shots)])
            if seed is not None:
                cmd.extend(["--seed", str(seed)])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            return self._parser_sortie(result.stdout, result.stderr, mode, qasm_path)

        except subprocess.TimeoutExpired:
            raise CompilerBridgeError("Timeout: la compilation a pris trop de temps.")
        except Exception as e:
            raise CompilerBridgeError(f"Erreur lors de l'exécution: {str(e)}")
        finally:
            for path in (temp_file, qasm_path):
                if os.path.exists(path):
                    try:
                        os.unlink(path)
                    except:
                        pass
    
    def _parser_sortie(self, stdout, stderr, mode, qasm_path=None):
        """Parse la sortie du compilateur"""
        resultat = {
            "statut": "ok" if not stderr or "Erreur" not in stderr else "erreur",
            "erreurs": [],
            "ast": "",
            "ir": "",
            "tokens": [],
            "circuit": [],
            "simulation": {
                "probabilites": {},
                "mesures_obtenues": {},
                "etat_final": None
            },
            "qasm": "",
            "stdout": stdout,
            "stderr": stderr
        }
        
        # --- 1. Extraire l'AST ---
        in_ast = False
        ast_lines = []
        for line in stdout.split('\n'):
            if "AST généré:" in line:
                in_ast = True
                continue
            if in_ast:
                if line.strip() == "":
                    continue
                # Sortir de l'AST quand on voit une ligne qui n'est pas indentée
                if line.strip() and not line.startswith('[') and not line.startswith(' '):
                    if "Analyse sémantique" in line or "Génération" in line or "Simulation" in line:
                        in_ast = False
                        continue
                if in_ast and line.strip():
                    ast_lines.append(line.strip())
        resultat["ast"] = "\n".join(ast_lines)
        
        # --- 2. Extraire l'IR ---
        in_ir = False
        ir_lines = []
        for line in stdout.split('\n'):
            if "IR généré:" in line:
                in_ir = True
                continue
            if in_ir:
                if line.strip() == "":
                    continue
                if line.strip() and not line.startswith('[IR]') and not line.startswith(' '):
                    if "Simulation" in line or "Génération" in line:
                        in_ir = False
                        continue
                if in_ir and line.strip():
                    ir_lines.append(line.strip())
        resultat["ir"] = "\n".join(ir_lines)
        
        # --- 3. Construire le circuit depuis l'IR ---
        circuit_data = {}
        for line in ir_lines:
            if not line.strip():
                continue

            # BUGFIX (double comptage) : auparavant, les 3 regex ci-dessous
            # étaient toutes testées indépendamment (if / if / if, sans
            # exclusion mutuelle). Une ligne comme "CX q[0], q[1]" correspond
            # À LA FOIS au motif générique 1-qubit (qui capture juste
            # "CX q[0]" avec target=-1, une entrée erronée) ET au motif
            # 2-qubits correct : chaque CX/CZ/SWAP était donc ajoutée deux fois
            # au circuit affiché. Idem pour "MEASURE q[0] -> c[0]", qui
            # correspond aussi au motif générique en plus du motif MEASURE
            # dédié : chaque mesure était comptée deux fois. Résultat observé :
            # Bell affichait 2 CNOT/4 M au lieu de 1 CNOT/2 M réels, etc.
            # On teste maintenant les motifs les plus spécifiques d'abord et on
            # utilise `continue` pour garantir qu'une ligne ne soit traitée
            # qu'une seule fois.

            # [IR] MEASURE q[0] -> c[0] (ligne 8)
            match = re.search(r'\[IR\]\s*MEASURE\s+q\[(\d+)\]\s+->\s+c\[(\d+)\]', line)
            if match:
                qubit = int(match.group(1))
                bit = int(match.group(2))
                if qubit not in circuit_data:
                    circuit_data[qubit] = {"qubit": qubit, "portes": []}
                circuit_data[qubit]["portes"].append({
                    "nom": "measure", 
                    "params": f"c[{bit}]", 
                    "target": -1
                })
                continue

            # [IR] CX q[0], q[1] (ligne 5) -- portes à 2 qubits (cx, cz, swap)
            match = re.search(r'\[IR\]\s*([A-Z_]+)\s+q\[(\d+)\],\s+q\[(\d+)\]', line)
            if match:
                porte = match.group(1).lower()
                qubit1 = int(match.group(2))
                qubit2 = int(match.group(3))
                if qubit1 not in circuit_data:
                    circuit_data[qubit1] = {"qubit": qubit1, "portes": []}
                if qubit2 not in circuit_data:
                    circuit_data[qubit2] = {"qubit": qubit2, "portes": []}
                circuit_data[qubit1]["portes"].append({
                    "nom": porte, 
                    "params": "", 
                    "target": qubit2
                })
                continue

            # [IR] H q[0] (ligne 4) -- porte à 1 qubit (repli, seulement si
            # aucun des motifs plus spécifiques ci-dessus n'a déjà matché)
            match = re.search(r'\[IR\]\s*([A-Z_]+)\s+q\[(\d+)\]', line)
            if match:
                porte = match.group(1).lower()
                qubit = int(match.group(2))
                if qubit not in circuit_data:
                    circuit_data[qubit] = {"qubit": qubit, "portes": []}
                # Ne pas ajouter PRINT_PROBS comme porte
                if porte not in ["print_probs", "print_state"]:
                    circuit_data[qubit]["portes"].append({
                        "nom": porte, 
                        "params": "", 
                        "target": -1
                    })
        
        resultat["circuit"] = list(circuit_data.values())
        
        # --- 4. Extraire les probabilités ---
        probs_pattern = r'\|\s*([01]+)\s*\>\s*:\s*([0-9.]+)'
        prob_matches = re.findall(probs_pattern, stdout)
        for state, prob in prob_matches:
            resultat["simulation"]["probabilites"][state] = float(prob)
        
        # --- 5. Extraire les résultats de mesure ---
        mesures_pattern = r'c\[(\d+)\]=(\d+)'
        mesure_matches = re.findall(mesures_pattern, stdout)
        for idx, val in mesure_matches:
            resultat["simulation"]["mesures_obtenues"][f"c{idx}"] = int(val)
        
        # --- 6. Extraire les erreurs ---
        if stderr:
            for line in stderr.split('\n'):
                if "Erreur" in line or "error" in line.lower():
                    resultat["erreurs"].append(line)
        
        # --- 7. Extraire le QASM ---
        # On relit strictement le chemin passé à qcompile via --output
        # (voir bugfix dans executer()) : plus aucune reconstruction de
        # chemin approximative basée sur l'emplacement du binaire.
        if qasm_path and os.path.exists(qasm_path):
            try:
                with open(qasm_path, 'r', encoding='utf-8') as f:
                    resultat["qasm"] = f.read()
            except OSError:
                pass
        
        return resultat
    
    def _extraire_ir(self, stdout):
        """Extrait l'IR de la sortie du compilateur"""
        ir_lines = []
        in_ir = False
        
        for line in stdout.split('\n'):
            if "IR généré:" in line:
                in_ir = True
                continue
            if in_ir:
                if line.strip() == "":
                    continue
                # Sortir quand on voit une nouvelle section
                if line.strip() and not line.startswith('[IR]') and not line.startswith(' '):
                    if "Simulation" in line or "Génération" in line:
                        in_ir = False
                        continue
                if in_ir and line.strip():
                    ir_lines.append(line.strip())
        
        return "\n".join(ir_lines)