// main.c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <getopt.h>
#include <unistd.h>
#include "ast.h"
#include "semantic.h"
#include "ir.h"
#include "sim_engine.h"
#include "codegen_qasm.h"

// Déclaration des fonctions externes
extern int yyparse(void);
extern FILE* yyin;
extern NoeudAST* racine_ast;
extern int ligne_courante;
int yydebug = 0;

void yyerror(const char *msg) {
    fprintf(stderr, "Erreur (ligne %d) : %s\n", ligne_courante, msg);
}

void afficher_usage(char* prog) {
    printf("QuantL - Compilateur quantique\n");
    printf("Usage: %s --source fichier.qtl [OPTIONS]\n", prog);
    printf("Options:\n");
    printf("  --source FILE    Fichier source QuantL (.qtl)\n");
    printf("  --mode MODE      Mode: sim, qasm, both (défaut: both)\n");
    printf("  --seed N         Graine aléatoire pour la simulation\n");
    printf("  --shots N        Nombre de tirages (défaut: 1)\n");
    printf("  --output FILE    Fichier de sortie pour les résultats\n");
    printf("  --help           Afficher cette aide\n");
    printf("  --debug          Activer le débogage du parser\n");
}

int main(int argc, char** argv) {
    char* source = NULL;
    char* mode = "both";
    char* output = NULL;
    int seed = 0;
    int shots = 1;
    int debug = 0;
    
    static struct option long_options[] = {
        {"source", required_argument, 0, 's'},
        {"mode", required_argument, 0, 'm'},
        {"seed", required_argument, 0, 'S'},
        {"shots", required_argument, 0, 'n'},
        {"output", required_argument, 0, 'o'},
        {"debug", no_argument, 0, 'd'},
        {"help", no_argument, 0, 'h'},
        {0, 0, 0, 0}
    };
    
    int c;
    while ((c = getopt_long(argc, argv, "s:m:S:n:o:dh", long_options, NULL)) != -1) {
        switch (c) {
            case 's':
                source = optarg;
                break;
            case 'm':
                mode = optarg;
                break;
            case 'S':
                seed = atoi(optarg);
                break;
            case 'n':
                shots = atoi(optarg);
                break;
            case 'o':
                output = optarg;
                break;
            case 'd':
                debug = 1;
                break;
            case 'h':
            default:
                afficher_usage(argv[0]);
                return 0;
        }
    }
    
    if (!source) {
        fprintf(stderr, "Erreur: --source est obligatoire.\n");
        afficher_usage(argv[0]);
        return 1;
    }
    
    yydebug = debug;
    
    yyin = fopen(source, "r");
    if (!yyin) {
        fprintf(stderr, "Erreur: impossible d'ouvrir le fichier %s\n", source);
        return 1;
    }
    
    printf("Analyse du fichier: %s\n", source);
    if (yyparse() != 0) {
        fprintf(stderr, "Erreur d'analyse syntaxique.\n");
        fclose(yyin);
        return 1;
    }
    fclose(yyin);
    
    if (!racine_ast) {
        fprintf(stderr, "AST vide.\n");
        return 1;
    }
    
    if (debug) {
        printf("\nAST généré:\n");
        ast_afficher(racine_ast, 0);
        printf("\n");
    }
    
    printf("Analyse sémantique...\n");
    if (analyser_semantique(racine_ast) != 0) {
        fprintf(stderr, "Erreur sémantique.\n");
        return 1;
    }
    printf("Analyse sémantique réussie.\n");
    
    printf("Génération de l'IR...\n");
    InstructionIR* ir = generer_ir(racine_ast);
    if (!ir) {
        fprintf(stderr, "Erreur de génération de l'IR.\n");
        // Afficher l'AST pour déboguer
        printf("\nAST avant IR:\n");
        ast_afficher(racine_ast, 0);
        return 1;
    }
    
    printf("\nIR généré:\n");
    afficher_ir(ir);
    printf("\n");
    
    if (strcmp(mode, "sim") == 0 || strcmp(mode, "both") == 0) {
        int nb_qubits = 0, nb_bits = 0;
        InstructionIR* courant = ir;
        while (courant) {
            if (courant->op == OP_MEASURE) {
                if (courant->bit_classique >= nb_bits) {
                    nb_bits = courant->bit_classique + 1;
                }
            }
            if (courant->nb_qubits > 0) {
                for (int i = 0; i < courant->nb_qubits; i++) {
                    if (courant->qubits[i] >= nb_qubits) {
                        nb_qubits = courant->qubits[i] + 1;
                    }
                }
            }
            courant = courant->suivant;
        }
        if (nb_qubits < 1) nb_qubits = 1;
        if (nb_bits < 1) nb_bits = 1;
        
        printf("\nSimulation (%d qubits, %d bits classiques)...\n", nb_qubits, nb_bits);
        printf("Graine aléatoire: %d, Tirages: %d\n", seed, shots);
        
        // FIX: Seed gérée dans sim_initialiser, pas ici
        for (int shot = 0; shot < shots; shot++) {
            if (shots > 1) {
                printf("\n--- Tirage %d ---\n", shot + 1);
            }
            
            // Passer la seed à l'initialisation (FIX: bug seed ignorée)
            Simulateur* sim = sim_initialiser(nb_qubits, nb_bits, seed);
            if (!sim) {
                fprintf(stderr, "Erreur d'initialisation du simulateur.\n");
                return 1;
            }
            
            sim_appliquer_ir(sim, ir);
            sim_liberer(sim);
        }
    }
    
    if (strcmp(mode, "qasm") == 0 || strcmp(mode, "both") == 0) {
        char* qasm_file = output ? output : "output.qasm";
        printf("\nGénération du code QASM vers %s...\n", qasm_file);
        generer_qasm(ir, qasm_file);
    }
    
    liberer_ir(ir);
    ast_liberer(racine_ast);
    
    printf("\nCompilation terminée.\n");
    return 0;
}