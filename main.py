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
    # Registrar tipo en tabla de símbolos
    var_node = p[1]
    if isinstance(var_node, tuple) and var_node[0] == 'var':
        var_name = var_node[1]
        # Validar la expresión (esto dispara verificaciones semánticas)
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
    'if_stmt : IF expression_logic stmt_block END_S'
    p[0] = ('if', p[2], p[3], [], None)

def p_if_stmt_else(p):
    'if_stmt : IF expression_logic stmt_block ELSE stmt_block END_S'
    p[0] = ('if', p[2], p[3], [], ('else', p[5]))

def p_if_stmt_elsif(p):
    'if_stmt : IF expression_logic stmt_block elsif_list END_S'
    p[0] = ('if', p[2], p[3], p[4], None)

def p_if_stmt_elsif_else(p):
    'if_stmt : IF expression_logic stmt_block elsif_list ELSE stmt_block END_S'
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
    print("7 - algoritmo7B.rb (BrayanBriones) ")
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
    elif opcion == "7":
        analizar_sintaxis("algoritmo7B.rb", "BrayanBriones")
    else:
        print("Opción no válida.")