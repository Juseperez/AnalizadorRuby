import ply.yacc as yacc
from lexico import tokens
import os
import datetime

# -----------------------------
# PRECEDENCIA (por si usas expr)
# -----------------------------
precedence = (
    ('left', 'OROR', 'OR'),
    ('left', 'ANDAND', 'AND'),
    ('left', 'EQ', 'NE', 'EQQ', 'MATCH', 'NMATCH', 'LT', 'LE', 'GT', 'GE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'MULT', 'DIV', 'MOD'),
    ('right', 'POWER'),
    ('right', 'UMINUS'),
)


errores_sintacticos = []
# Lo comente porque me daba error cuando queria probar el algoritmo4
#def p_expresion_suma(p):
#    'expresion : valor PLUS valor'
#    print("Reconocida una suma válida:", p[1], "+", p[3])
#    p[0] = p[1] + p[3] if isinstance(p[1], (int, float)) and isinstance(p[3], (int, float)) else None

# --------------------------------------------------
# NODO INICIAL - Inicio del Avance Elaborado por BrayanBriones
# --------------------------------------------------
def p_program(p):
    'program : statement_list'
    p[0] = ('program', p[1])

def p_statement_list_multi(p):
    'statement_list : statement_list statement'
    p[0] = p[1] + [p[2]]

def p_statement_list_single(p):
    'statement_list : statement'
    p[0] = [p[1]]

def p_stmt_block_single(p):
    'stmt_block : statement'
    # Representamos bloque como lista de sentencias
    p[0] = [p[1]]

def p_stmt_block_multi(p):
    'stmt_block : LBRACE statement_list RBRACE'
    # Si usas llaves para agrupar bloques
    p[0] = p[2]

def p_stmt_block_list(p):
    'stmt_block : statement_list'
    p[0] = p[1]
# --------------------------------------------------
# STATEMENTS ASIGNADOS
# --------------------------------------------------
def p_statement(p):
    '''statement : print_stmt
                 | input_stmt
                 | assignment
                 | while_stmt
                 | for_stmt
                 | hash_literal
                 | function_def
                 | if_stmt
                 | stmt_block
                 | expression'''
    p[0] = p[1]

# --------------------------------------------------
# IMPRESIÓN (print / puts expr)
# --------------------------------------------------
def p_print_stmt(p):
    '''print_stmt : PRINT expression
                  | PUTS expression'''
    # ('print', 'print', nodo_expr) o ('print', 'puts', nodo_expr)
    p[0] = ('print', p[1], p[2])

# --------------------------------------------------
# INGRESO DE DATOS POR TECLADO
# patrón típico: nombre = gets
# --------------------------------------------------
def p_input_stmt(p):
    'input_stmt : variable EQLS LOCAL_VAR'
    # ('input', ('var', nombre), 'gets')
    p[0] = ('input', p[1], p[3])

# --------------------------------------------------
# VARIABLES Y ASIGNACIÓN (todos los pertenecientes al analizador lexico)
# --------------------------------------------------
def p_variable(p):
    '''variable : GLOBAL_VAR
                | LOCAL_VAR
                | INSTANCE_VAR
                | CLASS_VAR
                | CONSTANT'''
    p[0] = ('var', p[1])

def p_assignment(p):
    '''assignment : variable EQLS expression
                  | variable PLUSEQLS expression
                  | variable MINUSEQLS expression
                  | variable MULTEQLS expression
                  | variable DIVEQLS expression
                  | variable MODEQLS expression
                  | variable POWEREQLS expression'''
    # ('assign', ('var', x), '=', expr)
    p[0] = ('assign', p[1], p[2], p[3])

# --------------------------------------------------
# ESTRUCTURA DE CONTROL: while ... end
# while <cond> do ... end  o  while <cond> ... end
# --------------------------------------------------
def p_while_stmt(p):
    '''while_stmt : WHILE expression_logic DO statement_list END_S
                  | WHILE expression_logic statement_list END_S'''
    if len(p) == 6:
        # while cond do stmts end
        p[0] = ('while', p[2], p[4])
    else:
        # while cond stmts end
        p[0] = ('while', p[2], p[3])

# --------------------------------------------------
# Jusepere ESTRUCTURA DE CONTROL: for ... in ... do ... end
# --------------------------------------------------
def p_for_stmt(p):
    '''for_stmt : FOR LOCAL_VAR IN expression DO statement_list END_S
                | FOR LOCAL_VAR IN expression statement_list END_S'''
    if len(p) == 7:
        # for i in expr do stmts end
        p[0] = ('for', p[2], p[4], p[6])
    else:
        # for i in expr stmts end
        p[0] = ('for', p[2], p[4], p[5])

#elias rubio
def p_if_stmt_basic(p):
    'if_stmt : IF expression stmt_block END_S'
    p[0] = ('if', p[2], p[3], [], None)

def p_if_stmt_else(p):
    'if_stmt : IF expression stmt_block ELSE stmt_block END_S'
    p[0] = ('if', p[2], p[3], [], ('else', p[5]))

def p_if_stmt_elsif(p):
    'if_stmt : IF expression stmt_block elsif_list END_S'
    p[0] = ('if', p[2], p[3], p[4], None)

def p_if_stmt_elsif_else(p):
    'if_stmt : IF expression stmt_block elsif_list ELSE stmt_block END_S'
    p[0] = ('if', p[2], p[3], p[4], ('else', p[6]))

# --------------------------------------------------
# Lista de ELSIF: right-recursive, 
# Cada elemento: ('elsif', condicion, bloque)
# --------------------------------------------------
def p_elsif_list_single(p):
    'elsif_list : ELSIF expression stmt_block'
    p[0] = [('elsif', p[2], p[3])]

def p_elsif_list_more(p):
    'elsif_list : ELSIF expression stmt_block elsif_list'
    # colocamos el primero al inicio de la lista
    p[0] = [('elsif', p[2], p[3])] + p[5]

# --------------------------------------------------
# else_block 
# --------------------------------------------------
def p_else_block(p):
    'else_block : ELSE stmt_block'
    p[0] = ('else', p[2])
# --------------------------------------------------
# EXPRESIONES LÓGICAS / DE COMPARACIÓN
# --------------------------------------------------
def p_expression_logic_chain(p):
    '''expression_logic : expression_logic ANDAND expression_logic
                        | expression_logic OROR expression_logic
                        | expression_logic AND expression_logic
                        | expression_logic OR expression_logic'''
    p[0] = ('logic', p[2], p[1], p[3])

def p_expression_logic_simple(p):
    'expression_logic : expression_compare'
    p[0] = p[1]

def p_expression_compare(p):
    '''expression_compare : expression LT expression
                          | expression LE expression
                          | expression GT expression
                          | expression GE expression
                          | expression EQ expression
                          | expression NE expression
                          | expression EQQ expression
                          | expression MATCH expression
                          | expression NMATCH expression'''
    p[0] = ('cmp', p[2], p[1], p[3])


def p_expression_not(p):
    'expression : NOT expression'
    # ('not', expr)
    p[0] = ('not', p[2])


# --------------------------------------------------
# ESTRUCTURA DE DATOS: HASH
# Soporta: { key => value, ... }  y  { key: value, ... }
# --------------------------------------------------
def p_hash_literal(p):
    'hash_literal : LBRACE hash_pairs_opt RBRACE'
    # ('hash', [ ('pair', key, val), ... ])
    p[0] = ('hash', p[2])

def p_hash_pairs_opt_empty(p):
    'hash_pairs_opt : '
    p[0] = []

def p_hash_pairs_opt_list(p):
    'hash_pairs_opt : hash_pairs'
    p[0] = p[1]

def p_hash_pairs_multi(p):
    'hash_pairs : hash_pairs COMMA hash_pair'
    p[0] = p[1] + [p[3]]

def p_hash_pairs_one(p):
    'hash_pairs : hash_pair'
    p[0] = [p[1]]

def p_hash_pair_arrow(p):
    'hash_pair : expression ARROW expression'
    # { expr => expr }
    p[0] = ('pair', p[1], p[3])

def p_hash_pair_symbolstyle(p):
    'hash_pair : SYMBOL COLON expression'
    # { :sym: expr } o { nombre: expr }
    p[0] = ('pair', p[1], p[3])

def p_hash_pair_keywordstyle(p):
    'hash_pair : LOCAL_VAR COLON expression'
    p[0] = ('pair', p[1], p[3])

def p_expression_hash(p):
    'expression : hash_literal'
    p[0] = p[1]

# --------------------------------------------------
# Jusepere: ESTRUCTURA DE DATOS: range (1..10 o 1...10)
# --------------------------------------------------
def p_expression_range(p):
    '''expression : expression RANGE_INCL expression
                  | expression RANGE_EXCL expression'''
    p[0] = ('range', p[2], p[1], p[3])

#-------------------------
#array emrubio
#--------------------------
# 1) Lista de expresiones (para separar elementos del array) — right-recursive
def p_expr_list_single(p):
    'expr_list : expression'
    p[0] = [p[1]]

def p_expr_list_more(p):
    'expr_list : expression COMMA expr_list'
    p[0] = [p[1]] + p[3]

# 2) Array literal: vacío o con elementos
def p_array_literal_empty(p):
    'array_literal : LBRACKET RBRACKET'
    p[0] = ('array', [])

def p_array_literal_elems(p):
    'array_literal : LBRACKET expr_list RBRACKET'
    p[0] = ('array', p[2])

# 3) Primary (núcleo) — incluimos array_literal como primitivo
def p_primary(p):
    '''primary : INTEGER
               | FLOAT
               | STR
               | SYMBOL
               | LOCAL_VAR
               | GLOBAL_VAR
               | INSTANCE_VAR
               | CLASS_VAR
               | CONSTANT
               | TRUE
               | FALSE
               | NIL
               | LPAREN expression RPAREN
               | array_literal'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        # caso LPAREN expression RPAREN
        p[0] = p[2]

# 4) Postfix: permite indexado repetido (ej: a[0][1])
#    Usamos left-recursion para encadenar índices: expr_postfix -> expr_postfix [ expr ]
def p_expr_postfix_index(p):
    'expr_postfix : expr_postfix LBRACKET expression RBRACKET'
    # ('index', base_expr, index_expr)
    p[0] = ('index', p[1], p[3])

def p_expr_postfix_primary(p):
    'expr_postfix : primary'
    p[0] = p[1]

# 5) Conectar postfix con expr_arith 
def p_expr_arith_postfix(p):
    'expr_arith : expr_postfix'
    p[0] = p[1]

def p_assignment_index(p):
    'assignment : expr_postfix EQLS expression'
    # ('array_assign', left_index_expr, value)
    # left_index_expr puede ser ('index', base, idx) o un índice anidado ('index', ('index', base, i0), i1)
    p[0] = ('array_assign', p[1], p[3])

# --------------------------------------------------
# TIPO DE FUNCIÓN: SIN RETORNO EXPLÍCITO
# Ruby ya es así: def nombre ... end
# --------------------------------------------------
def p_function_def(p):
    '''function_def : DEF LOCAL_VAR statement_list END_S
                    | DEF LOCAL_VAR LPAREN param_list RPAREN statement_list END_S'''
    if len(p) == 5:
        # def foo ... end
        p[0] = ('def', p[2], [], p[3])
    else:
        # def foo(a, b) ... end
        p[0] = ('def', p[2], p[4], p[6])

#Jusepere Parámetros opcionales
def p_optional_params(p):
    '''optional_params : param_list
                       | empty'''
    p[0] = p[1]

def p_param_list(p):
    '''param_list : parameter
                  | param_list COMMA parameter'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_parameter(p):
    '''parameter : LOCAL_VAR
                 | LOCAL_VAR EQLS expression'''
    if len(p) == 2:
        p[0] = (p[1], None)
    else:
        p[0] = (p[1], p[3])

def p_empty(p):
    'empty :'
    p[0] = None
# Elias Rubio
# --------------------------------------------------
# RETORNO (return expr)
# --------------------------------------------------
def p_return_stmt(p):
    '''statement : RETURN
                 | RETURN expression'''
    if len(p) == 2:
        # return sin valor
        p[0] = ('return', None)
    else:
        # return con expresión
        p[0] = ('return', p[2])

# class_def admite:
#  - class Nombre ... end
#  - class Nombre < Padre ... end
# El cuerpo de la clase es un stmt_block 
def p_class_def(p):
    '''class_def : CLASS CONSTANT stmt_block END_S
                 | CLASS CONSTANT opt_inherit stmt_block END_S'''
    # ('class', class_name, parent_or_None, body_list)
    if len(p) == 5:
        # class C <--- p[2] es CONSTANT, p[3] es stmt_block, p[4] es END_S
        p[0] = ('class', p[2], None, p[3])
    else:
        # class C < Parent ... end
        p[0] = ('class', p[2], p[3], p[5])

# opt_inherit: opcionalmente ' < CONSTANT ' (herencia simple)
def p_opt_inherit(p):
    '''opt_inherit : LT CONSTANT
                   | empty'''
    if len(p) == 3:
        p[0] = p[2]
    else:
        p[0] = None


def p_statement_class(p):
    'statement : class_def'
    p[0] = p[1]

# --------------------------------------------------
# PROPIEDADES (variables de instancia / de clase)
# --------------------------------------------------
# En Ruby, normalmente dentro de la clase se usan assignments como:
#   @name = "Elías"

def p_property_decl(p):
    '''property_decl : INSTANCE_VAR
                     | CLASS_VAR'''
    # ('prop', tipo, nombre_lexema)
    p[0] = ('prop', p[1])

# permitimos que property_decl sea un statement dentro de la clase (opcional)
def p_statement_property(p):
    'statement : property_decl'
    p[0] = p[1]

# --------------------------------------------------
# MÉTODOS
# --------------------------------------------------

def p_method_from_def(p):
    'method_def : function_def'
    node = p[1]
    if isinstance(node, tuple) and node and node[0] == 'def':
        _, name, params, body = node
        p[0] = ('method', name, params, body)
    else:
        p[0] = node

# Permitimos que method_def sea una statement 
def p_statement_method(p):
    'statement : method_def'
    p[0] = p[1]
#--------------------------------------------------
# EXPRESIONES (números, strings, vars, operaciones)
# --------------------------------------------------
def p_expression_binop(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression MULT expression
                  | expression DIV expression
                  | expression MOD expression
                  | expression POWER expression'''
    p[0] = ('binop', p[2], p[1], p[3])

def p_expression_group(p):
    'expression : LPAREN expression RPAREN'
    p[0] = p[2]

def p_expression_number(p):
    '''expression : INTEGER
                  | FLOAT
                  | RATIONAL
                  | COMPLEX'''
    p[0] = ('num', p[1])

def p_expression_literal(p):
    '''expression : STR
                  | SYMBOL
                  | REGEXP'''
    p[0] = ('lit', p[1])

def p_expression_variable(p):
    'expression : variable'
    p[0] = p[1]

def p_expression_uminus(p):
    '''expression : MINUS expression %prec UMINUS'''
    p[0] = ('uminus', p[2])

def p_valor_numero(p):
    'valor : INTEGER'
    p[0] = p[1]

def p_valor_variable(p):
    'valor : LOCAL_VAR'
    p[0] = p[1]

def p_error(p):
    if p:
        mensaje = f"Error de sintaxis con el token '{p.value}' en la línea {p.lineno}"
    else:
        mensaje = "Error de sintaxis al final de la entrada"
    print(mensaje)
    errores_sintacticos.append(mensaje)

# Build the parser
parser = yacc.yacc()

def analizar_sintaxis(nombre_archivo, usuario):
    global errores_sintacticos
    errores_sintacticos = []  # reiniciar errores cada análisis

    # Crear carpetas si no existen
    os.makedirs("algoritmos", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    ruta_archivo = os.path.join("algoritmos", nombre_archivo)

    # Leer archivo Ruby
    try:
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            data = f.read()
    except FileNotFoundError:
        print(f"[ERROR] No se encontró el archivo: {ruta_archivo}")
        return

    print(f"Analizando sintaxis de: {ruta_archivo}")
    parser.parse(data)

    # Crear log
    ahora = datetime.datetime.now().strftime("%d%m%Y-%Hh%M")
    nombre_log = f"sintactico-{usuario}-{ahora}.txt"
    ruta_log = os.path.join("logs", nombre_log)

    with open(ruta_log, "w", encoding="utf-8") as log:
        log.write(f"LOG de análisis sintáctico: {ruta_archivo}\n")
        log.write(f"Usuario: {usuario}\n")
        log.write(f"Fecha y hora: {ahora}\n")
        log.write("=" * 50 + "\n")

        if errores_sintacticos:
            log.write("Errores sintácticos encontrados:\n")
            for e in errores_sintacticos:
                log.write(f"- {e}\n")
        else:
            log.write("Sin errores sintácticos.\n")

    print(f"Log generado en: {ruta_log}")

# -------------------------------------------------
# Ejecución principal con selección de usuario/archivo
# -------------------------------------------------
if __name__ == "__main__":
    print("Seleccione el algoritmo a analizar:")
    print("1 - algoritmo1E.rb (emrubio85)")
    print("2 - algoritmo2B.rb (BrayanBriones)")
    print("3 - algoritmo3J.rb (Juseperez)")
    print("4 - algoritmo4B.rb (BrayanBriones)")
    print("5 - algoritmo5J.rb (Juseperez)")
    print("6 - algoritmo6E.rb (Emrubio85) ")
    opcion = input("Ingrese su opción: ").strip()

    if opcion == "1":
        analizar_sintaxis("algoritmo1E.rb", "emrubio85")
    elif opcion == "2":
        analizar_sintaxis("algoritmo2B.rb", "BrayanBriones")
    elif opcion == "3":
        analizar_sintaxis("algoritmo3J.rb", "Juseperez")
    elif opcion == "4":
        analizar_sintaxis("algoritmo4B.rb", "BrayanBriones")
    elif opcion == "5":
        analizar_sintaxis("algoritmo5J.rb", "Juseperez")
    elif opcion == "6":
        analizar_sintaxis("algoritmo6E.rb", "emrubio85")
    else:
        print("Opción no válida.")