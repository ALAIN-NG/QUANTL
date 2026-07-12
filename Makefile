CC = gcc
CFLAGS = -Wall -Wextra -std=c11 -g -O2 -D_GNU_SOURCE
LDFLAGS = -lm
TARGET = qcompile

SRC_DIR = src
BUILD_DIR = build
BIN_DIR = bin

SOURCES = $(SRC_DIR)/main.c \
          $(SRC_DIR)/ast.c \
          $(SRC_DIR)/semantic.c \
          $(SRC_DIR)/ir.c \
          $(SRC_DIR)/sim_engine.c \
          $(SRC_DIR)/codegen_qasm.c

OBJECTS = $(patsubst $(SRC_DIR)/%.c, $(BUILD_DIR)/%.o, $(SOURCES))

LEXER_SRC = $(SRC_DIR)/quantl.l
PARSER_SRC = $(SRC_DIR)/quantl.y
LEXER_OUT = $(SRC_DIR)/quantl.yy.c
PARSER_OUT = $(SRC_DIR)/quantl.tab.c
PARSER_HEADER = $(SRC_DIR)/quantl.tab.h

LEX = flex
YACC = bison
# Enlever -Wno-conflicts-sr pour éviter l'avertissement
YACC_FLAGS = -d -v

.PHONY: all clean distclean

all: $(BIN_DIR)/$(TARGET)

$(BIN_DIR):
	mkdir -p $@

$(BUILD_DIR):
	mkdir -p $@

# Générer l'analyseur syntaxique en premier
$(PARSER_OUT) $(PARSER_HEADER): $(PARSER_SRC)
	$(YACC) $(YACC_FLAGS) -o $@ $<

# Générer l'analyseur lexical
$(LEXER_OUT): $(LEXER_SRC) $(PARSER_HEADER)
	$(LEX) -o $@ $<

# Compiler l'analyseur syntaxique
$(BUILD_DIR)/quantl.tab.o: $(PARSER_OUT) $(PARSER_HEADER)
	$(CC) $(CFLAGS) -c $< -o $@

# Compiler l'analyseur lexical
$(BUILD_DIR)/quantl.yy.o: $(LEXER_OUT) $(PARSER_HEADER)
	$(CC) $(CFLAGS) -c $< -o $@

# Compiler les autres fichiers
$(BUILD_DIR)/%.o: $(SRC_DIR)/%.c
	$(CC) $(CFLAGS) -c $< -o $@

# Lier l'exécutable
$(BIN_DIR)/$(TARGET): $(BIN_DIR) $(BUILD_DIR) $(OBJECTS) $(BUILD_DIR)/quantl.yy.o $(BUILD_DIR)/quantl.tab.o
	$(CC) $(OBJECTS) $(BUILD_DIR)/quantl.yy.o $(BUILD_DIR)/quantl.tab.o -o $@ $(LDFLAGS)
	@echo "Compilation terminée: $(BIN_DIR)/$(TARGET)"

clean:
	rm -rf $(BUILD_DIR) $(BIN_DIR)
	rm -f $(LEXER_OUT) $(PARSER_OUT) $(PARSER_HEADER) $(SRC_DIR)/quantl.output

distclean: clean
	rm -f *.qasm

test: $(BIN_DIR)/$(TARGET)
	@echo "Tests en cours..."
	@echo "  Test Bell:"
	@$(BIN_DIR)/$(TARGET) --source tests/bell.qtl --mode sim --seed 12345
	@echo "  Test GHZ:"
	@$(BIN_DIR)/$(TARGET) --source tests/ghz.qtl --mode sim --seed 12345
	@echo "  Test Deutsch:"
	@$(BIN_DIR)/$(TARGET) --source tests/deutsch.qtl --mode both --seed 12345