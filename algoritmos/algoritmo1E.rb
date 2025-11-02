45+3%
3 + 4 * _ab + _if _if3 if + _print BEGIN
  + -20 *2 > < true

### Operadores unarios
+5
-10
~0         
!true
not false

### Operadores binarios aritméticos y de comparación
1 + 2 - 3 * 4 / 5 % 6 ** 2
a = 1
b = 2.0
c = a < b
d = a <= b
e = a > b
f = a >= b
g = a == b
h = a != b
i = a <=> b

### Asignaciones compuestas y combinación con otros tokens
x = 0
x += 1
x -= 2
x *= 3
x /= 4
x %= 5
x **= 2
arr[0] ||= 100
hash[:k] ||= 'v'

### Operadores lógicos y bitwise
p = true && false
q = true || false
r = true & false
s = true | false
t = true ^ false

### Operador de rango
(1..5).to_a
(1...5).to_a

### Operadores de asignación múltiple, splat y doble splat
a, b = [1, 2]
c, *rest = [3, 4, 5]
d = {x: 1, y: 2}
e = **{z: 3} rescue nil

### Símbolos y operadores relacionados
:foo
:"bar-baz"
:"with spaces"
:+
:==

str = <<~RUBY
  if true
    x += 1
  end
RUBY

def metodo(arg = nil, *rest, &blk)
  return :ret if arg == :ret
  yield if block_given?
  super if defined?(super)
end

class MiClase < BaseClase
  include Enumerable
  extend Forwardable

  def initialize(v)
    @v = v
  end

  private

  def secreto?
    @v == :secreto
  end
end

module MiModulo
  CONST = 123
end

if true
  puts 'si'
elsif false
  puts 'elsif'
else
  puts 'no'
end

unless false
  ok = true
end

while false
  break
end

until true
  next
end

for i in 0..2
  redo if i == 1
end

begin
  raise StandardError, 'err'
rescue StandardError => ex
  retry if ex.message == 'retryable'
else
  :ok
ensure
  # cleanup
end

case a
when 1, 2
  :low
when 3..5
  :mid
else
  :high
end

defined? foo
__LINE__
__FILE__
true; false; nil

1 << 2
4 >> 1
