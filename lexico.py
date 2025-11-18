import re
import ply.lex as lex
import os
from datetime import datetime
from zoneinfo import ZoneInfo


#cambio hecho por elias rubio git emrubio_85...
reserved = {
            "if": "IF", "while": "WHILE","def": "DEF", "return": "RETURN", "BEGIN": "BEGIN_U",
            'else': 'ELSE', 'for': 'FOR', 'class': 'CLASS', 'nil': 'NIL', 'true': 'TRUE',
            'false': 'FALSE', 'END': 'END_U', '__ENCODING__': 'ENCODING', 'begin': 'BEGIN_S',
            '__LINE__': 'LINE', '__FILE__': 'FILE', 'alias': 'ALIAS', 'and': 'AND', 'break': 'BREAK',
            'case': 'CASE', 'defined?': 'DEFINEDQ', 'do': 'DO', 'end': 'END_S', 'elsif': 'ELSIF',
            'ensure': 'ENSURE', 'in': 'IN', 'module': 'MODULE', 'next': 'NEXT', 'not': 'NOT',
            'or': 'OR', 'redo': 'REDO', 'rescue': 'RESCUE', 'retry': 'RETRY', 'self': 'SELF',
            'super': 'SUPER', 'then': 'THEN', 'undef': 'UNDEF', 'unless': 'UNLESS', 'until': 'UNTIL',
            'when': 'WHEN', 'yield': 'YIELD', "print": "PRINT", "puts": "PUTS", "type":"TYPE",
            }
#...fin cambio hecho por elias rubio git emrubio_85

# Lista de tokens creada por Brayan Briones git BrayanBriones
tokens = (
    # literales
    'FLOAT', 'INTEGER', 'RATIONAL', 'COMPLEX',
    'STR', 'SYMBOL', 'REGEXP',

    # identificadores / variables (separados por tipo)
    'GLOBAL_VAR', 'LOCAL_VAR', 'INSTANCE_VAR', 'CLASS_VAR', 'CONSTANT',


    # comparación
    'LT', 'LE', 'GT', 'GE', 'EQ', 'NE', 'EQQ', 'CMP', 'MATCH', 'NMATCH',

    # lógicos
    'ANDAND', 'OROR', 'BANG',

    # rangos
    'RANGE_INCL', 'RANGE_EXCL',

    #cambio hecho por elias rubio git emrubio_85...

    # operadores aritmeticos
    'PLUS', 'MINUS', 'MULT', 'DIV', 'MOD', 'POWER',  # Power --> POTENCIACION

    # operadores logicos bitwise
    'B_AND', 'B_OR', 'B_XOR', 'B_ONES', 'B_LEFT_SHIFT', 'B_RIGHT_SHIFT', 

    # operadores asignacion
    'EQLS', 'PLUSEQLS', 'MINUSEQLS', 'MULTEQLS', 'DIVEQLS', 'MODEQLS', 'POWEREQLS', 'QUESTION',

    # delimitadores Juseperez
    'LPAREN', 'RPAREN',
    'LBRACKET', 'RBRACKET',
    'LBRACE', 'RBRACE',
    'COMMA', 'COLON', 'SEMICOLON', 'DOT', 'ARROW',
    #'NEW_LINE',
    'INTERPOLATION',

#...fin cambio hecho por elias rubio git emrubio_85
) + tuple(sorted(set(reserved.values())))

errores_lexicos = []

# Operadores multi-caracter creados por Brayan Briones git BrayanBriones

def t_EQQ(t):
    r'==='
    return t

def t_EQ(t):
    r'=='
    return t

def t_NE(t):
    r'!='
    return t

def t_CMP(t):
    r'<=>'
    return t

def t_MATCH(t):
    r'=~'
    return t

def t_NMATCH(t):
    r'!~'
    return t

def t_LE(t):
    r'<='
    return t

def t_GE(t):
    r'>='
    return t

def t_RANGE_EXCL(t):
    r'\.\.\.'
    return t

def t_RANGE_INCL(t):
    r'\.\.'
    return t

def t_ANDAND(t):
    r'&&'
    return t

def t_OROR(t):
    r'\|\|'
    return t

def t_ARROW(t):
    r'=>'
    return t

#cambio hecho por elias rubio git emrubio_85...
def t_PLUSEQLS(t):
    r'\+\='
    return t
def t_MINUSEQLS(t):
    r'-\='
    return t
def t_MULTEQLS(t):
    r'\*\='
    return t
def t_POWEREQLS(t):
    r'\*\*\='
    return t
def t_DIVEQLS(t):
    r'/\='
    return t
def t_MODEQLS(t):
    r'%\='
    return t
def t_B_RIGHT_SHIFT(t):
    r'>>'
    return t
def t_B_LEFT_SHIFT(t):
    r'<<'
    return t

#...fin cambio hecho por elias rubio git emrubio_85


# Operadores de Comparacion creados por Brayan Briones git BrayanBriones
t_LT     = r'<'
t_GT     = r'>'
t_BANG   = r'!'
t_DOT    = r'\.'

#Delimitadores Juseperez
t_LPAREN   = r'\('
t_RPAREN   = r'\)'
t_LBRACKET = r'\['
t_RBRACKET = r'\]'
t_LBRACE   = r'\{'
t_RBRACE   = r'\}'
t_COMMA    = r','
t_COLON    = r':'
t_SEMICOLON = r';'

#cambio hecho por elias rubio git emrubio_85...

t_PLUS = r'\+'
t_MINUS = r'-'
t_MULT = r'\*'
t_DIV = r'/'
t_MOD = r'%'
t_POWER = r'\*\*'
t_EQLS  = r'='
t_B_AND = r'&'
t_B_OR = r'\|'
t_B_XOR = r'\^'
t_B_ONES = r'~'
t_QUESTION = r'\?'
#...fin cambio hecho por elias rubio git emrubio_85

# String Ruby creado por Brayan Briones git BrayanBriones:
# - "..." con escapes y \#\{...\} (interpolación no anidada aquí)
# - '...' con escapes básicos
# - %q/%Q con { }, ( ), [ ], < >
#   Se implementa en una sola regex para cumplir con PLY.

#Juseperez Interpolación
def t_INTERPOLATION(t):
    r'\#\{[^}]*\}'
    return t

#Comentarios

def t_comment_single(t):
    r'\#.*'
    pass 

def t_STR(t):
    r'"([^"\\]|\\.|\#\{[^}]*\})*"|\'([^\'\\]|\\.)*\'|%[Qq](\{[^}]*\}|\([^)]*\)|\[[^\]]*\]|<[^>]*>)'
    return t

# Heredoc básico: <<LABEL, <<-LABEL, <<~LABEL
# Tokenizado como STR creado por Brayan Briones git BrayanBriones
def t_HEREDOC(t):
    r'<<[-~]?[A-Za-z_]\w*'
    m = re.match(r'<<(?:[-~]?)([A-Za-z_]\w*)', t.value)
    label = m.group(1)
    allow_indent = '-' in t.value or '~' in t.value
    start = t.lexer.lexpos
    data = t.lexer.lexdata

    # saltar hasta fin de línea del inicio de heredoc
    nl = data.find('\n', start)
    if nl == -1:
        t.type = 'STR'
        t.value = ''
        t.lexer.lexpos = start
        return t
    content_start = nl + 1

    # patrón de terminación
    if allow_indent:
        end_pat = r'^[ \t]*' + re.escape(label) + r'[ \t]*\r?\n'
    else:
        end_pat = r'^' + re.escape(label) + r'[ \t]*\r?\n'

    end_re = re.compile(end_pat, re.MULTILINE)
    m_end = end_re.search(data, content_start)
    if m_end:
        content_end = m_end.start()
        t.value = data[content_start:content_end]
        t.type = 'STR'
        t.lexer.lexpos = m_end.end()
        # sumar líneas consumidas (contenido + línea del terminador)
        t.lexer.lineno += t.value.count('\n') + 1
        return t
    else:
        # sin terminador: consumir hasta el final
        t.value = data[content_start:]
        t.type = 'STR'
        t.lexer.lexpos = len(data)
        t.lexer.lineno += t.value.count('\n')
        return t

# Símbolos :ident o :"string con espacios"
def t_SYMBOL(t):
    r':([A-Za-z_]\w*|"(?:[^"\\]|\\.)*")'
    return t

# Expresiones regulares /.../flags  (colocar antes de DIVIDE)
def t_REGEXP(t):
    r'/([^/\\]|\\.)*/[imxounse]*'
    return t



# Identificadores / variables / constantes / métodos ? ! = creados por Brayan Briones git BrayanBriones
# Se separan por tipo: CLASS_VAR (@@), INSTANCE_VAR (@), GLOBAL_VAR ($), CONSTANT (Mayúsculas), LOCAL_VAR (identificador normal).
# Las palabras reservadas se asignan desde 'reserved' para LOCAL_VAR.
def t_CLASS_VAR(t):
    r'@@[A-Za-z_]\w*'
    return t

def t_INSTANCE_VAR(t):
    r'@[A-Za-z_]\w*'
    return t

def t_GLOBAL_VAR(t):
    r'\$(?:[A-Za-z_]\w*|\d+)'
    return t

def t_CONSTANT(t):
    r'__?[A-Z][A-Za-z_]\w*__?|[A-Z][A-Za-z_]\w*'
    # Mantener tokens especiales como __ENCODING__ si están en reserved
    if t.value in reserved:
        t.type = reserved[t.value]
    return t

def t_LOCAL_VAR(t):
    r'[A-Za-z_]\w*[!?=]?'
    # mapear a palabra reservada si corresponde (e.g., if, while, def)
    if t.value in reserved:
        t.type = reserved[t.value]
    return t

# Números: racionales y complejos simples
def t_RATIONAL(t):
    r'(?:\d+/\d+|\d+)r'
    t.value = t.value
    return t

def t_COMPLEX(t):
    r'(?:\d+(?:\.\d+)?[+-]\d+(?:\.\d+)?i|\d+(?:\.\d+)?i)'
    t.value = t.value
    return t

def t_FLOAT(t):
    r'\d+\.\d+(?:[eE][+-]?\d+)?'
    # mantener semántica original (no castear a float)
    t.value = t.value
    return t

def t_INTEGER(t):
    r'\d+'
    t.value = int(t.value)
    return t


#----------------
#Aporte Juseperez
#----------------


# Comentarios de bloque: =begin ... =end (líneas propias)
states = (('MLC','exclusive'),)
t_MLC_ignore = ' \t'
def t_begin_mlc(t):
    r'=begin[^\n]*\n'
    t.lexer.push_state('MLC')

def t_MLC_end(t):
    r'\n=end[^\n]*'
    t.lexer.pop_state()

def t_MLC_any(t):
    r'.'
    pass

def t_MLC_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

    #Salto de línea

'''def t_NEW_LINE(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    t.value = "\\n"
    return t
    '''



# Define a rule so we can track line numbers
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# A string containing ignored characters (spaces and tabs)
t_ignore  = ' \t'

# Error handling rule
def t_error(t):
    mensaje_error =f"Componente léxico {t.value[0]} no existe en Ruby en la línea {t.lexer.lineno}"
    print(mensaje_error)
    errores_lexicos.append(mensaje_error)
    t.lexer.skip(1)

def t_MLC_error(t):
    t.lexer.skip(1)

lexer = lex.lex()

