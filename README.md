# QuantL

**QuantL** est un langage de programmation dédié (DSL) à la description de circuits quantiques, accompagné d'un compilateur natif écrit en C (Flex/Bison) et d'une interface graphique de bureau (PyQt6) permettant l'édition, la compilation, la simulation et l'export interopérable des programmes QuantL.

Le projet a été conçu dans un cadre académique (Master 1 Informatique) pour illustrer, sur une chaîne de compilation complète, l'ensemble des phases classiques d'un compilateur — analyse lexicale, analyse syntaxique, analyse sémantique, génération de représentation intermédiaire (IR), simulation numérique et génération de code cible — appliquées à un domaine non conventionnel : la programmation par circuits quantiques.

---

## Sommaire

1. [Aperçu](#aperçu)
2. [Fonctionnalités](#fonctionnalités)
3. [Architecture du projet](#architecture-du-projet)
4. [Le langage QuantL](#le-langage-quantl)
5. [Structure du dépôt](#structure-du-dépôt)
6. [Installation](#installation)
7. [Utilisation en ligne de commande](#utilisation-en-ligne-de-commande)
8. [Interface graphique](#interface-graphique)
9. [Exemples de circuits fournis](#exemples-de-circuits-fournis)
10. [Export OpenQASM 2.0](#export-openqasm-20)
11. [Limites connues](#limites-connues)
12. [Pistes d'évolution](#pistes-dévolution)
13. [Documentation académique](#documentation-académique)
14. [Auteur et cadre académique](#auteur-et-cadre-académique)

---

## Aperçu

QuantL permet de décrire un circuit quantique à l'aide d'une syntaxe déclarative proche de celle utilisée par les SDK quantiques usuels (registres quantiques et classiques, portes unitaires, mesures, contrôle conditionnel classique). Le programme source (`.qtl`) est ensuite :

1. **analysé lexicalement et syntaxiquement** par un compilateur natif généré avec Flex et Bison ;
2. **vérifié sémantiquement** (déclarations de registres, indices de qubits/bits valides, cohérence des opérandes) ;
3. **traduit en une représentation intermédiaire (IR)** linéaire, indépendante de la syntaxe source ;
4. **simulé numériquement** par un moteur de simulation à vecteur d'état complet (état exact, portes appliquées comme opérateurs unitaires) ;
5. **exporté au format OpenQASM 2.0**, standard ouvert interopérable avec l'écosystème IBM Quantum / Qiskit.

L'ensemble de cette chaîne est accessible soit via un exécutable en ligne de commande (`qcompile`), soit via une interface graphique de bureau construite en PyQt6 selon une architecture MVC, qui encapsule le compilateur natif et présente ses résultats (AST, IR, simulation, code QASM, diagnostics) dans des onglets dédiés.

## Fonctionnalités

**Langage et compilateur (`src/`, en C)**

- Registres quantiques et classiques déclarés explicitement (`qreg`, `creg`) ;
- Portes à un qubit : `h`, `x`, `y`, `z`, `s`, `t` ;
- Portes paramétrées à un qubit : `rx`, `ry`, `rz` (rotation d'angle réel, y compris la constante `pi`) ;
- Portes à deux qubits : `cx` (CNOT), `cz`, `swap` ;
- Porte à trois qubits : `toffoli` (CCX) ;
- Mesure d'un qubit vers un bit classique (`measure ... -> ...`) ;
- Contrôle conditionnel classique sur un bit précis d'un registre (`if (c[i] == v) instruction;`) ;
- Répétition d'un bloc d'instructions (`repeat (N) { ... }`) ;
- Synchronisation visuelle/logique du circuit (`barrier`) ;
- Directives d'introspection pour la simulation (`print state;`, `print probs;`) ;
- Commentaires sur une ligne (`//`) ;
- Diagnostics d'erreurs lexicales, syntaxiques et sémantiques avec numéro de ligne.

**Simulation**

- Moteur de simulation à vecteur d'état complet (`double complex`), portes appliquées comme opérateurs unitaires exacts (aucune approximation) ;
- Support du tirage pseudo-aléatoire des mesures avec graine (`--seed`) pour la reproductibilité ;
- Simulation répétée (`--shots N`) pour l'estimation statistique des distributions de mesure ;
- Affichage de l'état quantique complet et des probabilités associées à chaque état de base.

**Génération de code**

- Export vers **OpenQASM 2.0**, directement compatible avec Qiskit et les simulateurs/matériels de l'écosystème IBM Quantum ;
- Traduction fidèle des portes, mesures et barrières ; documentation explicite en commentaire des constructions QuantL sans équivalent direct en OpenQASM 2.0 (conditions sur un bit unique, notamment).

**Interface graphique (`gui/`, en PyQt6)**

- Architecture MVC : modèle (`gui/model/`), contrôleurs (`gui/controllers/`), vues (`gui/views/`) ;
- Éditeur de code avec coloration syntaxique dédiée au langage QuantL ;
- Onglets de résultats : analyse lexicale (tokens), arbre syntaxique abstrait (AST), représentation intermédiaire (IR), circuit, simulation, export QASM, console de diagnostics ;
- Compilation exécutée en tâche de fond (thread dédié, `QThread`) afin de ne jamais bloquer l'interface ;
- Thèmes graphiques clair et sombre (`gui/resources/light.qss`, `dark.qss`) ;
- Bibliothèque d'exemples de circuits intégrée, couvrant des cas pédagogiques classiques à des algorithmes quantiques plus avancés.

## Architecture du projet

La chaîne de compilation est organisée en modules successifs, chacun correspondant à un fichier source dédié dans `src/` :

```
Code source .qtl
       |
       v
 Lexer (quantl.l, Flex)        Analyse lexicale : découpage en tokens
       |                       (mots-clés, identifiants, entiers, flottants)
       v
 Parser (quantl.y, Bison)      Analyse syntaxique ascendante (LALR),
       |                       construction de l'arbre syntaxique abstrait
       |                       (ast.c / ast.h)
       v
 Sémantique (semantic.c)       Vérification des registres déclarés,
       |                       des indices de qubits/bits et des
       |                       opérandes des instructions
       v
 IR (ir.c)                     Génération d'une représentation
       |                       intermédiaire linéaire (liste chaînée
       |                       d'instructions typées, indépendante
       |                       de la syntaxe source)
       |
       +-------------------+-------------------+
       v                                       v
 Simulateur (sim_engine.c)          Générateur QASM (codegen_qasm.c)
 vecteur d'état complet             OpenQASM 2.0, compatible Qiskit
```

L'interface graphique (`gui/`) n'implémente aucune logique de compilation propre : elle invoque l'exécutable natif `qcompile` en sous-processus (`gui/model/compiler_bridge.py`), puis analyse et structure sa sortie standard pour l'afficher dans les différents onglets. Cette séparation stricte entre le cœur du compilateur (C, performant et testable indépendamment) et la couche de présentation (Python/PyQt6) constitue le principe directeur de l'architecture.

## Le langage QuantL

### Exemple : paire intriquée (état de Bell)

```qtl
// Etat de Bell : intrication maximale de 2 qubits
qreg q[2];
creg c[2];

h q[0];
cx q[0], q[1];

barrier q[0], q[1];

measure q[0] -> c[0];
measure q[1] -> c[1];

print probs;
```

### Exemple : contrôle conditionnel classique

```qtl
qreg q[3];
creg c[2];

h q[0];
h q[1];
measure q[0] -> c[0];
measure q[1] -> c[1];

if (c[0] == 0) print state;
if (c[1] == 1) print state;
```

### Grammaire (aperçu informel)

| Construction              | Exemple                          | Sémantique                                   |
|----------------------------|-----------------------------------|-----------------------------------------------|
| Déclaration de registre     | `qreg q[3]; creg c[3];`          | Alloue `n` qubits / bits classiques           |
| Porte à un qubit             | `h q[0];`                        | Applique `H`, `X`, `Y`, `Z`, `S` ou `T`       |
| Porte de rotation             | `rx(pi/2) q[0];`                 | Rotation paramétrée autour d'un axe de Bloch  |
| Porte à deux qubits           | `cx q[0], q[1];`                 | `CNOT`, `CZ` ou `SWAP`                        |
| Porte à trois qubits           | `toffoli q[0], q[1], q[2];`      | Porte de Toffoli (CCX)                        |
| Mesure                        | `measure q[0] -> c[0];`          | Projette et enregistre le résultat            |
| Contrôle conditionnel          | `if (c[0] == 1) x q[1];`         | Exécution conditionnée à un bit classique     |
| Répétition                    | `repeat (4) { h q[0]; }`         | Réexécute un bloc `N` fois                    |
| Synchronisation                | `barrier q[0], q[1];`            | Marque une frontière logique dans le circuit  |
| Introspection                  | `print state;` / `print probs;` | Affiche l'état ou les probabilités (simulation uniquement) |

## Structure du dépôt

```
quantl/
├── src/                     Compilateur natif (C)
│   ├── quantl.l             Spécification lexicale (Flex)
│   ├── quantl.y             Grammaire (Bison)
│   ├── ast.c / ast.h        Arbre syntaxique abstrait
│   ├── semantic.c / .h      Analyse sémantique
│   ├── ir.c / ir.h          Représentation intermédiaire
│   ├── sim_engine.c / .h    Moteur de simulation (vecteur d'état)
│   ├── codegen_qasm.c / .h  Génération de code OpenQASM 2.0
│   ├── json_writer.c / .h   Export JSON (réservé, non implémenté)
│   └── main.c               Point d'entrée CLI (qcompile)
├── Makefile                 Construction du compilateur natif
├── gui/                      Interface graphique (Python / PyQt6)
│   ├── main.py                Point d'entrée de l'application
│   ├── model/                 Pont vers le compilateur natif, état de session
│   ├── controllers/            Orchestration de la compilation (thread dédié)
│   ├── views/                   Fenêtre principale et onglets (éditeur, AST, IR,
│   │                             circuit, simulation, QASM, console)
│   ├── widgets/                  Composants réutilisables (éditeur, coloration)
│   ├── resources/                 Thèmes graphiques (QSS) et exemples intégrés
│   └── examples/                   Bibliothèque de circuits d'exemple (.qtl)
├── tests/                    Programmes QuantL de test / non-régression
├── docu/                      Support de présentation académique (LaTeX/Beamer)
└── README.md
```

## Installation

### Prérequis

- Un compilateur C conforme C11 (`gcc` ou `clang`) ;
- `make` ;
- `flex` et `bison` (génération de l'analyseur lexical et syntaxique) ;
- Python ≥ 3.10 avec `PyQt6` installé, pour l'interface graphique uniquement.

Sur une distribution de type Debian/Ubuntu :

```bash
sudo apt-get install build-essential flex bison
pip install PyQt6
```

### Compilation du compilateur natif

```bash
cd quantl
make
```

Cette commande génère l'analyseur lexical et syntaxique à partir de `quantl.l` et `quantl.y`, compile l'ensemble des modules du compilateur, puis produit l'exécutable `bin/qcompile`.

```bash
make clean     # Supprime les fichiers objets et l'exécutable
```

### Lancement de l'interface graphique

```bash
cd gui
python3 main.py
```

L'interface graphique localise automatiquement l'exécutable `qcompile` (dans `bin/` à la racine du projet, ou dans le répertoire courant) ; à défaut, le chemin peut être précisé explicitement lors de l'instanciation du pont de compilation (`CompilerBridge`).

## Utilisation en ligne de commande

```bash
./bin/qcompile --source mon_circuit.qtl --mode both --shots 100 --seed 42 --output mon_circuit.qasm
```

| Option              | Description                                                        | Valeur par défaut |
|---------------------|----------------------------------------------------------------------|--------------------|
| `--source FILE`     | Fichier source QuantL (`.qtl`) à compiler — **obligatoire**           | —                  |
| `--mode MODE`       | `sim` (simulation seule), `qasm` (export seul) ou `both`              | `both`             |
| `--shots N`         | Nombre de tirages de simulation indépendants                          | `1`                |
| `--seed N`          | Graine du générateur pseudo-aléatoire, pour des résultats reproductibles | `0`               |
| `--output FILE`     | Chemin du fichier de sortie QASM (mode `qasm`/`both`)                  | `output.qasm`      |
| `--debug`           | Active le mode de débogage (affichage de l'AST, verbosité du parseur)  | désactivé          |
| `--help`            | Affiche l'aide et quitte                                               | —                  |

> Si `--output` est omis, le fichier `output.qasm` est écrit dans le **répertoire de travail courant** du processus, et non à côté de l'exécutable. Il est recommandé de toujours préciser `--output` avec un chemin explicite dans tout usage scripté ou embarqué (voir la note d'implémentation dans `gui/model/compiler_bridge.py`).

## Interface graphique

L'application PyQt6 (`gui/`) suit une architecture MVC :

- **Modèle** (`gui/model/`) : `compiler_bridge.py` invoque `qcompile` en sous-processus sur un fichier temporaire et analyse sa sortie standard pour reconstruire l'AST, l'IR, le circuit, les résultats de simulation et le code QASM sous une forme exploitable par les vues ; `session.py` conserve l'état de la session (dernier résultat, dernier code source).
- **Contrôleurs** (`gui/controllers/`) : `compile_controller.py` exécute chaque compilation dans un `QThread` dédié afin de ne jamais geler l'interface, et diffuse les signaux Qt (progression, succès, erreur) vers les vues.
- **Vues** (`gui/views/`) : `main_window.py` assemble les onglets suivants —
  - **Éditeur** : édition du code source QuantL avec coloration syntaxique ;
  - **Lexical** : liste des tokens produits par l'analyseur lexical ;
  - **Circuit** : représentation structurée du circuit reconstruite depuis l'IR ;
  - **Simulation** : état quantique final, probabilités et résultats de mesure ;
  - **QASM** : code OpenQASM 2.0 généré, avec bouton de validation syntaxique et export vers un fichier `.qasm` ;
  - **Console** : sortie brute et diagnostics du compilateur natif ;
  - **À propos** : informations sur le projet.

## Exemples de circuits fournis

Le répertoire `gui/examples/` contient une progression de circuits de complexité croissante, utilisables directement depuis l'interface graphique ou en ligne de commande :

| Fichier                          | Circuit illustré                                            |
|-----------------------------------|---------------------------------------------------------------|
| `01_superposition.qtl`            | Superposition d'un unique qubit                                |
| `02_bell_state.qtl`                | Paire intriquée (état de Bell)                                 |
| `03_ghz_state.qtl`                  | État GHZ à 3 qubits (intrication multipartite)                 |
| `04_rotations_phase.qtl`             | Portes de rotation paramétrées et phase                        |
| `05_deutsch_jozsa.qtl`                | Algorithme de Deutsch-Jozsa (oracle équilibré)                  |
| `06_toffoli_logic.qtl`                | Portes logiques réversibles via Toffoli                         |
| `07_teleportation.qtl`                  | Protocole de téléportation quantique                            |
| `08_grover_search.qtl`                   | Algorithme de recherche de Grover                               |
| `09_deep_ansatz_repeat.qtl`                | Circuit paramétré profond utilisant `repeat`                    |
| `10_bitflip_qec.qtl`                        | Code de correction d'erreur à répétition (bit-flip)             |

## Export OpenQASM 2.0

Chaque programme QuantL peut être traduit en OpenQASM 2.0, avec systématiquement l'en-tête standard :

```qasm
OPENQASM 2.0;
include "qelib1.inc";

qreg q[2];
creg c[2];

h q[0];
cx q[0], q[1];
barrier q[0], q[1];
measure q[0] -> c[0];
measure q[1] -> c[1];
```

Les constructions QuantL sans équivalent strict en OpenQASM 2.0 — en particulier les conditions portant sur un bit unique d'un registre classique (`if (c[i] == v) ...`), qu'OpenQASM 2.0 ne sait exprimer qu'au niveau d'un registre entier — sont documentées explicitement en commentaire dans le fichier généré, afin de garantir que le fichier `.qasm` produit reste toujours syntaxiquement valide et chargeable dans Qiskit ou tout interpréteur OpenQASM 2.0 conforme.

## Limites connues

- **Simulation idéale uniquement** : le moteur de simulation ne modélise ni bruit, ni décohérence (pas de relaxation `T1`/`T2`, pas de portes bruitées) ; il suppose un matériel quantique parfait.
- **Passage à l'échelle** : la complexité mémoire du vecteur d'état croît en `O(2ⁿ)` ; une limite pragmatique d'environ 20 qubits (soit de l'ordre de 16 Mo d'amplitudes complexes) est recommandée pour rester dans des temps et volumes de calcul raisonnables sur une machine de bureau.
- **Absence d'optimisation de circuit** : aucune fusion ni réécriture de portes n'est effectuée avant simulation ou export, contrairement aux transpileurs des SDK quantiques matures.
- **`repeat`** génère une réexécution complète du bloc à chaque itération, sans réutilisation d'état au-delà des registres classiques.
- **Export JSON non implémenté** : les fichiers `src/json_writer.c` et `src/json_writer.h` existent mais sont actuellement vides ; cette fonctionnalité est prévue mais non réalisée.

## Pistes d'évolution

- Extensions du langage : fonctions et sous-circuits réutilisables, boucles paramétrées par variable (au-delà d'un `repeat(N)` à `N` constant), types de données classiques plus riches ;
- Modèle physique : modélisation du bruit et de la décohérence, bascule vers un back-end Qiskit réel pour l'exécution sur matériel ou simulateurs cloud ;
- Outillage : optimiseur de circuits (fusion de portes, réduction de profondeur), finalisation de l'export JSON structuré, visualisation graphique interactive du circuit, intégration de tests automatisés de bout en bout (CI).

## Documentation académique

Une présentation complète du projet (support LaTeX/Beamer, `docu/presentation.tex` et `docu/presentation.pdf`) détaille l'ensemble des phases de la chaîne de compilation, la conception du langage, le moteur de simulation, la génération OpenQASM, des études de cas sur des circuits de référence, l'architecture de l'interface graphique, ainsi que le bilan et les perspectives du projet.

## Auteur et cadre académique

NGUEUDJANG DJOMO ALAIN GILDAS --- gildas.ngueudjang@facsciences-uy1.cm

Projet réalisé dans le cadre d'un cursus de **Master 1 Informatique**, à des fins pédagogiques d'illustration des phases classiques de compilation appliquées à un domaine spécifique (langages dédiés à la programmation quantique).
