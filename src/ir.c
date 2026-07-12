#include "ir.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

// Structure pour suivre l'état de la génération d'IR
typedef struct {
    InstructionIR* debut;
    InstructionIR* fin;
    int nb_qubits;
    int nb_bits;
    RegistreMapping* registres;  // Table de mapping registre→qubit
    int nb_registres;
} IRContext;

// Prototypes
void generer_ir_depuis_ast(NoeudAST* noeud, IRContext* ctx);
InstructionIR* creer_instruction(OpCode op, int ligne);
void ajouter_instruction(IRContext* ctx, InstructionIR* instr);
OpCode get_opcode_porte_1q(char* nom);
OpCode get_opcode_porte_2q(char* nom);
void ajouter_registre_mapping(IRContext* ctx, char* nom, int taille);
int obtenir_qubit_global(IRContext* ctx, char* nom_registre, int indice_local, int* registre_id);
void liberer_registre_mapping(IRContext* ctx);

InstructionIR* creer_instruction(OpCode op, int ligne) {
    InstructionIR* ir = (InstructionIR*)calloc(1, sizeof(InstructionIR));
    if (!ir) {
        fprintf(stderr, "Erreur d'allocation mémoire\n");
        exit(1);
    }
    ir->op = op;
    ir->ligne_source = ligne;
    ir->nb_qubits = 0;
    ir->bit_classique = -1;
    ir->angle = 0.0;
    ir->condition_bit = -1;
    ir->condition_val = 0;
    ir->suivant = NULL;
    return ir;
}

void ajouter_instruction(IRContext* ctx, InstructionIR* instr) {
    if (!instr) return;
    if (!ctx->debut) {
        ctx->debut = instr;
        ctx->fin = instr;
    } else {
        ctx->fin->suivant = instr;
        ctx->fin = instr;
    }
}

OpCode get_opcode_porte_1q(char* nom) {
    if (strcmp(nom, "h") == 0) return OP_H;
    if (strcmp(nom, "x") == 0) return OP_X;
    if (strcmp(nom, "y") == 0) return OP_Y;
    if (strcmp(nom, "z") == 0) return OP_Z;
    if (strcmp(nom, "s") == 0) return OP_S;
    if (strcmp(nom, "t") == 0) return OP_T;
    if (strcmp(nom, "rx") == 0) return OP_RX;
    if (strcmp(nom, "ry") == 0) return OP_RY;
    if (strcmp(nom, "rz") == 0) return OP_RZ;
    fprintf(stderr, "Porte 1Q inconnue: %s\n", nom);
    return OP_H;
}

OpCode get_opcode_porte_2q(char* nom) {
    if (strcmp(nom, "cx") == 0) return OP_CX;
    if (strcmp(nom, "cz") == 0) return OP_CZ;
    if (strcmp(nom, "swap") == 0) return OP_SWAP;
    fprintf(stderr, "Porte 2Q inconnue: %s\n", nom);
    return OP_CX;
}

// Ajouter un registre à la table de mapping (FIX: bug registres multi-qubits)
void ajouter_registre_mapping(IRContext* ctx, char* nom, int taille) {
    if (!ctx || !nom) return;
    
    ctx->registres = (RegistreMapping*)realloc(ctx->registres, 
                                                (ctx->nb_registres + 1) * sizeof(RegistreMapping));
    if (!ctx->registres) {
        fprintf(stderr, "Erreur d'allocation mémoire pour mapping registre\n");
        return;
    }
    
    ctx->registres[ctx->nb_registres].nom_registre = strdup(nom);
    ctx->registres[ctx->nb_registres].qubit_debut = ctx->nb_qubits;
    ctx->registres[ctx->nb_registres].taille = taille;
    
    ctx->nb_qubits += taille;
    ctx->nb_registres++;
}

// Obtenir le qubit global à partir d'un registre et indice local
int obtenir_qubit_global(IRContext* ctx, char* nom_registre, int indice_local, int* registre_id) {
    if (!ctx || !nom_registre) return -1;
    
    for (int i = 0; i < ctx->nb_registres; i++) {
        if (strcmp(ctx->registres[i].nom_registre, nom_registre) == 0) {
            if (indice_local < 0 || indice_local >= ctx->registres[i].taille) {
                fprintf(stderr, "Erreur: indice %d hors limites pour registre %s (taille %d)\n",
                        indice_local, nom_registre, ctx->registres[i].taille);
                return -1;
            }
            if (registre_id) *registre_id = i;
            return ctx->registres[i].qubit_debut + indice_local;
        }
    }
    
    fprintf(stderr, "Erreur: registre %s non trouvé\n", nom_registre);
    return -1;
}

// Libérer la table de mapping
void liberer_registre_mapping(IRContext* ctx) {
    if (!ctx || !ctx->registres) return;
    
    for (int i = 0; i < ctx->nb_registres; i++) {
        free(ctx->registres[i].nom_registre);
    }
    free(ctx->registres);
    ctx->registres = NULL;
    ctx->nb_registres = 0;
}

void generer_ir_depuis_ast(NoeudAST* noeud, IRContext* ctx) {
    if (!noeud) {
        return;
    }
    
    // Parcourir la liste chaînée d'instructions
    NoeudAST* courant = noeud;
    while (courant) {
        switch (courant->type) {
            case N_DECL_QREG: {
                // Ajouter à la table de mapping (FIX: registres multi-qubits)
                ajouter_registre_mapping(ctx, courant->decl.nom_registre, courant->decl.taille);
                break;
            }
            case N_DECL_CREG:
                // Les déclarations classiques ignorées (pas de mapping requis)
                break;
                
            case N_PORTE_1Q: {
                OpCode op = get_opcode_porte_1q(courant->porte_1q.nom_porte);
                InstructionIR* ir = creer_instruction(op, courant->ligne);
                
                // Utiliser le mapping pour obtenir l'indice global (FIX: registres multi-qubits)
                int registre_id = -1;
                int qubit_global = obtenir_qubit_global(ctx, courant->porte_1q.nom_reg, 
                                                        courant->porte_1q.indice_qubit, &registre_id);
                if (qubit_global >= 0) {
                    ir->qubits[0] = qubit_global;
                    ir->registre_id = registre_id;
                    ir->nb_qubits = 1;
                    ir->angle = courant->porte_1q.angle;
                    ajouter_instruction(ctx, ir);
                } else {
                    free(ir);  // Libérer en cas d'erreur
                }
                break;
            }
                
            case N_PORTE_2Q: {
                OpCode op = get_opcode_porte_2q(courant->porte_2q.nom_porte);
                InstructionIR* ir = creer_instruction(op, courant->ligne);
                
                // Utiliser le mapping pour obtenir les indices globaux (FIX: registres multi-qubits)
                int q1 = obtenir_qubit_global(ctx, courant->porte_2q.nom_reg1, 
                                               courant->porte_2q.indice1, NULL);
                int q2 = obtenir_qubit_global(ctx, courant->porte_2q.nom_reg2, 
                                               courant->porte_2q.indice2, NULL);
                
                if (q1 >= 0 && q2 >= 0) {
                    ir->qubits[0] = q1;
                    ir->qubits[1] = q2;
                    ir->nb_qubits = 2;
                    ajouter_instruction(ctx, ir);
                } else {
                    free(ir);  // Libérer en cas d'erreur
                }
                break;
            }
                
            case N_PORTE_TOFFOLI: {
                InstructionIR* ir = creer_instruction(OP_TOFFOLI, courant->ligne);
                
                // Utiliser le mapping pour obtenir les indices globaux
                int q1 = obtenir_qubit_global(ctx, courant->porte_toffoli.nom_reg1, 
                                               courant->porte_toffoli.indice1, NULL);
                int q2 = obtenir_qubit_global(ctx, courant->porte_toffoli.nom_reg2, 
                                               courant->porte_toffoli.indice2, NULL);
                int q3 = obtenir_qubit_global(ctx, courant->porte_toffoli.nom_reg3, 
                                               courant->porte_toffoli.indice3, NULL);
                
                if (q1 >= 0 && q2 >= 0 && q3 >= 0) {
                    ir->qubits[0] = q1;
                    ir->qubits[1] = q2;
                    ir->qubits[2] = q3;
                    ir->nb_qubits = 3;
                    ajouter_instruction(ctx, ir);
                } else {
                    free(ir);
                }
                break;
            }
                
            case N_MESURE: {
                InstructionIR* ir = creer_instruction(OP_MEASURE, courant->ligne);
                
                // Utiliser le mapping pour obtenir l'indice global du qubit
                int qubit_global = obtenir_qubit_global(ctx, courant->mesure.nom_reg_qubit, 
                                                        courant->mesure.indice_qubit, NULL);
                
                if (qubit_global >= 0) {
                    ir->qubits[0] = qubit_global;
                    ir->bit_classique = courant->mesure.indice_bit;
                    ir->nb_qubits = 1;
                    
                    if (ctx->nb_bits <= ir->bit_classique) {
                        ctx->nb_bits = ir->bit_classique + 1;
                    }
                    
                    ajouter_instruction(ctx, ir);
                } else {
                    free(ir);
                }
                break;
            }
                
            case N_IF: {
                // Début du if
                InstructionIR* ir_debut = creer_instruction(OP_IF_DEBUT, courant->ligne);
                ir_debut->condition_bit = courant->if_instr.indice_bit;
                ir_debut->condition_val = courant->if_instr.valeur;
                
                if (ctx->nb_bits <= ir_debut->condition_bit) {
                    ctx->nb_bits = ir_debut->condition_bit + 1;
                }
                
                ajouter_instruction(ctx, ir_debut);
                
                // Instructions du if
                if (courant->if_instr.instruction) {
                    generer_ir_depuis_ast(courant->if_instr.instruction, ctx);
                }
                
                // Fin du if
                InstructionIR* ir_fin = creer_instruction(OP_IF_FIN, courant->ligne);
                ajouter_instruction(ctx, ir_fin);
                break;
            }
                
            case N_PRINT: {
                OpCode op = (courant->print_instr.mode == 0) ? OP_PRINT_STATE : OP_PRINT_PROBS;
                InstructionIR* ir = creer_instruction(op, courant->ligne);
                ajouter_instruction(ctx, ir);
                break;
            }
                
            case N_BARRIER: {
                InstructionIR* ir = creer_instruction(OP_BARRIER, courant->ligne);
                if (courant->barrier.nb_qubits > 0) {
                    // FIX: Limiter à 3 qubits max dans IR (structure limitée) ou utiliser allocation dynamique
                    // Pour maintenant, limiter et avertir si dépassement
                    int nb_barrier = courant->barrier.nb_qubits;
                    if (nb_barrier > 3) {
                        fprintf(stderr, "Avertissement: Barrier limité à 3 premiers qubits (dépasse limite IR)\n");
                        nb_barrier = 3;
                    }
                    ir->nb_qubits = nb_barrier;
                    for (int i = 0; i < nb_barrier; i++) {
                        int q = obtenir_qubit_global(ctx, courant->barrier.qubits[i].nom_registre,
                                                     courant->barrier.qubits[i].indice, NULL);
                        if (q >= 0) {
                            ir->qubits[i] = q;
                        }
                    }
                }
                ajouter_instruction(ctx, ir);
                break;
            }
                
            case N_REPEAT: {
                // Dérouler la boucle
                for (int i = 0; i < courant->repeat.repetitions; i++) {
                    if (courant->repeat.bloc) {
                        generer_ir_depuis_ast(courant->repeat.bloc, ctx);
                    }
                }
                break;
            }
                
            case N_PROGRAMME: {
                // Analyser le contenu du programme
                if (courant->premier) {
                    generer_ir_depuis_ast(courant->premier, ctx);
                }
                break;
            }
                
            default:
                fprintf(stderr, "Avertissement: Type de nœud inconnu %d\n", courant->type);
                break;
        }
        courant = courant->suivant;
    }
}

InstructionIR* generer_ir(NoeudAST* ast) {
    if (!ast) {
        fprintf(stderr, "[DEBUG] AST est NULL!\n");
        return NULL;
    }
    
    IRContext ctx = {0};
    ctx.debut = NULL;
    ctx.fin = NULL;
    ctx.nb_qubits = 0;
    ctx.nb_bits = 0;
    ctx.registres = NULL;  // Initialiser table de mapping
    ctx.nb_registres = 0;
    
    // Parcourir l'AST
    generer_ir_depuis_ast(ast, &ctx);
    
    if (!ctx.debut) {
        fprintf(stderr, "[DEBUG] Aucune instruction IR générée!\n");
    }
    
    // Libérer la table de mapping
    liberer_registre_mapping(&ctx);
    
    return ctx.debut;
}

void liberer_ir(InstructionIR* ir) {
    InstructionIR* courant = ir;
    while (courant) {
        InstructionIR* suivant = courant->suivant;
        free(courant);
        courant = suivant;
    }
}

void afficher_ir(InstructionIR* ir) {
    InstructionIR* courant = ir;
    while (courant) {
        printf("[IR] ");
        switch (courant->op) {
            case OP_H: printf("H q[%d]", courant->qubits[0]); break;
            case OP_X: printf("X q[%d]", courant->qubits[0]); break;
            case OP_Y: printf("Y q[%d]", courant->qubits[0]); break;
            case OP_Z: printf("Z q[%d]", courant->qubits[0]); break;
            case OP_S: printf("S q[%d]", courant->qubits[0]); break;
            case OP_T: printf("T q[%d]", courant->qubits[0]); break;
            case OP_RX: printf("RX(%.4f) q[%d]", courant->angle, courant->qubits[0]); break;
            case OP_RY: printf("RY(%.4f) q[%d]", courant->angle, courant->qubits[0]); break;
            case OP_RZ: printf("RZ(%.4f) q[%d]", courant->angle, courant->qubits[0]); break;
            case OP_CX: printf("CX q[%d], q[%d]", courant->qubits[0], courant->qubits[1]); break;
            case OP_CZ: printf("CZ q[%d], q[%d]", courant->qubits[0], courant->qubits[1]); break;
            case OP_SWAP: printf("SWAP q[%d], q[%d]", courant->qubits[0], courant->qubits[1]); break;
            case OP_TOFFOLI: printf("TOFFOLI q[%d], q[%d], q[%d]", courant->qubits[0], courant->qubits[1], courant->qubits[2]); break;
            case OP_MEASURE: printf("MEASURE q[%d] -> c[%d]", courant->qubits[0], courant->bit_classique); break;
            case OP_IF_DEBUT: printf("IF (c[%d] == %d)", courant->condition_bit, courant->condition_val); break;
            case OP_IF_FIN: printf("END IF"); break;
            case OP_BARRIER: printf("BARRIER"); break;
            case OP_PRINT_STATE: printf("PRINT_STATE"); break;
            case OP_PRINT_PROBS: printf("PRINT_PROBS"); break;
            default: printf("UNKNOWN(%d)", courant->op); break;
        }
        printf(" (ligne %d)\n", courant->ligne_source);
        courant = courant->suivant;
    }
}