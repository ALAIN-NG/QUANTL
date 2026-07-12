#include "ast.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

// Fonction pour créer un nouveau nœud AST
NoeudAST* ast_creer_noeud(TypeNoeud type, int ligne) {
    NoeudAST* n = (NoeudAST*)calloc(1, sizeof(NoeudAST));
    if (!n) {
        fprintf(stderr, "Erreur d'allocation mémoire\n");
        exit(1);
    }
    n->type = type;
    n->ligne = ligne;
    n->suivant = NULL;
    return n;
}

// Créer une liste vide
NoeudAST* ast_creer_liste_vide() {
    return NULL;
}

// Ajouter une instruction à une liste
NoeudAST* ast_ajouter_instruction(NoeudAST* liste, NoeudAST* instr) {
    if (!instr) return liste;
    if (!liste) return instr;
    
    NoeudAST* courant = liste;
    while (courant->suivant) {
        courant = courant->suivant;
    }
    courant->suivant = instr;
    return liste;
}

// Créer un programme (liste d'instructions)
NoeudAST* ast_creer_programme(NoeudAST* liste) {
    NoeudAST* n = ast_creer_noeud(N_PROGRAMME, 0);
    n->premier = liste;
    return n;
}

// Déclaration de registre quantique ou classique
NoeudAST* ast_decl_registre(TypeRegistre type, char* nom, int taille, int ligne) {
    NoeudAST* n = ast_creer_noeud((type == QUANTIQUE) ? N_DECL_QREG : N_DECL_CREG, ligne);
    n->decl.nom_registre = strdup(nom);
    n->decl.taille = taille;
    n->decl.type_reg = type;
    return n;
}

// Porte à 1 qubit (H, X, Y, Z, S, T, RX, RY, RZ)
NoeudAST* ast_porte_1q(char* nom_porte, char* nom_reg, int indice, double angle, int ligne) {
    NoeudAST* n = ast_creer_noeud(N_PORTE_1Q, ligne);
    n->porte_1q.nom_porte = strdup(nom_porte);
    n->porte_1q.nom_reg = strdup(nom_reg);
    n->porte_1q.indice_qubit = indice;
    n->porte_1q.angle = angle;
    // Détecter si la porte a un angle ou non
    n->porte_1q.a_angle = (angle != 0.0 || strcmp(nom_porte, "rx") == 0 || 
                           strcmp(nom_porte, "ry") == 0 || strcmp(nom_porte, "rz") == 0);
    return n;
}

// Porte à 2 qubits (CX, CZ, SWAP)
NoeudAST* ast_porte_2q(char* nom_porte, char* nom_reg1, int indice1, char* nom_reg2, int indice2, int ligne) {
    NoeudAST* n = ast_creer_noeud(N_PORTE_2Q, ligne);
    n->porte_2q.nom_porte = strdup(nom_porte);
    n->porte_2q.nom_reg1 = strdup(nom_reg1);
    n->porte_2q.indice1 = indice1;
    n->porte_2q.nom_reg2 = strdup(nom_reg2);
    n->porte_2q.indice2 = indice2;
    return n;
}

// Porte Toffoli (3 qubits)
NoeudAST* ast_porte_toffoli(char* reg1, int i1, char* reg2, int i2, char* reg3, int i3, int ligne) {
    NoeudAST* n = ast_creer_noeud(N_PORTE_TOFFOLI, ligne);
    n->porte_toffoli.nom_reg1 = strdup(reg1);
    n->porte_toffoli.indice1 = i1;
    n->porte_toffoli.nom_reg2 = strdup(reg2);
    n->porte_toffoli.indice2 = i2;
    n->porte_toffoli.nom_reg3 = strdup(reg3);
    n->porte_toffoli.indice3 = i3;
    return n;
}

// Instruction de mesure
NoeudAST* ast_mesure(char* reg_qubit, int i_qubit, char* reg_bit, int i_bit, int ligne) {
    NoeudAST* n = ast_creer_noeud(N_MESURE, ligne);
    n->mesure.nom_reg_qubit = strdup(reg_qubit);
    n->mesure.indice_qubit = i_qubit;
    n->mesure.nom_reg_bit = strdup(reg_bit);
    n->mesure.indice_bit = i_bit;
    return n;
}

// Instruction conditionnelle IF
NoeudAST* ast_if(char* reg_bit, int i_bit, int valeur, NoeudAST* instr, int ligne) {
    NoeudAST* n = ast_creer_noeud(N_IF, ligne);
    n->if_instr.nom_reg_bit = strdup(reg_bit);
    n->if_instr.indice_bit = i_bit;
    n->if_instr.valeur = valeur;
    n->if_instr.instruction = instr;
    return n;
}

// Print state
NoeudAST* ast_print_state(int ligne) {
    NoeudAST* n = ast_creer_noeud(N_PRINT, ligne);
    n->print_instr.mode = 0;
    n->print_instr.chaine = NULL;
    return n;
}

// Print probs
NoeudAST* ast_print_probs(int ligne) {
    NoeudAST* n = ast_creer_noeud(N_PRINT, ligne);
    n->print_instr.mode = 1;
    n->print_instr.chaine = NULL;
    return n;
}

// Print string (bonus)
NoeudAST* ast_print_string(char* chaine, int ligne) {
    NoeudAST* n = ast_creer_noeud(N_PRINT, ligne);
    n->print_instr.mode = 2;
    n->print_instr.chaine = strdup(chaine);
    return n;
}

// Instruction BARRIER
NoeudAST* ast_barrier(Reference* qubits, int nb_qubits, int ligne) {
    NoeudAST* n = ast_creer_noeud(N_BARRIER, ligne);
    n->barrier.qubits = qubits;
    n->barrier.nb_qubits = nb_qubits;
    return n;
}

// Instruction REPEAT
NoeudAST* ast_repeat(int repetitions, NoeudAST* bloc, int ligne) {
    NoeudAST* n = ast_creer_noeud(N_REPEAT, ligne);
    n->repeat.repetitions = repetitions;
    n->repeat.bloc = bloc;
    return n;
}

// Afficher un nœud AST avec son indice
void ast_afficher_noeud(NoeudAST* noeud, int niveau, int index) {
    if (!noeud) {
        printf("[NULL]\n");
        return;
    }
    
    // Vérifier la profondeur maximale (sécurité contre débordement récursif)
    if (niveau > MAX_AST_DEPTH) {
        printf("[... profondeur max atteinte ...]\n");
        return;
    }
    
    // Allocation dynamique sûre du buffer d'indentation
    int indent_size = niveau * 2 + 1;
    char* indent = (char*)malloc(indent_size);
    if (!indent) {
        fprintf(stderr, "Erreur d'allocation mémoire pour indentation\n");
        return;
    }
    
    for (int i = 0; i < niveau * 2; i++) indent[i] = ' ';
    indent[niveau * 2] = '\0';
    
    printf("%s[%d] ", indent, index);
    
    switch (noeud->type) {
        case N_PROGRAMME:
            printf("PROGRAMME");
            break;
        case N_DECL_QREG:
            printf("DECL_QREG: %s[%d]", noeud->decl.nom_registre, noeud->decl.taille);
            break;
        case N_DECL_CREG:
            printf("DECL_CREG: %s[%d]", noeud->decl.nom_registre, noeud->decl.taille);
            break;
        case N_PORTE_1Q:
            printf("PORTE_1Q: %s %s[%d]", noeud->porte_1q.nom_porte, 
                   noeud->porte_1q.nom_reg, noeud->porte_1q.indice_qubit);
            if (noeud->porte_1q.a_angle) printf("(%.4f)", noeud->porte_1q.angle);
            break;
        case N_PORTE_2Q:
            printf("PORTE_2Q: %s %s[%d], %s[%d]", noeud->porte_2q.nom_porte,
                   noeud->porte_2q.nom_reg1, noeud->porte_2q.indice1,
                   noeud->porte_2q.nom_reg2, noeud->porte_2q.indice2);
            break;
        case N_PORTE_TOFFOLI:
            printf("TOFFOLI: %s[%d], %s[%d], %s[%d]",
                   noeud->porte_toffoli.nom_reg1, noeud->porte_toffoli.indice1,
                   noeud->porte_toffoli.nom_reg2, noeud->porte_toffoli.indice2,
                   noeud->porte_toffoli.nom_reg3, noeud->porte_toffoli.indice3);
            break;
        case N_MESURE:
            printf("MESURE: %s[%d] -> %s[%d]", noeud->mesure.nom_reg_qubit,
                   noeud->mesure.indice_qubit, noeud->mesure.nom_reg_bit,
                   noeud->mesure.indice_bit);
            break;
        case N_IF:
            printf("IF: %s[%d] == %d", noeud->if_instr.nom_reg_bit,
                   noeud->if_instr.indice_bit, noeud->if_instr.valeur);
            break;
        case N_PRINT:
            if (noeud->print_instr.mode == 0) printf("PRINT state");
            else if (noeud->print_instr.mode == 1) printf("PRINT probs");
            else printf("PRINT \"%s\"", noeud->print_instr.chaine);
            break;
        case N_BARRIER:
            printf("BARRIER (%d qubits)", noeud->barrier.nb_qubits);
            break;
        case N_REPEAT:
            printf("REPEAT %d fois", noeud->repeat.repetitions);
            break;
        default:
            printf("UNKNOWN(%d)", noeud->type);
            break;
    }
    printf(" (ligne %d)\n", noeud->ligne);
    
    // Afficher les enfants pour certains types
    if (noeud->type == N_IF) {
        ast_afficher_noeud(noeud->if_instr.instruction, niveau + 1, 0);
    } else if (noeud->type == N_REPEAT) {
        ast_afficher_noeud(noeud->repeat.bloc, niveau + 1, 0);
    } else if (noeud->type == N_PROGRAMME) {
        ast_afficher_noeud(noeud->premier, niveau + 1, 0);
    }
    
    // Libérer le buffer d'indentation
    free(indent);
}

// Afficher tout l'AST (liste d'instructions)
void ast_afficher(NoeudAST* noeud, int niveau) {
    if (!noeud) {
        printf("[AST VIDE]\n");
        return;
    }
    
    int index = 0;
    NoeudAST* courant = noeud;
    while (courant) {
        ast_afficher_noeud(courant, niveau, index++);
        courant = courant->suivant;
    }
}

// Libérer la mémoire de l'AST
void ast_liberer(NoeudAST* noeud) {
    if (!noeud) return;
    
    switch (noeud->type) {
        case N_DECL_QREG:
        case N_DECL_CREG:
            free(noeud->decl.nom_registre);
            break;
            
        case N_PORTE_1Q:
            free(noeud->porte_1q.nom_porte);
            free(noeud->porte_1q.nom_reg);
            break;
            
        case N_PORTE_2Q:
            free(noeud->porte_2q.nom_porte);
            free(noeud->porte_2q.nom_reg1);
            free(noeud->porte_2q.nom_reg2);
            break;
            
        case N_PORTE_TOFFOLI:
            free(noeud->porte_toffoli.nom_reg1);
            free(noeud->porte_toffoli.nom_reg2);
            free(noeud->porte_toffoli.nom_reg3);
            break;
            
        case N_MESURE:
            free(noeud->mesure.nom_reg_qubit);
            free(noeud->mesure.nom_reg_bit);
            break;
            
        case N_IF:
            free(noeud->if_instr.nom_reg_bit);
            ast_liberer(noeud->if_instr.instruction);
            break;
            
        case N_PRINT:
            if (noeud->print_instr.chaine) {
                free(noeud->print_instr.chaine);
            }
            break;
            
        case N_BARRIER:
            if (noeud->barrier.qubits) {
                for (int i = 0; i < noeud->barrier.nb_qubits; i++) {
                    free(noeud->barrier.qubits[i].nom_registre);
                }
                free(noeud->barrier.qubits);
            }
            break;
            
        case N_REPEAT:
            ast_liberer(noeud->repeat.bloc);
            break;
            
        case N_PROGRAMME:
            ast_liberer(noeud->premier);
            break;
            
        default:
            break;
    }
    
    // Libérer le nœud suivant (liste chaînée)
    if (noeud->suivant) {
        ast_liberer(noeud->suivant);
    }
    
    free(noeud);
}