#ifndef AST_H
#define AST_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

// Types de registres
typedef enum { QUANTIQUE, CLASSIQUE } TypeRegistre;

// Types de nœuds de l'AST
typedef enum {
    N_PROGRAMME,
    N_DECL_QREG,
    N_DECL_CREG,
    N_PORTE_1Q,
    N_PORTE_2Q,
    N_PORTE_TOFFOLI,
    N_MESURE,
    N_IF,
    N_PRINT,
    N_BARRIER,
    N_REPEAT
} TypeNoeud;

// Structure pour stocker une référence de qubit/bit
typedef struct {
    char* nom_registre;
    int indice;
} Reference;


// Structure principale du nœud AST
typedef struct NoeudAST {
    TypeNoeud type;
    int ligne;
    struct NoeudAST* suivant;
    
    union {
        struct {
            char* nom_registre;
            int taille;
            TypeRegistre type_reg;
        } decl;
        
        struct {
            char* nom_porte;
            char* nom_reg;
            int indice_qubit;
            double angle;
            bool a_angle;
        } porte_1q;
        
        struct {
            char* nom_porte;
            char* nom_reg1;
            int indice1;
            char* nom_reg2;
            int indice2;
        } porte_2q;
        
        struct {
            char* nom_reg1;
            int indice1;
            char* nom_reg2;
            int indice2;
            char* nom_reg3;
            int indice3;
        } porte_toffoli;
        
        struct {
            char* nom_reg_qubit;
            int indice_qubit;
            char* nom_reg_bit;
            int indice_bit;
        } mesure;
        
        struct {
            char* nom_reg_bit;
            int indice_bit;
            int valeur;
            struct NoeudAST* instruction;
        } if_instr;
        
        struct {
            int mode;  // 0: state, 1: probs, 2: string
            char* chaine;
        } print_instr;
        
        struct {
            Reference* qubits;
            int nb_qubits;
        } barrier;
        
        struct {
            int repetitions;
            struct NoeudAST* bloc;
        } repeat;
        
        struct NoeudAST* premier;  // Pour N_PROGRAMME
    };
} NoeudAST;

// Déclaration de la racine de l'AST (définie dans quantl.y)
extern NoeudAST* racine_ast;

// Fonctions de construction de l'AST
NoeudAST* ast_creer_noeud(TypeNoeud type, int ligne);
NoeudAST* ast_creer_liste_vide();
NoeudAST* ast_ajouter_instruction(NoeudAST* liste, NoeudAST* instr);
NoeudAST* ast_creer_programme(NoeudAST* liste);
NoeudAST* ast_decl_registre(TypeRegistre type, char* nom, int taille, int ligne);
NoeudAST* ast_porte_1q(char* nom_porte, char* nom_reg, int indice, double angle, int ligne);
NoeudAST* ast_porte_2q(char* nom_porte, char* nom_reg1, int indice1, char* nom_reg2, int indice2, int ligne);
NoeudAST* ast_porte_toffoli(char* reg1, int i1, char* reg2, int i2, char* reg3, int i3, int ligne);
NoeudAST* ast_mesure(char* reg_qubit, int i_qubit, char* reg_bit, int i_bit, int ligne);
NoeudAST* ast_if(char* reg_bit, int i_bit, int valeur, NoeudAST* instr, int ligne);
NoeudAST* ast_print_state(int ligne);
NoeudAST* ast_print_probs(int ligne);
NoeudAST* ast_print_string(char* chaine, int ligne);
NoeudAST* ast_barrier(Reference* qubits, int nb_qubits, int ligne);
NoeudAST* ast_repeat(int repetitions, NoeudAST* bloc, int ligne);

// Fonctions d'affichage et de libération
void ast_afficher(NoeudAST* noeud, int niveau);
void ast_afficher_noeud(NoeudAST* noeud, int niveau, int index);
void ast_liberer(NoeudAST* noeud);

// Limites de profondeur pour sécurité
#define MAX_AST_DEPTH 100

#endif