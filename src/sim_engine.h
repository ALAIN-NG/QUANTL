#ifndef SIM_ENGINE_H
#define SIM_ENGINE_H

#include <complex.h>
#include "ir.h"

typedef struct {
    double complex* etat;
    int nb_qubits;
    int* bits_classiques;
    int nb_bits_classiques;
    double* probabilites;
    int* mesures_obtenues;
    int seed;  // FIX: Seed aléatoire pour déterminisme
} Simulateur;

// Prototypes
Simulateur* sim_initialiser(int nb_qubits, int nb_bits_classiques, int seed);  // FIX: Ajouter seed
void sim_appliquer_ir(Simulateur* sim, InstructionIR* ir);
void sim_mesure(Simulateur* sim, int qubit, int bit_classique);
void sim_afficher_etat(Simulateur* sim);
void sim_afficher_probabilites(Simulateur* sim);
void sim_liberer(Simulateur* sim);

#endif