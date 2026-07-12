#include "semantic.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

#define MAX_QUBITS 20

// Table des symboles
typedef struct Symbole {
    char* nom;
    TypeRegistre type;
    int taille;
    int ligne_decl;
    bool* mesure;  // Pour les bits classiques: true si mesuré
    struct Symbole* suivant;
} Symbole;

Symbole* table_symboles = NULL;
int nb_qubits_total = 0;
bool erreur_semantique = false;

// Prototypes des fonctions internes
Symbole* trouver_symbole(char* nom);
void ajouter_symbole(char* nom, TypeRegistre type, int taille, int ligne);
bool verifier_reference(char* nom_reg, int indice, int ligne);
void marquer_mesure(char* nom_reg, int indice);
bool bit_est_mesure(char* nom_reg, int indice);
void analyser_noeud(NoeudAST* noeud);
bool est_porte_rotation(char* nom);
bool est_porte_1q_sans_angle(char* nom);

Symbole* trouver_symbole(char* nom) {
    Symbole* s = table_symboles;
    while (s) {
        if (strcmp(s->nom, nom) == 0) return s;
        s = s->suivant;
    }
    return NULL;
}

void ajouter_symbole(char* nom, TypeRegistre type, int taille, int ligne) {
    if (trouver_symbole(nom)) {
        fprintf(stderr, "Erreur sémantique (ligne %d) : Registre '%s' déjà déclaré.\n", ligne, nom);
        erreur_semantique = true;
        return;
    }
    
    Symbole* s = (Symbole*)malloc(sizeof(Symbole));
    s->nom = strdup(nom);
    s->type = type;
    s->taille = taille;
    s->ligne_decl = ligne;
    s->mesure = NULL;
    
    if (type == CLASSIQUE) {
        s->mesure = (bool*)calloc(taille, sizeof(bool));
    }
    
    s->suivant = table_symboles;
    table_symboles = s;
    
    if (type == QUANTIQUE) {
        nb_qubits_total += taille;
        if (nb_qubits_total > MAX_QUBITS) {
            fprintf(stderr, "Avertissement (ligne %d) : Nombre total de qubits (%d) dépasse la limite (%d).\n",
                    ligne, nb_qubits_total, MAX_QUBITS);
        }
    }
}

bool verifier_reference(char* nom_reg, int indice, int ligne) {
    Symbole* s = trouver_symbole(nom_reg);
    if (!s) {
        fprintf(stderr, "Erreur sémantique (ligne %d) : Registre inconnu '%s'.\n", ligne, nom_reg);
        erreur_semantique = true;
        return false;
    }
    if (indice < 0 || indice >= s->taille) {
        fprintf(stderr, "Erreur sémantique (ligne %d) : Indice %d hors bornes pour le registre '%s' (taille %d).\n",
                ligne, indice, nom_reg, s->taille);
        erreur_semantique = true;
        return false;
    }
    return true;
}

void marquer_mesure(char* nom_reg, int indice) {
    Symbole* s = trouver_symbole(nom_reg);
    if (s && s->type == CLASSIQUE) {
        s->mesure[indice] = true;
    }
}

bool bit_est_mesure(char* nom_reg, int indice) {
    Symbole* s = trouver_symbole(nom_reg);
    if (s && s->type == CLASSIQUE) {
        return s->mesure[indice];
    }
    return false;
}

bool est_porte_rotation(char* nom) {
    return (strcmp(nom, "rx") == 0 || strcmp(nom, "ry") == 0 || strcmp(nom, "rz") == 0);
}

bool est_porte_1q_sans_angle(char* nom) {
    return (strcmp(nom, "h") == 0 || strcmp(nom, "x") == 0 || 
            strcmp(nom, "y") == 0 || strcmp(nom, "z") == 0 ||
            strcmp(nom, "s") == 0 || strcmp(nom, "t") == 0);
}

void analyser_noeud(NoeudAST* noeud) {
    if (!noeud) return;
    
    // Parcourir la liste chaînée (toutes les instructions sont connectées via suivant)
    NoeudAST* courant = noeud;
    while (courant) {
        switch (courant->type) {
            case N_DECL_QREG:
                ajouter_symbole(courant->decl.nom_registre, QUANTIQUE, 
                              courant->decl.taille, courant->ligne);
                break;
                
            case N_DECL_CREG:
                ajouter_symbole(courant->decl.nom_registre, CLASSIQUE,
                              courant->decl.taille, courant->ligne);
                break;
                
            case N_PORTE_1Q: {
                // Vérifier que le registre existe
                if (verifier_reference(courant->porte_1q.nom_reg, 
                                      courant->porte_1q.indice_qubit, courant->ligne)) {
                    Symbole* s = trouver_symbole(courant->porte_1q.nom_reg);
                    if (s && s->type != QUANTIQUE) {
                        fprintf(stderr, "Erreur sémantique (ligne %d) : Porte quantique sur registre classique '%s'.\n",
                                courant->ligne, courant->porte_1q.nom_reg);
                        erreur_semantique = true;
                    }
                }
                
                // Vérifier la présence d'angle
                char* nom = courant->porte_1q.nom_porte;
                if (est_porte_rotation(nom) && !courant->porte_1q.a_angle) {
                    fprintf(stderr, "Erreur sémantique (ligne %d) : Angle manquant pour la porte %s.\n",
                            courant->ligne, nom);
                    erreur_semantique = true;
                }
                if (est_porte_1q_sans_angle(nom) && courant->porte_1q.a_angle) {
                    fprintf(stderr, "Avertissement (ligne %d) : Porte %s ne prend pas d'angle.\n",
                            courant->ligne, nom);
                }
                break;
            }
                
            case N_PORTE_2Q: {
                // Vérifier que les registres existent
                bool ok1 = verifier_reference(courant->porte_2q.nom_reg1, 
                                             courant->porte_2q.indice1, courant->ligne);
                bool ok2 = verifier_reference(courant->porte_2q.nom_reg2,
                                             courant->porte_2q.indice2, courant->ligne);
                
                if (ok1 && ok2) {
                    Symbole* s1 = trouver_symbole(courant->porte_2q.nom_reg1);
                    Symbole* s2 = trouver_symbole(courant->porte_2q.nom_reg2);
                    if (s1 && s1->type != QUANTIQUE) {
                        fprintf(stderr, "Erreur sémantique (ligne %d) : Porte quantique sur registre classique '%s'.\n",
                                courant->ligne, courant->porte_2q.nom_reg1);
                        erreur_semantique = true;
                    }
                    if (s2 && s2->type != QUANTIQUE) {
                        fprintf(stderr, "Erreur sémantique (ligne %d) : Porte quantique sur registre classique '%s'.\n",
                                courant->ligne, courant->porte_2q.nom_reg2);
                        erreur_semantique = true;
                    }
                }
                
                // Vérifier que les qubits sont distincts
                if (ok1 && ok2 && 
                    strcmp(courant->porte_2q.nom_reg1, courant->porte_2q.nom_reg2) == 0 &&
                    courant->porte_2q.indice1 == courant->porte_2q.indice2) {
                    fprintf(stderr, "Erreur sémantique (ligne %d) : Contrôle et cible identiques.\n",
                            courant->ligne);
                    erreur_semantique = true;
                }
                break;
            }
                
            case N_PORTE_TOFFOLI: {
                // Vérifier les 3 qubits
                bool ok1 = verifier_reference(courant->porte_toffoli.nom_reg1,
                                             courant->porte_toffoli.indice1, courant->ligne);
                bool ok2 = verifier_reference(courant->porte_toffoli.nom_reg2,
                                             courant->porte_toffoli.indice2, courant->ligne);
                bool ok3 = verifier_reference(courant->porte_toffoli.nom_reg3,
                                             courant->porte_toffoli.indice3, courant->ligne);
                
                // Vérifier que tous les qubits sont distincts
                if (ok1 && ok2 && ok3) {
                    // Vérification simplifiée
                    if (strcmp(courant->porte_toffoli.nom_reg1, courant->porte_toffoli.nom_reg2) == 0 &&
                        courant->porte_toffoli.indice1 == courant->porte_toffoli.indice2) {
                        fprintf(stderr, "Erreur sémantique (ligne %d) : Qubits identiques dans Toffoli.\n",
                                courant->ligne);
                        erreur_semantique = true;
                    }
                }
                break;
            }
                
            case N_MESURE: {
                // Vérifier le qubit
                if (verifier_reference(courant->mesure.nom_reg_qubit,
                                      courant->mesure.indice_qubit, courant->ligne)) {
                    Symbole* s = trouver_symbole(courant->mesure.nom_reg_qubit);
                    if (s && s->type != QUANTIQUE) {
                        fprintf(stderr, "Erreur sémantique (ligne %d) : Mesure sur un registre classique.\n",
                                courant->ligne);
                        erreur_semantique = true;
                    }
                }
                
                // Vérifier le bit classique
                if (verifier_reference(courant->mesure.nom_reg_bit,
                                      courant->mesure.indice_bit, courant->ligne)) {
                    Symbole* s = trouver_symbole(courant->mesure.nom_reg_bit);
                    if (s && s->type != CLASSIQUE) {
                        fprintf(stderr, "Erreur sémantique (ligne %d) : Mesure vers un registre quantique.\n",
                                courant->ligne);
                        erreur_semantique = true;
                    } else if (s) {
                        marquer_mesure(courant->mesure.nom_reg_bit, courant->mesure.indice_bit);
                    }
                }
                break;
            }
                
            case N_IF: {
                // Vérifier le bit classique
                if (verifier_reference(courant->if_instr.nom_reg_bit,
                                      courant->if_instr.indice_bit, courant->ligne)) {
                    Symbole* s = trouver_symbole(courant->if_instr.nom_reg_bit);
                    if (s && s->type != CLASSIQUE) {
                        fprintf(stderr, "Erreur sémantique (ligne %d) : Condition sur un registre quantique.\n",
                                courant->ligne);
                        erreur_semantique = true;
                    } else if (s && !bit_est_mesure(courant->if_instr.nom_reg_bit, 
                                                   courant->if_instr.indice_bit)) {
                        fprintf(stderr, "Avertissement (ligne %d) : Bit classique '%s[%d]' non mesuré avant le if.\n",
                                courant->ligne, courant->if_instr.nom_reg_bit, courant->if_instr.indice_bit);
                    }
                }
                
                // Analyser l'instruction dans le if
                if (courant->if_instr.instruction) {
                    analyser_noeud(courant->if_instr.instruction);
                }
                break;
            }
                
            case N_PRINT:
                // Rien à vérifier
                break;
                
            case N_BARRIER:
                // Vérifier les qubits
                for (int i = 0; i < courant->barrier.nb_qubits; i++) {
                    Reference* ref = &courant->barrier.qubits[i];
                    verifier_reference(ref->nom_registre, ref->indice, courant->ligne);
                }
                break;
                
            case N_REPEAT:
                // Analyser le bloc
                if (courant->repeat.bloc) {
                    analyser_noeud(courant->repeat.bloc);
                }
                break;
                
            case N_PROGRAMME:
                // Analyser le contenu du programme
                if (courant->premier) {
                    analyser_noeud(courant->premier);
                }
                break;
                
            default:
                fprintf(stderr, "Avertissement: Type de nœud inconnu %d\n", courant->type);
                break;
        }
        courant = courant->suivant;
    }
}

int analyser_semantique(NoeudAST* racine) {
    table_symboles = NULL;
    nb_qubits_total = 0;
    erreur_semantique = false;
    
    // Premier parcours: collecter les déclarations et vérifier les références
    analyser_noeud(racine);
    
    // Libérer la table des symboles
    Symbole* courant = table_symboles;
    while (courant) {
        Symbole* suivant = courant->suivant;
        free(courant->nom);
        if (courant->mesure) {
            free(courant->mesure);
        }
        free(courant);
        courant = suivant;
    }
    table_symboles = NULL;
    
    return erreur_semantique ? 1 : 0;
}