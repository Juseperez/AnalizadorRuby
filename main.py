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
# Errores encontrados en la fase semántica (añadidos por comprobaciones en reglas)
errores_semanticos = []
# Tabla de símbolos global: {nombre_var: {tipo: 'integer'|'float'|'string'|..., valor: ...}}
tabla_simbolos = {}
# Advertencias semánticas (castings indebidos, operaciones sospechosas)
advertencias_semanticas = []
contexto_bucles = 0
contexto_if = 0

def es_string_numerico_entero(valor_str):
    """Verifica si un string es 100% numérico entero (ej: '123', '-45').
    Devuelve True/False."""
    if not isinstance(valor_str, str):
        return False
    valor_limpio = valor_str.strip()
    if not valor_limpio:
        return False
    # permitir signo negativo al inicio
    if valor_limpio[0] in ('+', '-'):
        valor_limpio = valor_limpio[1:]
    return valor_limpio.isdigit()


def es_string_numerico_flotante(valor_str):
    """Verifica si un string es 100% numérico flotante (ej: '3.14', '-2.5', '1e-5').
    Devuelve True/False."""
    if not isinstance(valor_str, str):
        return False
    valor_limpio = valor_str.strip()
    if not valor_limpio:
        return False
    try:
        float(valor_limpio)
        return True
    except ValueError:
        return False


def obtener_valor_string(node):
    """Extrae el valor de string de un nodo AST.
    Devuelve el string sin comillas, o None si no es un string literal."""
    if node is None:
        return None
    
    if isinstance(node, tuple):
        if node[0] == 'lit' and len(node) > 1:
            valor = node[1]
            if isinstance(valor, str):
                # Remover comillas si existen
                if (valor.startswith('"') and valor.endswith('"')) or \
                   (valor.startswith("'") and valor.endswith("'")):
                    return valor[1:-1]
                return valor
        elif node[0] == 'var' and len(node) > 1:
            # Si es una variable, buscar su valor en la tabla de símbolos
            var_name = node[1]
            if var_name in tabla_simbolos:
                valor_info = tabla_simbolos[var_name].get('valor')
                # Recursivamente obtener el valor
                return obtener_valor_string(valor_info)
    elif isinstance(node, str):
        # Si es un string directo
        if (node.startswith('"') and node.endswith('"')) or \
           (node.startswith("'") and node.endswith("'")):
            return node[1:-1]
        return node
    
    return None


def inferir_tipo_nodo(node):
    """Inferir tipo simple a partir del nodo AST usado por el parser.
    Devuelve 'integer', 'float', 'string', 'symbol', 'boolean', 'array', 'hash' o 'desconocido'.
    """
    if node is None:
        return 'nil'
    # literales numéricos: ('num', valor)
    if isinstance(node, tuple):
        tag = node[0]
        if tag == 'num':
            v = node[1]
            if isinstance(v, int):
                return 'integer'
            if isinstance(v, float):
                return 'float'
            # t_FLOAT in lexer returns string like '3.14'
            if isinstance(v, str):
                if '.' in v or 'e' in v or 'E' in v:
                    return 'float'
                # fallback: digits only
                if v.isdigit():
                    return 'integer'
                return 'desconocido'
        if tag == 'lit':
            val = node[1]
            # STR tokens come as quoted strings or heredoc content
            if isinstance(val, str):
                if val.startswith(':'):
                    return 'symbol'
                # regexp like /.../ also as str, but treat as string for ops
                return 'string'
        if tag == 'str':
            return 'string'
        if tag == 'sym':
            return 'symbol'
        if tag == 'bool':
            return 'boolean'
        if tag == 'array':
            return 'array'
        if tag == 'hash':
            return 'hash'
        if tag == 'var':
            # consultar tabla de símbolos
            nombre = node[1]
            if nombre in tabla_simbolos:
                return tabla_simbolos[nombre].get('tipo', 'desconocido')
            return 'desconocido'
        if tag == 'call':
            # ('call', objeto, método, args) -- soporte para llamadas a métodos
            # .to_i, .to_f, .to_s, .to_a, etc.
            metodo = node[2] if len(node) > 2 else ''
            obj = node[1] if len(node) > 1 else None
            
            # Validar conversiones indebidas (castings inseguros)
            if metodo == 'to_i':
                # Verificar si el objeto es un string y validar su contenido
                obj_tipo = inferir_tipo_nodo(obj)
                if obj_tipo == 'string':
                    # Intentar extraer el valor del string
                    valor_string = obtener_valor_string(obj)
                    if valor_string is not None:
                        if not es_string_numerico_entero(valor_string):
                            aviso = f"Error semántico: Casting indebido - '{valor_string}' no es 100% numérico. .to_i convertirá a 0 o valor parcial"
                            errores_semanticos.append(aviso)
                            print(aviso)
                return 'integer'
            
            if metodo == 'to_f':
                obj_tipo = inferir_tipo_nodo(obj)
                if obj_tipo == 'string':
                    valor_string = obtener_valor_string(obj)
                    if valor_string is not None:
                        if not es_string_numerico_flotante(valor_string):
                            aviso = f"Error semántico: Casting indebido - '{valor_string}' no es 100% numérico. .to_f convertirá a 0.0 o valor parcial"
                            errores_semanticos.append(aviso)
                            print(aviso)
                return 'float'
            
            if metodo == 'to_s' or metodo == 'to_str':
                return 'string'
            if metodo == 'to_a' or metodo == 'to_ary':
                return 'array'
            if metodo == 'to_h' or metodo == 'to_hash':
                return 'hash'
            # fallback: devolver tipo del objeto si no es conversión conocida
            if node:
                return inferir_tipo_nodo(node[1])
            return 'desconocido'
        if tag == 'func_call':
            # ('func_call', nombre, args) -- soporte para llamadas a funciones
            # Por defecto retornamos desconocido (habría que analizar definición)
            return 'desconocido'
        if tag == 'binop':
            # inferir desde operandos
            left_node = node[1] if len(node) > 1 else None
            right_node = node[2] if len(node) > 2 else None
            l = inferir_tipo_nodo(left_node)
            r = inferir_tipo_nodo(right_node)
            op = node[1] if len(node) > 1 else '?'
            # el segundo índice es el operador, tercero es left, cuarto es right
            # reordenar: node es ('binop', op, left, right)
            if len(node) >= 4:
                op = node[1]
                l = inferir_tipo_nodo(node[2])
                r = inferir_tipo_nodo(node[3])
            if l == 'string' and r == 'string':
                return 'string'
            if l in ('integer', 'float') and r in ('integer', 'float'):
                return 'float' if 'float' in (l, r) else 'integer'
            return 'desconocido'
    # si es literal simple
    if isinstance(node, int):
        return 'integer'
    if isinstance(node, float):
        return 'float'
    if isinstance(node, str):
        # comillas indican string literal
        if node.startswith('"') or node.startswith("'"):
            return 'string'
        if node.startswith(':'):
            return 'symbol'
    return 'desconocido'
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


# Jusepere BREAK
def p_statement_break(p):
    'statement : BREAK'
    linea = p.lineno(1)
    if contexto_bucles <= 0:
        errores_semanticos.append(f"Error: break fuera de estructura iterativa. (línea {linea})")
    p[0] = ('break', linea)


# Jusepere NEXT
def p_statement_next(p):
    'statement : NEXT'
    linea = p.lineno(1)
    if contexto_bucles <= 0:
        errores_semanticos.append(f"Error: next fuera de estructura iterativa. (línea {linea})")
    p[0] = ('next', linea)
def p_stmt_block_single(p):
    'stmt_block : statement'
    # Representamos bloque como lista de sentencias
    p[0] = [p[1]]

def p_stmt_block_multiple(p):
    "stmt_block : stmt_block statement"
    p[0] = p[1] + [p[2]]

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
                 | optional_then
                 | stmt_block
                 | elsif_list
                 | else_part
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

    var_node = p[1]
    if isinstance(var_node, tuple) and var_node[0] == 'var':
        var_name = var_node[1]

        # VERIFICACIÓN DE REASIGNACIÓN DE CONSTANTE
        if var_name.isupper() or var_name.startswith('__') and var_name.endswith('__'):
            # Es una constante (mayúsculas o __CONSTANT__)
            if var_name in tabla_simbolos:
                # La constante ya existe, es una reasignación
                linea = p.lineno(2)  # Línea donde está el operador de asignación
                advertencia = f"Advertencia semántica: Reasignación de constante '{var_name}' en línea {linea}"
                advertencias_semanticas.append(advertencia)
                print(advertencia)

        # Registrar tipo en tabla de símbolos
        expr_tipo = inferir_tipo_nodo(p[3])
        tabla_simbolos[var_name] = {
            'tipo': expr_tipo,
            'valor': p[3],
            'operador': p[2]
        }

    p[0] = ('assign', p[1], p[2], p[3])

# --------------------------------------------------
# ESTRUCTURA DE CONTROL: while ... end
# while <cond> do ... end  o  while <cond> ... end
# --------------------------------------------------
#Jusepere Validar el uso correcto de break y next dentro de bucles.
def p_while_stmt(p):
    '''while_stmt : WHILE expression_logic while_enter DO statement_list END_S while_exit
                  | WHILE expression_logic while_enter statement_list END_S while_exit'''
    p[0] = ('while', p[2], p[5])

def p_while_enter(p):
    'while_enter :'
    global contexto_bucles
    contexto_bucles += 1

def p_while_exit(p):
    'while_exit :'
    global contexto_bucles
    contexto_bucles -= 1

# --------------------------------------------------
# Jusepere ESTRUCTURA DE CONTROL: for ... in ... do ... end
# --------------------------------------------------
def p_for_stmt(p):
    '''for_stmt : FOR LOCAL_VAR IN expression for_enter DO statement_list END_S for_exit
                | FOR LOCAL_VAR IN expression for_enter statement_list END_S for_exit'''
    p[0] = ('for', p[2], p[4], p[7])

def p_for_enter(p):
    'for_enter :'
    global contexto_bucles
    contexto_bucles += 1

def p_for_exit(p):
    'for_exit :'
    global contexto_bucles
    contexto_bucles -= 1

#elias rubio
# regla para una sentencia simple

try:
    contexto_if
except NameError:
    contexto_if = 0

def semantica_if_inicio():
    global contexto_if
    contexto_if += 1


def semantica_if_fin():
    global contexto_if
    if contexto_if > 0:
        contexto_if -= 1


def semantica_elsif_check(lineno=None):
    if contexto_if == 0:
        msg = "Error semántico: 'elsif' fuera de un 'if'."
        if lineno:
            msg = f"Línea {lineno}: {msg}"
        errores_semanticos.append(msg)

def semantica_else_check(lineno=None):
    if contexto_if == 0:
        msg = "Error semántico: 'else' fuera de un 'if'."
        if lineno:
            msg = f"Línea {lineno}: {msg}"
        errores_semanticos.append(msg)

# ---------------------------
# Reglas sintácticas 
# ---------------------------

# 
def p_if_stmt(p):
    """if_stmt : IF expression_logic optional_then stmt_block elsif_list else_part END_S"""
    # marca inicio de contexto IF
    semantica_if_inicio()
    try:
        
        p[0] = ('if', p[2], p[4], p[5], p[6])
    finally:
        
        semantica_if_fin()

# optional THEN
def p_optional_then_present(p):
    "optional_then : THEN"
    p[0] = 'THEN'

def p_optional_then_empty(p):
    "optional_then : empty"
    p[0] = None

# elsif_list left-recursive
def p_elsif_list_empty(p):
    "elsif_list : empty"
    p[0] = []

def p_elsif_list_left_recursive(p):
    """elsif_list : elsif_list ELSIF expression_logic optional_then stmt_block"""
    this = ('elsif', p[3], p[5])
    p[0] = p[1] + [this]

# else opcional
def p_else_part_empty(p):
    "else_part : empty"
    p[0] = None

def p_else_part(p):
    "else_part : ELSE stmt_block"
    # si ELSE aparece, comprobamos contexto semántico (por si aparece fuera de if)
    try:
        lineno = p.lineno(1)
    except Exception:
        lineno = None
    semantica_else_check(lineno)
    p[0] = p[2]

# ---------------------------
# Reglas para detectar ELSIF / ELSE sueltos como statement
# ---------------------------

def p_statement_invalid_elsif_full(p):
    "statement : ELSIF expression_logic optional_then stmt_block"
    try:
        lineno = p.lineno(1)
    except Exception:
        lineno = None
    semantica_elsif_check(lineno)    
    p[0] = ('semantic_error', "elsif_fuera_de_if")

def p_statement_invalid_elsif_short(p):
    "statement : ELSIF expression"
    try:
        lineno = p.lineno(1)
    except Exception:
        lineno = None
    semantica_elsif_check(lineno)
    p[0] = ('semantic_error', "elsif_fuera_de_if")

def p_statement_invalid_else_full(p):
    "statement : ELSE stmt_block"
    try:
        lineno = p.lineno(1)
    except Exception:
        lineno = None
    semantica_else_check(lineno)
    p[0] = ('semantic_error', "else_fuera_de_if")

def p_statement_invalid_else_short(p):
    "statement : ELSE"
    try:
        lineno = p.lineno(1)
    except Exception:
        lineno = None
    semantica_else_check(lineno)
    p[0] = ('semantic_error', "else_fuera_de_if")
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
               | variable
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

# 3b) Function call: variable_local(args)
def p_function_call_expression(p):
    '''expr_postfix : LOCAL_VAR LPAREN RPAREN
                    | LOCAL_VAR LPAREN expr_list RPAREN'''
    # ('func_call', nombre, [args])
    func_name = p[1]
    if len(p) == 4:
        # func()
        p[0] = ('func_call', func_name, [])
    else:
        # func(args)
        p[0] = ('func_call', func_name, p[3])

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

# pila para contexto de funciones: cada elemento es dict { 'name': str, 'expected_return': tipo|None, 'returns': [tipo|None] }
func_context_stack = []

# --- util: normalizar/inferrar tipos sencillos desde nodos AST de expresion/literales ---
def infer_type_from_expr(expr):
    # expr puede ser un literal simple o un AST más complejo; adaptarlo a tu AST real
    # Ejemplos manejados aquí: ('num', 42), ('str', "hola"), ('nil', None), ('bool', True), ('ident', 'a'), ('binop', op, left, right)
    if expr is None:
        return 'nil'
    if isinstance(expr, tuple):
        tag = expr[0]
        if tag == 'num':      # número literal
            return 'number'
        if tag == 'str':
            return 'string'
        if tag == 'nil':
            return 'nil'
        if tag == 'bool':
            return 'boolean'
        if tag == 'ident':
            # no podemos inferir el tipo de una variable simple aqui; devolver unknown
            return 'unknown'
        if tag == 'binop':
            # ejemplo simplificado: si ambos operandos son number => number; si uno unknown => unknown
            _, op, left, right = expr
            lt = infer_type_from_expr(left)
            rt = infer_type_from_expr(right)
            if lt == 'number' and rt == 'number':
                return 'number'
            # otras heurísticas mínimas:
            if lt == 'string' or rt == 'string':
                # concatenación u otras operaciones con strings no manejadas aquí
                return 'string'
            return 'unknown'
    # por defecto
    return 'unknown'

# --- helpers de contexto ---
def func_enter(name, expected_return_type=None):
    func_context_stack.append({
        'name': name,
        'expected_return': expected_return_type,  # 'number','string','boolean','nil' o None
        'returns': []  # lista de tipos inferidos de cada return en el cuerpo
    })

def func_exit():
    ctx = func_context_stack.pop() if func_context_stack else None
    return ctx

def func_current():
    return func_context_stack[-1] if func_context_stack else None

def check_return_against_expected(ret_type, lineno=None):
    ctx = func_current()
    if ctx is None:
        # return fuera de función: podría ser un  semantico error
        msg = "Error semántico: 'return' fuera de una función."
        if lineno:
            msg = f"Línea {lineno}: {msg}"
        errores_semanticos.append(msg)
        return

    ctx['returns'].append(ret_type)

    expected = ctx['expected_return']
    if expected is None:
        # si no hay anotación, intentamos inferir consistencia: si ya hay otros returns no-unknown,
        # forzamos que coincidan entre sí 
        non_unknown = [t for t in ctx['returns'] if t and t != 'unknown']
        if len(non_unknown) >= 2 and len(set(non_unknown)) > 1:
            # tipos distintos inferidos entre distintos returns
            msg = f"Error: tipos de retorno inconsistentes en función '{ctx['name']}'."
            if lineno:
                msg = f"Línea {lineno}: {msg}"
            errores_semanticos.append(msg)
    else:
        #  comprobar compatibilidad básica
        # permitimos que 'nil'
        compatible = False
        if ret_type == expected:
            compatible = True
        elif ret_type == 'unknown':
            
            compatible = True
        elif ret_type == 'nil' and expected != 'number' and expected != 'string':
            
            compatible = True
        
        if not compatible:
            msg = f"Error: Tipo de retorno no coincide con expectativas {expected}."
            if lineno:
                msg = f"Línea {lineno}: {msg}"
            errores_semanticos.append(msg)


def p_function_def_with_ret(p):
    '''function_def : DEF LOCAL_VAR optional_params optional_ret statement_list END_S'''
    # p[2] nombre; p[3] params; p[4] anotacion de retorno (tipo string) o None; p[5] cuerpo
    name = p[2]
    params = p[3] or []
    ret_annot = p[4]  # por ejemplo 'number','string', None
    # al entrar en la función, registramos contexto
    func_enter(name, ret_annot)
    # NOTA: si quieres hacer checks mientras parseas los statement (ej. returns), las reglas de statement deben llamar a check_return...
    # Aquí, construimos el AST y salimos del contexto
    body = p[5]
    ctx = func_exit()
    p[0] = ('def', name, params, ret_annot, body)

# regla para anotación de retorno opcional (ej: ':' TYPE)
def p_optional_ret(p):
    '''optional_ret : COLON TYPE
                    | empty'''
    if len(p) == 3:
        
        p[0] = p[2]
    else:
        p[0] = None


# ---------------------------------------------------
# Return: en la regla p_return_stmt se hace la comprobación semántica
# ---------------------------------------------------
def p_return_stmt(p):
    '''statement : RETURN
                 | RETURN expression'''
    if len(p) == 2:
        # return sin expresión => tipo 'nil'
        ret_type = 'nil'
        try:
            lineno = p.lineno(1)
        except Exception:
            lineno = None
        check_return_against_expected(ret_type, lineno)
        p[0] = ('return', None)
    else:
        expr = p[2]
        ret_type = infer_type_from_expr(expr)
        try:
            lineno = p.lineno(1)
        except Exception:
            lineno = None
        check_return_against_expected(ret_type, lineno)
        p[0] = ('return', expr)

# ---------------------------------------------------
# Ejemplo simplificado de reglas de expresión para permitir inferencia
# ---------------------------------------------------


def p_expression_nil(p):
    "expression : NIL"
    p[0] = ('nil', None)

def p_expression_bool_true(p):
    "expression : TRUE"
    p[0] = ('bool', True)

def p_expression_bool_false(p):
    "expression : FALSE"
    p[0] = ('bool', False)


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
    # comprobaciones semánticas básicas relacionadas con strings y conversiones
    op = p[2]
    left = p[1]
    right = p[3]
    left_t = inferir_tipo_nodo(left)
    right_t = inferir_tipo_nodo(right)

    # Regla: concatenación '+' sólo válida entre strings
    if op == '+':
        if left_t == 'string' and right_t == 'string':
            pass  # válido
        elif left_t == 'string' and right_t != 'string':
            msg = f"Error semántico: No se puede concatenar String con {right_t}"
            print(msg)
            errores_semanticos.append(msg)
        elif right_t == 'string' and left_t != 'string':
            msg = f"Error semántico: No se puede concatenar {left_t} con String"
            print(msg)
            errores_semanticos.append(msg)

    # Regla: operaciones aritméticas no válidas con strings
    if op in ('-', '*', '/', '%', 'POWER'):
        if left_t == 'string' or right_t == 'string':
            msg = f"Error semántico: Operación '{op}' no permitida entre {left_t} y {right_t}"
            print(msg)
            errores_semanticos.append(msg)

    # Regla: permitir conversiones numéricas implícitas entre integer y float
    # No se hace nada aquí (aceptable): integer + float -> float
    # Nota: conversiones explícitas (.to_i, .to_f) se manejan en p_method_call

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

def p_expression_postfix(p):
    'expression : expr_postfix'
    p[0] = p[1]

# --------------------------------------------------
# LLAMADAS A MÉTODOS (method calls)
# Soporta: expr.metodo o expr.metodo(args)
# Ej: "123".to_i, x.to_f, [1,2].length
# --------------------------------------------------
def p_method_call(p):
    '''expr_postfix : expr_postfix DOT LOCAL_VAR
                    | expr_postfix DOT LOCAL_VAR LPAREN RPAREN
                    | expr_postfix DOT LOCAL_VAR LPAREN expr_list RPAREN'''
    # ('call', objeto, método, [args] o None)
    obj = p[1]
    metodo = p[3]
    if len(p) == 4:
        # expression.metodo
        p[0] = ('call', obj, metodo, [])
    elif len(p) == 6:
        # expression.metodo()
        p[0] = ('call', obj, metodo, [])
    else:
        # expression.metodo(args)
        p[0] = ('call', obj, metodo, p[5])

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

def analizar_semantica(nombre_archivo, usuario):
    global errores_semanticos
    errores_semanticos = []  # reiniciar errores cada análisis

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
    nombre_log = f"semantico-{usuario}-{ahora}.txt"
    ruta_log = os.path.join("logs", nombre_log)

    with open(ruta_log, "w", encoding="utf-8") as log:
        log.write(f"LOG de análisis semántico: {ruta_archivo}\n")
        log.write(f"Usuario: {usuario}\n")
        log.write(f"Fecha y hora: {ahora}\n")
        log.write("=" * 50 + "\n")

        if errores_semanticos:
            log.write("Errores semánticos encontrados:\n")
            for e in errores_semanticos:
                log.write(f"- {e}\n")
        else:
            log.write("Sin errores semánticos.\n")


        if advertencias_semanticas:
            log.write("Advertencias semánticas encontradas:\n")
            for a in advertencias_semanticas:
                log.write(f"- {a}\n")
        else:
            log.write("Sin advertencias semánticas.\n")

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
    print("7 - algoritmo7B.rb (BrayanBriones) ")
    print("8 - algoritmo8J.rb (Juseperez) ")
    print("9 - algoritmo9E.rb (Elias Rubio) ")
    opcion = input("Ingrese su opción: ").strip()

    if opcion == "1":
        analizar_semantica("algoritmo1E.rb", "emrubio85")
    elif opcion == "2":
        analizar_semantica("algoritmo2B.rb", "BrayanBriones")
    elif opcion == "3":
        analizar_semantica("algoritmo3J.rb", "Juseperez")
    elif opcion == "4":
        analizar_semantica("algoritmo4B.rb", "BrayanBriones")
    elif opcion == "5":
        analizar_semantica("algoritmo5J.rb", "Juseperez")
    elif opcion == "6":
        analizar_semantica("algoritmo6E.rb", "emrubio85")
    elif opcion == "7":
        analizar_semantica("algoritmo7B.rb", "BrayanBriones")
    elif opcion == "8":
        analizar_semantica("algoritmo8J.rb", "Juseperez")
    elif opcion == "9":
        analizar_semantica("algoritmo9E.rb", "Elias Rubio")
    else:
        print("Opción no válida.")