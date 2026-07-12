%{
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "ast.h"

int yylex(void);
void yyerror(const char *msg);

NoeudAST* racine_ast = NULL;
extern int ligne_courante;
%}

%define parse.error verbose

%union {
    int ival;
    double dval;
    char *str;
    NoeudAST *noeud;
}

%token QREG CREG MEASURE IF PRINT BARRIER REPEAT TOFFOLI
%token FLECHE EGALEGAL
%token <str> PORTE1Q PORTE2Q PORTEROT IDENT
%token <ival> ENTIER
%token <dval> FLOTTANT

%type <noeud> programme liste_instructions instruction
%type <noeud> decl_qreg decl_creg instr_porte instr_mesure instr_if instr_print instr_barrier instr_repeat
%type <dval> angle
%type <noeud> liste_ref_qubits

%start programme

%%

programme:
    /* vide */ { racine_ast = NULL; }
    | liste_instructions { racine_ast = $1; }
    ;

liste_instructions:
    instruction { $$ = $1; }
    | liste_instructions instruction {
        if ($1 == NULL) {
            $$ = $2;
        } else {
            NoeudAST* courant = $1;
            while (courant->suivant) {
                courant = courant->suivant;
            }
            courant->suivant = $2;
            $$ = $1;
        }
    }
    ;

instruction:
    decl_qreg
    | decl_creg
    | instr_porte
    | instr_mesure
    | instr_if
    | instr_print
    | instr_barrier
    | instr_repeat
    ;

decl_qreg:
    QREG IDENT '[' ENTIER ']' ';' { 
        $$ = ast_decl_registre(QUANTIQUE, $2, $4, ligne_courante); 
        free($2); // ast_decl_registre() en a fait sa propre copie (strdup)
    }
    ;

decl_creg:
    CREG IDENT '[' ENTIER ']' ';' { 
        $$ = ast_decl_registre(CLASSIQUE, $2, $4, ligne_courante); 
        free($2);
    }
    ;

instr_porte:
    PORTE1Q IDENT '[' ENTIER ']' ';' {
        $$ = ast_porte_1q($1, $2, $4, 0.0, ligne_courante);
        free($1); free($2);
    }
    | PORTE1Q IDENT '[' ENTIER ']' '(' angle ')' ';' {
        $$ = ast_porte_1q($1, $2, $4, $7, ligne_courante);
        free($1); free($2);
    }
    | PORTEROT IDENT '[' ENTIER ']' '(' angle ')' ';' {
        $$ = ast_porte_1q($1, $2, $4, $7, ligne_courante);
        free($1); free($2);
    }
    | PORTE2Q IDENT '[' ENTIER ']' ',' IDENT '[' ENTIER ']' ';' {
        $$ = ast_porte_2q($1, $2, $4, $7, $9, ligne_courante);
        free($1); free($2); free($7);
    }
    | TOFFOLI IDENT '[' ENTIER ']' ',' IDENT '[' ENTIER ']' ',' IDENT '[' ENTIER ']' ';' {
        $$ = ast_porte_toffoli($2, $4, $7, $9, $12, $14, ligne_courante);
        free($2); free($7); free($12);
    }
    ;

instr_mesure:
    MEASURE IDENT '[' ENTIER ']' FLECHE IDENT '[' ENTIER ']' ';' {
        $$ = ast_mesure($2, $4, $7, $9, ligne_courante);
        free($2); free($7);
    }
    ;

instr_if:
    IF '(' IDENT '[' ENTIER ']' EGALEGAL ENTIER ')' instruction {
        $$ = ast_if($3, $5, $8, $10, ligne_courante);
        free($3);
    }
    ;

instr_print:
    PRINT IDENT ';' {
        // BUGFIX : le lexer ne produit jamais de tokens littéraux "state"/"probs"
        // (il retourne toujours IDENT pour ce texte), donc les anciennes règles
        // `PRINT "state" ';'` et `PRINT "probs" ';'` n'étaient JAMAIS atteintes :
        // tout "print state;" ou "print probs;" retombait silencieusement sur
        // cette règle générique, qui appelait systématiquement ast_print_probs().
        // Résultat : "print state;" (utilisé par ex. dans deutsch.qtl) ne
        // produisait jamais l'affichage du vecteur d'état complet.
        // On distingue maintenant explicitement les deux mots-clés.
        if (strcmp($2, "state") == 0) {
            $$ = ast_print_state(ligne_courante);
        } else if (strcmp($2, "probs") == 0) {
            $$ = ast_print_probs(ligne_courante);
        } else {
            fprintf(stderr,
                "Erreur sémantique (ligne %d) : argument invalide pour 'print' : '%s' "
                "(attendu 'state' ou 'probs').\n",
                ligne_courante, $2);
            $$ = ast_print_probs(ligne_courante);
        }
        free($2);
    }
    ;

instr_barrier:
    BARRIER ';' { $$ = ast_barrier(NULL, 0, ligne_courante); }
    | BARRIER liste_ref_qubits ';' { $$ = $2; }
    ;

// Liste de références de qubits pour BARRIER
liste_ref_qubits:
    IDENT '[' ENTIER ']' {
        Reference* refs = (Reference*)malloc(sizeof(Reference));
        if (refs) {
            // BUGFIX (fuite mémoire) : $1 est déjà une chaîne allouée par le
            // lexer (strdup dans quantl.l) ; un strdup() supplémentaire ici
            // dupliquait inutilement la chaîne et perdait le pointeur original.
            // On prend directement possession de la chaîne du lexer.
            refs[0].nom_registre = $1;
            refs[0].indice = $3;
        } else {
            free($1);
        }
        $$ = ast_barrier(refs, 1, ligne_courante);
    }
    | liste_ref_qubits ',' IDENT '[' ENTIER ']' {
        // $1 est un noeud BARRIER existant
        NoeudAST* barrier_node = $1;
        if (barrier_node && barrier_node->type == N_BARRIER) {
            int new_nb = barrier_node->barrier.nb_qubits + 1;
            Reference* new_refs = (Reference*)realloc(barrier_node->barrier.qubits, new_nb * sizeof(Reference));
            if (new_refs) {
                barrier_node->barrier.qubits = new_refs;
                // BUGFIX (fuite mémoire) : idem, $3 est déjà alloué par le lexer.
                barrier_node->barrier.qubits[new_nb - 1].nom_registre = $3;  // $3 est IDENT
                barrier_node->barrier.qubits[new_nb - 1].indice = $5;        // $5 est ENTIER
                barrier_node->barrier.nb_qubits = new_nb;
            } else {
                free($3);
            }
        }
        $$ = barrier_node;
    }
    ;

instr_repeat:
    REPEAT '(' ENTIER ')' '{' liste_instructions '}' {
        $$ = ast_repeat($3, $6, ligne_courante);
    }
    ;

angle:
    FLOTTANT { $$ = $1; }
    | ENTIER { $$ = (double)$1; }
    ;

%%