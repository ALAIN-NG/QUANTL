#ifndef IR_H
#define IR_H

#include "ast.h"

typedef enum {
    OP_H, OP_X, OP_Y, OP_Z, OP_S, OP_T,
    OP_RX, OP_RY, OP_RZ,
    OP_CX, OP_CZ, OP_SWAP, OP_TOFFOLI,
    OP_MEASURE, OP_IF_DEBUT, OP_IF_FIN,
    OP_BARRIER, OP_PRINT_STATE, OP_PRINT_PROBS
} OpCode;

typedef struct InstructionIR {
    OpCode op;
    int qubits[3];
    int nb_qubits;
    int bit_classique;
    double angle;
    int condition_bit;
    int condition_val;
    int ligne_source;
    int registre_id;  // ID du registre quantique source (FIX: mapping multi-registre)
    struct InstructionIR *suivant;
} InstructionIR;

// Table de mapping registre (nom) -> qubit (indice global)
typedef struct {
    char* nom_registre;
    int qubit_debut;  // Premier qubit de ce registre
    int taille;       // Nombre de qubits
} RegistreMapping;

// Prototypes
InstructionIR* generer_ir(NoeudAST* ast);
void liberer_ir(InstructionIR* ir);
void afficher_ir(InstructionIR* ir);

#endif