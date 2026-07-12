// sim_engine.c - Version complète corrigée
#include "sim_engine.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <complex.h>
#include <time.h>
#include <string.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

Simulateur* sim_initialiser(int nb_qubits, int nb_bits_classiques, int seed) {
    Simulateur* sim = (Simulateur*)calloc(1, sizeof(Simulateur));
    if (!sim) {
        fprintf(stderr, "Erreur d'allocation mémoire\n");
        return NULL;
    }
    
    sim->nb_qubits = nb_qubits;
    sim->nb_bits_classiques = nb_bits_classiques;
    sim->seed = seed;  // Stocker la seed
    int taille_etat = 1 << nb_qubits;
    
    sim->etat = (double complex*)calloc(taille_etat, sizeof(double complex));
    sim->bits_classiques = (int*)calloc(nb_bits_classiques, sizeof(int));
    sim->probabilites = (double*)calloc(taille_etat, sizeof(double));
    sim->mesures_obtenues = (int*)calloc(nb_bits_classiques, sizeof(int));
    
    if (!sim->etat || !sim->bits_classiques || !sim->probabilites || !sim->mesures_obtenues) {
        fprintf(stderr, "Erreur d'allocation mémoire\n");
        sim_liberer(sim);
        return NULL;
    }
    
    sim->etat[0] = 1.0 + 0.0 * I;
    
    // FIX: Appliquer la seed correctement (une seule fois)
    if (seed != 0) {
        srand(seed);
    } else {
        srand(time(NULL));
    }
    
    return sim;
}

void sim_appliquer_porte_1q(Simulateur* sim, int qubit, double complex U[2][2]) {
    int taille = 1 << sim->nb_qubits;
    int pas = 1 << qubit;
    double complex temp[2];
    
    for (int i = 0; i < taille; i++) {
        if ((i & pas) == 0) {
            int j = i | pas;
            temp[0] = sim->etat[i];
            temp[1] = sim->etat[j];
            
            sim->etat[i] = U[0][0] * temp[0] + U[0][1] * temp[1];
            sim->etat[j] = U[1][0] * temp[0] + U[1][1] * temp[1];
        }
    }
}

void sim_appliquer_cx(Simulateur* sim, int controle, int cible) {
    int taille = 1 << sim->nb_qubits;
    int pas_controle = 1 << controle;
    int pas_cible = 1 << cible;
    
    // Parcourir toutes les combinaisons
    for (int i = 0; i < taille; i++) {
        // Si le bit de contrôle est 1
        if (i & pas_controle) {
            // Bit cible actuel
            int bit_cible = (i & pas_cible) ? 1 : 0;
            // État avec le bit cible inversé
            int j = (bit_cible == 0) ? (i | pas_cible) : (i & ~pas_cible);
            
            if (i < j) { // Pour éviter de traiter deux fois la même paire
                double complex tmp = sim->etat[i];
                sim->etat[i] = sim->etat[j];
                sim->etat[j] = tmp;
            }
        }
    }
}

void sim_appliquer_cz(Simulateur* sim, int controle, int cible) {
    int taille = 1 << sim->nb_qubits;
    int pas_controle = 1 << controle;
    int pas_cible = 1 << cible;
    
    for (int i = 0; i < taille; i++) {
        if ((i & pas_controle) && (i & pas_cible)) {
            sim->etat[i] = -sim->etat[i];
        }
    }
}

void sim_appliquer_swap(Simulateur* sim, int q1, int q2) {
    int taille = 1 << sim->nb_qubits;
    int pas1 = 1 << q1;
    int pas2 = 1 << q2;
    
    for (int i = 0; i < taille; i++) {
        if ((i & pas1) == 0 && (i & pas2) == 0) {
            int i1 = i | pas1;
            int i2 = i | pas2;
            
            double complex tmp = sim->etat[i1];
            sim->etat[i1] = sim->etat[i2];
            sim->etat[i2] = tmp;
        }
    }
}

void sim_appliquer_toffoli(Simulateur* sim, int c1, int c2, int cible) {
    int taille = 1 << sim->nb_qubits;
    int pas_c1 = 1 << c1;
    int pas_c2 = 1 << c2;
    int pas_cible = 1 << cible;
    
    for (int i = 0; i < taille; i++) {
        if ((i & pas_c1) && (i & pas_c2) && !(i & pas_cible)) {
            int j = i | pas_cible;
            double complex tmp = sim->etat[i];
            sim->etat[i] = sim->etat[j];
            sim->etat[j] = tmp;
        }
    }
}

void sim_mesure(Simulateur* sim, int qubit, int bit_classique) {
    int taille = 1 << sim->nb_qubits;
    int pas = 1 << qubit;
    double p0 = 0.0;
    
    for (int i = 0; i < taille; i++) {
        if ((i & pas) == 0) {
            double prob = creal(sim->etat[i]) * creal(sim->etat[i]) + 
                         cimag(sim->etat[i]) * cimag(sim->etat[i]);
            p0 += prob;
        }
    }
    
    double r = (double)rand() / RAND_MAX;
    int resultat = (r > p0) ? 1 : 0;
    
    if (bit_classique >= 0 && bit_classique < sim->nb_bits_classiques) {
        sim->bits_classiques[bit_classique] = resultat;
        sim->mesures_obtenues[bit_classique] = resultat;
    }
    
    double norme = 0.0;
    for (int i = 0; i < taille; i++) {
        int bit_qubit = (i & pas) ? 1 : 0;
        if (bit_qubit != resultat) {
            sim->etat[i] = 0.0;
        } else {
            norme += creal(sim->etat[i]) * creal(sim->etat[i]) + 
                    cimag(sim->etat[i]) * cimag(sim->etat[i]);
        }
    }
    
    norme = sqrt(norme);
    if (norme > 1e-15) {
        for (int i = 0; i < taille; i++) {
            if (sim->etat[i] != 0.0) {
                sim->etat[i] /= norme;
            }
        }
    }
}

void sim_appliquer_ir(Simulateur* sim, InstructionIR* ir) {
    if (!sim || !ir) return;
    
    InstructionIR* courant = ir;
    while (courant) {
        switch (courant->op) {
            case OP_H: {
                double complex H[2][2] = {
                    {1/sqrt(2), 1/sqrt(2)},
                    {1/sqrt(2), -1/sqrt(2)}
                };
                sim_appliquer_porte_1q(sim, courant->qubits[0], H);
                break;
            }
            case OP_X: {
                double complex X[2][2] = {{0, 1}, {1, 0}};
                sim_appliquer_porte_1q(sim, courant->qubits[0], X);
                break;
            }
            case OP_Y: {
                double complex Y[2][2] = {{0, -I}, {I, 0}};
                sim_appliquer_porte_1q(sim, courant->qubits[0], Y);
                break;
            }
            case OP_Z: {
                double complex Z[2][2] = {{1, 0}, {0, -1}};
                sim_appliquer_porte_1q(sim, courant->qubits[0], Z);
                break;
            }
            case OP_S: {
                double complex S[2][2] = {{1, 0}, {0, I}};
                sim_appliquer_porte_1q(sim, courant->qubits[0], S);
                break;
            }
            case OP_T: {
                double complex phase = cos(M_PI/4) + I * sin(M_PI/4);
                double complex T[2][2] = {{1, 0}, {0, phase}};
                sim_appliquer_porte_1q(sim, courant->qubits[0], T);
                break;
            }
            case OP_RX: {
                double theta = courant->angle;
                double c = cos(theta/2);
                double s = sin(theta/2);
                double complex RX[2][2] = {{c, -I*s}, {-I*s, c}};
                sim_appliquer_porte_1q(sim, courant->qubits[0], RX);
                break;
            }
            case OP_RY: {
                double theta = courant->angle;
                double c = cos(theta/2);
                double s = sin(theta/2);
                double complex RY[2][2] = {{c, -s}, {s, c}};
                sim_appliquer_porte_1q(sim, courant->qubits[0], RY);
                break;
            }
            case OP_RZ: {
                double theta = courant->angle;
                double phase1 = cos(theta/2) - I * sin(theta/2);
                double phase2 = cos(theta/2) + I * sin(theta/2);
                double complex RZ[2][2] = {{phase1, 0}, {0, phase2}};
                sim_appliquer_porte_1q(sim, courant->qubits[0], RZ);
                break;
            }
            case OP_CX: {
                sim_appliquer_cx(sim, courant->qubits[0], courant->qubits[1]);
                break;
            }
            case OP_CZ: {
                sim_appliquer_cz(sim, courant->qubits[0], courant->qubits[1]);
                break;
            }
            case OP_SWAP: {
                sim_appliquer_swap(sim, courant->qubits[0], courant->qubits[1]);
                break;
            }
            case OP_TOFFOLI: {
                sim_appliquer_toffoli(sim, courant->qubits[0], courant->qubits[1], courant->qubits[2]);
                break;
            }
            case OP_MEASURE: {
                sim_mesure(sim, courant->qubits[0], courant->bit_classique);
                break;
            }
            case OP_IF_DEBUT: {
                if (courant->condition_bit < sim->nb_bits_classiques) {
                    int val = sim->bits_classiques[courant->condition_bit];
                    if (val == courant->condition_val) {
                        courant = courant->suivant;
                        while (courant && courant->op != OP_IF_FIN) {
                            sim_appliquer_ir(sim, courant);
                            courant = courant->suivant;
                        }
                    } else {
                        while (courant && courant->op != OP_IF_FIN) {
                            courant = courant->suivant;
                        }
                    }
                }
                break;
            }
            case OP_IF_FIN: {
                break;
            }
            case OP_BARRIER: {
                break;
            }
            case OP_PRINT_STATE: {
                sim_afficher_etat(sim);
                break;
            }
            case OP_PRINT_PROBS: {
                sim_afficher_probabilites(sim);
                break;
            }
            default: {
                break;
            }
        }
        courant = courant->suivant;
    }
}

void sim_afficher_etat(Simulateur* sim) {
    int taille = 1 << sim->nb_qubits;
    printf("État quantique:\n");
    for (int i = 0; i < taille; i++) {
        double prob = creal(sim->etat[i]) * creal(sim->etat[i]) + 
                     cimag(sim->etat[i]) * cimag(sim->etat[i]);
        if (prob > 1e-10) {
            printf("  |%0*b> : %.6f %+.6fi (probabilité: %.4f)\n", 
                   sim->nb_qubits, i,
                   creal(sim->etat[i]), cimag(sim->etat[i]), prob);
        }
    }
}

void sim_afficher_probabilites(Simulateur* sim) {
    int taille = 1 << sim->nb_qubits;
    printf("Probabilités de mesure:\n");
    for (int i = 0; i < taille; i++) {
        double prob = creal(sim->etat[i]) * creal(sim->etat[i]) + 
                     cimag(sim->etat[i]) * cimag(sim->etat[i]);
        if (prob > 1e-10) {
            printf("  |%0*b> : %.4f\n", sim->nb_qubits, i, prob);
        }
    }
    printf("\nRésultats de mesure: ");
    for (int i = 0; i < sim->nb_bits_classiques; i++) {
        printf("c[%d]=%d ", i, sim->bits_classiques[i]);
    }
    printf("\n");
}

void sim_liberer(Simulateur* sim) {
    if (!sim) return;
    free(sim->etat);
    free(sim->bits_classiques);
    free(sim->probabilites);
    free(sim->mesures_obtenues);
    free(sim);
}