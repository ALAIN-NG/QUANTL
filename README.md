# quantl

quantl est un projet de compilateur / interpréteur pour un langage de programmation simple et pédagogique. Ce README explique les objectifs, l'architecture, les composants principaux, l'installation, l'utilisation, les exemples de code et les contributions possibles.

## Objectif

Le projet quantl a pour but de fournir :

- un langage de programmation simple, conçu pour l'apprentissage des concepts de compilation,
- un compilateur minimal capable de transformer le code source quantl en une représentation intermédiaire ou en binaire,
- un interpréteur pour exécuter directement des programmes quantl sans passer par une phase de compilation complète,
- un ensemble de tests pour valider les étapes de l'analyse lexicale, de l'analyse syntaxique, de la génération de code et de l'exécution.

L'objectif principal est de permettre l'étude des phases classiques d'un compilateur : analyse lexicale, analyse syntaxique, vérification contextuelle, génération de code et optimisation basique.

## Fonctionnalités supportées

Le langage quantl supporte actuellement :

- déclaration de variables (entier, réel, booléen, chaîne),
- opérations arithmétiques et logiques,
- structures de contrôle : conditions (`si`, `sinon`) et boucles (`tantque`),
- fonctions et procédures avec paramètres et valeurs de retour,
- entrées/sorties basiques (`afficher`, `lire`),
- commentaires sur une ligne (`//`).

## Architecture du projet

Le compilateur est organisé en plusieurs modules :

- `lexer/` : tokenisation du code source, reconnaissance des mots-clés, identificateurs et littéraux,
- `parser/` : construction de l'arbre syntaxique abstrait (AST) à partir des tokens,
- `semantics/` : vérification des types, déclarations, portées et cohérence des symboles,
- `ir/` : génération d'une représentation intermédiaire pour faciliter la traduction vers une cible,
- `backend/` : génération de code natif ou en bytecode selon la configuration,
- `interpreter/` : exécution directe de l'AST ou de l'IR pour le mode interprété,
- `tests/` : suite de tests unitaires et tests d'intégration pour valider le comportement du langage.

## Installation

1. Cloner le dépôt :
   ```bash
   git clone <url-du-depot> quantl
   cd quantl
   ```

2. Pré-requis :
   - un compilateur C/C++ moderne (`gcc`, `clang`, `g++`),
   - `make` ou `cmake`,
   - éventuellement `python` ou un interpréteur de test pour exécuter les cas de test.

3. Construire le projet :
   ```bash
   make
   ```

   ou si vous utilisez CMake :

   ```bash
   mkdir build
   cd build
   cmake ..
   make
   ```

4. Vérifier l'installation :
   ```bash
   ./quantlc --version
   ```

## Utilisation

### Compilation d'un programme quantl

```bash
./quantlc examples/exemple.qtl -o exemple.out
```

### Exécution via l'interpréteur

```bash
./quantl_run examples/exemple.qtl
```

### Options courantes

- `-o <fichier>` : fichier de sortie pour le code compilé,
- `--debug` : activer les informations de débogage,
- `--ast` : afficher l'arbre syntaxique abstrait,
- `--help` : afficher l'aide.

## Structure du projet

Une structure typique du dépôt est la suivante :

- `src/` : code source du compilateur,
- `include/` : fichiers d'en-tête,
- `lexer/`, `parser/`, `semantics/`, `backend/`, `interpreter/` : modules du compilateur,
- `tests/` : scénarios de tests automatisés,
- `examples/` : programmes d'exemple écrits en quantl,
- `docs/` : documentation du langage et du compilateur,
- `Makefile`, `CMakeLists.txt` : scripts de construction,
- `README.md` : documentation du projet.

## Exemple de code quantl

Voici un exemple plus complet illustrant les fonctionnalités de base :

```quantl
// Exemple de programme quantl
fonction entier factorielle(entier n) {
    si (n <= 1) {
        retourner 1;
    } sinon {
        retourner n * factorielle(n - 1);
    }
}

fonction principal() {
    entier valeur = 5;
    entier resultat = factorielle(valeur);
    afficher("Factorielle de ");
    afficher(valeur);
    afficher(" = ");
    afficher(resultat);
}
```

### Exemple avec boucle et lecture utilisateur

```quantl
fonction principal() {
    entier compteur = 0;
    entier limite = 10;

    tantque (compteur < limite) {
        afficher(compteur);
        compteur = compteur + 1;
    }
}
```

## Tests

Le projet inclut plusieurs jeux de tests :

- tests unitaires du lexer et du parser,
- tests de validation des types et des symboles,
- tests d'exécution de programmes quantl,
- tests de régression pour les erreurs connues.

Pour exécuter les tests :

```bash
make test
```

ou

```bash
ctest --output-on-failure
```

## Contribution

Les contributions sont bienvenues. Voici les axes principaux :

- ajouter de nouveaux tests pour les fonctionnalités existantes,
- étendre le langage avec de nouvelles constructions syntaxiques,
- améliorer la gestion des erreurs et les messages d'erreur,
- implémenter des optimisations de la génération de code,
- documenter le langage et rédiger des tutoriels.

Pour contribuer :

1. créer une branche dédiée,
2. implémenter une fonctionnalité ou corriger un bug,
3. ajouter des tests pertinents,
4. ouvrir une pull request avec une description claire.

## Licence

Ce projet peut être distribué sous une licence open source. Exemple :

- MIT
- Apache 2.0
- GPL v3

Remplacez cette section par la licence choisie.

## Contact

Pour toute question ou suggestion, contactez l'auteur du projet ou ouvrez une issue sur le dépôt.
