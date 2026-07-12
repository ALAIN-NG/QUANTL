%{
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "ast.h"
#include "quantl.tab.h"

int ligne_courante = 1;
int col_courante = 0;

void yyerror(const char *msg);
%}

%option noyywrap

%%

"qreg"              { return QREG; }
"creg"              { return CREG; }
"h"|"x"|"y"|"z"|"s"|"t" { yylval.str = strdup(yytext); return PORTE1Q; }
"rx"|"ry"|"rz"      { yylval.str = strdup(yytext); return PORTEROT; }
"cx"|"cz"|"swap"    { yylval.str = strdup(yytext); return PORTE2Q; }
"toffoli"           { return TOFFOLI; }
"measure"           { return MEASURE; }
"if"                { return IF; }
"print"             { return PRINT; }
"barrier"           { return BARRIER; }
"repeat"            { return REPEAT; }
"pi"                { yylval.dval = 3.14159265358979; return FLOTTANT; }

[a-zA-Z_][a-zA-Z0-9_]* { yylval.str = strdup(yytext); return IDENT; }

[0-9]+\.[0-9]+([eE][+-]?[0-9]+)? { yylval.dval = atof(yytext); return FLOTTANT; }
[0-9]+              { yylval.ival = atoi(yytext); return ENTIER; }

"->"                { return FLECHE; }
"=="                { return EGALEGAL; }
"{"                 { return '{'; }
"}"                 { return '}'; }
"["                 { return '['; }
"]"                 { return ']'; }
"("                 { return '('; }
")"                 { return ')'; }
","                 { return ','; }
";"                 { return ';'; }

[ \t\r]+            ;
"\n"                { ligne_courante++; col_courante = 0; }
"//".*              ;

.                   { 
    // Ignorer les caractères Unicode invisibles comme le BOM ou les espaces insécables
    if ((unsigned char)yytext[0] < 128) {
        fprintf(stderr, "Erreur: caractère inattendu '%c' (ASCII %d) à la ligne %d\n", 
                yytext[0], yytext[0], ligne_courante);
        yyerror("Caractère inattendu");
    }
    return yytext[0]; 
}

%%