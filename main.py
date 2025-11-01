import re
import ply.lex as lex


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
            'when': 'WHEN', 'yield': 'YIELD'
            }
#...fin cambio hecho por elias rubio git emrubio_85

# Lista de tokens
tokens = (
    # literales
    'FLOAT', 'INTEGER', 'RATIONAL', 'COMPLEX',
    'STR', 'SYMBOL', 'REGEXP',

    # identificadores / variables
    'VARIABLE',

    # comparación
    'LT', 'LE', 'GT', 'GE', 'EQ', 'NE', 'EQQ', 'CMP', 'MATCH', 'NMATCH',

    # lógicos
    'ANDAND', 'OROR', 'BANG',

    # rangos
    'RANGE_INCL', 'RANGE_EXCL',

    # delimitadores / separadores
    'LPAREN', 'RPAREN',
    'LBRACKET', 'RBRACKET',
    'LBRACE', 'RBRACE',
    'COMMA', 'COLON', 'SEMICOLON', 'DOT', 'ARROW',

    #cambio hecho por elias rubio git emrubio_85...

    # operadores aritmeticos
    'SUMA', 'RESTA', 'MULTI', 'DIV', 'MOD', 'POTE',  # POTE --> POTENCIACION


    # operadores asignacion
    'EQLS', 'SUMAEQLS', 'RESTAEQLS', 'MULTIEQLS', 'DIVEQLS', 'MODEQLS',

#...fin cambio hecho por elias rubio git emrubio_85
) + tuple(sorted(set(reserved.values())))

# Operadores multi-caracter

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
def t_SUMAEQLS(t):
    r'\+\='
    return t
def t_RESTAEQLS(t):
    r'-\='
    return t
def t_MULTIEQLS(t):
    r'\*\='
    return t
def t_DIVEQLS(t):
    r'/\='
    return t
def t_MODEQLS(t):
    r'%\='
    return t
#...fin cambio hecho por elias rubio git emrubio_85


# Operadores de Comparacion
t_LT     = r'<'
t_GT     = r'>'
t_BANG   = r'!'
t_DOT    = r'\.'

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

t_SUMA = r'\+'
t_RESTA = r'-'
t_MULTI = r'\*'
t_DIV = r'/'
t_MOD = r'%'
t_POTE = r'\*\*'
t_EQLS  = r'='

#...fin cambio hecho por elias rubio git emrubio_85

# Strings Ruby:
# - "..." con escapes y \#\{...\} (interpolación no anidada aquí)
# - '...' con escapes básicos
# - %q/%Q con { }, ( ), [ ], < >
#   Se implementa en una sola regex para cumplir con PLY.
def t_STR(t):
    r'"([^"\\]|\\.|\#\{[^}]*\})*"|\'([^\'\\]|\\.)*\'|%[Qq](\{[^}]*\}|\([^)]*\)|\[[^\]]*\]|<[^>]*>)'
    return t

# Heredoc básico: <<LABEL, <<-LABEL, <<~LABEL
# Tokenizado como STR
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

# Identificadores / variables / constantes / métodos ? ! =
# Incluye: @@foo, @foo, $foo, $1, CONSTANTE, local, foo?, bar!, baz=
# y mapea a reservadas si corresponde.
def t_VARIABLE(t):
    r'(?:@@|@|\$)?[A-Za-z_]\w*[!?=]?|\$\d+|__[A-Z]+__'
    t.type = reserved.get(t.value, 'VARIABLE')
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




# Define a rule so we can track line numbers
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# A string containing ignored characters (spaces and tabs)
t_ignore  = ' \t'

# Error handling rule
def t_error(t):
    print(f"Componente léxico {t.value[0]} no existe en este lenguaje")
    t.lexer.skip(1)

# Build the lexer
lexer = lex.lex()

# Test it out
data = ''' 45+3%
3 + 4 * _ab + _if _if3 if + _print BEGIN
  + -20 *2 > < true
'''

# Give the lexer some input
lexer.input(data)

# Tokenize
while True:
    tok = lexer.token()
    if not tok:
        break      # No more input
    print(tok)