import ply.lex as lex


reserved = {"_print":"PRINT",
            "_if":"IF",
            "_while":"WHILE",
            "_def":"DEF",
            "_return":"RETURN",
            "BEGIN":"BEGINUPPER"
            }

# List of token names.   This is always required
tokens = (
   'INTEGER',
   'FLOAT',
   'BOOLEAN',
   'PLUS',
   'MINUS',
   'TIMES',
   'DIVIDE',
   'LPAREN',
   'RPAREN',
   'MODULE',
   'LESSTHAN',
   'GREATERTHAN',
    'VARIABLE',
    'ID',
)+tuple(reserved.values())

# Regular expression rules for simple tokens
t_PLUS    = r'\+'
t_MINUS   = r'-'
t_TIMES   = r'\*'
t_DIVIDE  = r'/'
t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_MODULE  = r'%'
t_LESSTHAN=r'<'
t_GREATERTHAN=r'>'


def t_BOOLEAN(t):
    r'(true|false)'
    return t

def t_VARIABLE(t):
    r'_[a-z]\w*'
    t.type=reserved.get(t.value, "VARIABLE")
    return t

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value,'ID')
    return t


def t_FLOAT(t):
    r'\d+\.\d+'
    t.value = float(t.value)
    return t

# A regular expression rule with some action code
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
data = ''' 44+3%
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