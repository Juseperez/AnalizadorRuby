# Algoritmo de prueba - cubre literales, operadores, strings, regex, heredoc, símbolos, comentarios y estructuras

# Comentario de bloque
=begin
Bloque de comentario para probar =begin ... =end
Incluye líneas múltiples
=end

# Comentario single-line
# Esto es un comentario simple

# Variables y constantes
CONSTANTE = 42
@inst_var = "instancia"
@@class_var = :clase
$global_var = 100

local_var = 10
another_var = 3.14  # FLOAT
int_var = 7         # INTEGER

# Rational y Complex como literales para el lexer (ejemplos textuales)
rational1 = 2/3r
rational2 = 5r
complex1 = 1+2i
complex2 = 3i

# Strings y interpolación
name = "Ruby"
greeting = "Hola #{name}, prueba de interpolación \n y escapes \" \\ "
single_q = 'cadena simple con \\n y comillas simples'

# %Q / %q forms
percent_q = %q(esto es %q (sin interpolación))
percent_Q = %Q{esto es %Q con #{name}}

# Heredocs
texto1 = <<LABEL
Heredoc básico
Linea 2
LABEL

texto2 = <<-INDENT
    Heredoc con indentación permitida
      otra linea
INDENT

texto3 = <<~STRIP
      Heredoc con indentación removida
    linea
STRIP

# Símbolos
sym1 = :simple
sym2 = :"símbolo con espacios"

# Expresiones regulares
re1 = /ab+c/i
re2 = /\/escaped\/slash/  # regex con slash escapado

# Operadores de comparación y lógicos
a = 5
b = 10
eq1 = (a == b)
identical = (a === b)
ne = (a != b)
cmp = (a <=> b)
match = ("hola" =~ /la$/)
nmatch = ("hola" !~ /x/)

# Rango incluido y excluyente
r_inc = (1..5)
r_exc = (1...5)

# Operadores bitwise y shifts
x = 0b1010
y = x & 0b1100
z = x | 0b0011
w = x ^ 0b0101
ones = ~x
left = x << 2
right = x >> 1

# Operadores aritméticos y asignaciones combinadas
sum = 1 + 2
sum += 3
sum -= 1
prod = 2 * 3
prod *= 4
div = 10 / 2
div /= 5
mod = 10 % 3
mod %= 2
pow = 2 ** 3
pow **= 2

# Otros tokens: punto, coma, dos puntos, punto y coma, flecha (hash rocket)
obj = { :a => 1, "b" => 2, c: 3 }
arr = [1, 2, 3]
hash_arrow = { "key" => "value" }

# Ternario y pregunta
cond = (a < b) ? "menos" : "mas"
pregunta = true ? "si" : "no"

# Definiciones, clases, bloques, loops y control de flujo para cubrir tokens reservados
def ejemplo_param(x, y=1)
  return x + y if y > 0
  nil
end

class MiClase
  def initialize(val)
    @val = val
  end

  def mostrar
    puts "Valor: #{@val}"
  end
end

m = MiClase.new(7)
m.mostrar

# while, for, begin/rescue/ensure
i = 0
while i < 2
  puts "while #{i}"
  i += 1
end

for j in 0..1
  puts "for #{j}"
end

begin
  raise "error de prueba" if false
rescue => e
  puts "rescued: #{e}"
ensure
  # siempre pasa
end

# yield y block
def con_block
  yield if block_given?
end

con_block { puts "block pasado" }

# Uso de defined? y otros operadores especiales
puts defined?(CONSTANTE)
puts nil.nil?
puts true && false
puts true || false
puts not false

# Fin del archivo de prueba