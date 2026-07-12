#include "codegen_qasm.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void generer_qasm(InstructionIR* ir, char* nom_fichier) {
    FILE* f = fopen(nom_fichier, "w");
    if (!f) {
        fprintf(stderr, "Erreur: impossible d'ouvrir le fichier %s\n", nom_fichier);
        return;
    }
    
    // Compter les qubits et bits classiques
    int nb_qubits = 0;
    int nb_bits = 0;
    int profondeur_if = 0; // pour avertir si une vraie porte se retrouve dans un if
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
    
    // En-tête QASM
    fprintf(f, "OPENQASM 2.0;\n");
    fprintf(f, "include \"qelib1.inc\";\n\n");
    
    // Déclarations
    fprintf(f, "qreg q[%d];\n", nb_qubits);
    fprintf(f, "creg c[%d];\n\n", nb_bits);
    
    // Instructions
    courant = ir;
    while (courant) {
        if (profondeur_if > 0 && courant->op != OP_PRINT_STATE && courant->op != OP_PRINT_PROBS
            && courant->op != OP_IF_DEBUT && courant->op != OP_IF_FIN) {
            fprintf(f, "// ATTENTION : l'instruction suivante etait a l'interieur d'un "
                       "if dans le source QuantL ; elle est exportee ici de maniere "
                       "INCONDITIONNELLE car OpenQASM 2.0 ne supporte pas les conditions "
                       "par bit unique sur un registre classique :\n");
        }
        switch (courant->op) {
            case OP_H:
                fprintf(f, "h q[%d];\n", courant->qubits[0]);
                break;
            case OP_X:
                fprintf(f, "x q[%d];\n", courant->qubits[0]);
                break;
            case OP_Y:
                fprintf(f, "y q[%d];\n", courant->qubits[0]);
                break;
            case OP_Z:
                fprintf(f, "z q[%d];\n", courant->qubits[0]);
                break;
            case OP_S:
                fprintf(f, "s q[%d];\n", courant->qubits[0]);
                break;
            case OP_T:
                fprintf(f, "t q[%d];\n", courant->qubits[0]);
                break;
            case OP_RX:
                fprintf(f, "rx(%.6f) q[%d];\n", courant->angle, courant->qubits[0]);
                break;
            case OP_RY:
                fprintf(f, "ry(%.6f) q[%d];\n", courant->angle, courant->qubits[0]);
                break;
            case OP_RZ:
                fprintf(f, "rz(%.6f) q[%d];\n", courant->angle, courant->qubits[0]);
                break;
            case OP_CX:
                fprintf(f, "cx q[%d], q[%d];\n", courant->qubits[0], courant->qubits[1]);
                break;
            case OP_CZ:
                fprintf(f, "cz q[%d], q[%d];\n", courant->qubits[0], courant->qubits[1]);
                break;
            case OP_SWAP:
                fprintf(f, "swap q[%d], q[%d];\n", courant->qubits[0], courant->qubits[1]);
                break;
            case OP_TOFFOLI:
                fprintf(f, "ccx q[%d], q[%d], q[%d];\n", 
                       courant->qubits[0], courant->qubits[1], courant->qubits[2]);
                break;
            case OP_MEASURE:
                fprintf(f, "measure q[%d] -> c[%d];\n", 
                       courant->qubits[0], courant->bit_classique);
                break;
            case OP_IF_DEBUT:
                // BUGFIX : l'OpenQASM 2.0 réel n'a PAS de bloc `{ }` pour if,
                // et son "if" ne peut comparer qu'un registre classique ENTIER
                // (ex. `if(c==1) x q[0];`), jamais un bit précis comme `c[0]==0`.
                // L'ancien code générait `if (c[0]==0) { ... }`, une syntaxe
                // invalide qui échoue au chargement dans Qiskit ou tout
                // interpréteur OpenQASM 2.0 conforme. QuantL autorise pourtant
                // des conditions par bit (`if (c[0] == val) instr;`), qu'on ne
                // peut pas toujours retraduire fidèlement sans connaître la
                // largeur du registre classique concerné (info non disponible
                // ici). Par sécurité, on documente la condition en commentaire
                // et on n'émet la ou les instructions du bloc que si elles ont
                // un équivalent QASM réel (les autres, comme `print`, sont déjà
                // gérées en commentaire plus bas) — cela garantit un fichier
                // .qasm toujours syntaxiquement valide, quitte à perdre la
                // conditionnalité au niveau du texte QASM généré.
                fprintf(f, "// if (c[%d] == %d) — condition non representable "
                           "telle quelle en OpenQASM 2.0 (voir documentation) :\n",
                       courant->condition_bit, courant->condition_val);
                profondeur_if++;
                break;
            case OP_IF_FIN:
                fprintf(f, "// fin du if\n");
                if (profondeur_if > 0) profondeur_if--;
                break;
            case OP_BARRIER: {
                if (courant->nb_qubits > 0) {
                    fprintf(f, "barrier ");
                    for (int i = 0; i < courant->nb_qubits && i < 3; i++) {
                        fprintf(f, "q[%d]", courant->qubits[i]);
                        if (i < courant->nb_qubits - 1 && i < 2) {
                            fprintf(f, ", ");
                        }
                    }
                    fprintf(f, ";\n");
                } else {
                    fprintf(f, "barrier q;\n");
                }
                break;
            }
            case OP_PRINT_STATE:
            case OP_PRINT_PROBS:
                // Ignoré en QASM (commentaire)
                fprintf(f, "// %s (simulation uniquement)\n", 
                       courant->op == OP_PRINT_STATE ? "print state" : "print probs");
                break;
            default:
                break;
        }
        courant = courant->suivant;
    }
    
    fclose(f);
    printf("Code QASM généré dans %s\n", nom_fichier);
}