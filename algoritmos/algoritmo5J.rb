# Asignación de variables
x = 5
y = 3 + 2 * 4
z = (x + y) / 2
$global_count = 10
@instance_value = x ** 2
@@class_value = $global_count % 3

# Ejemplo de rangos
inclusive_range = 1..5
exclusive_range = 1...5

# Loop con rango
for i in 1..5 do
  total = i * 2 + x
end

# For loop usando variable
for n in inclusive_range do
  value = n + z
end

# Función con parámetros opcionales
def multiply_add(a, b = 2, c = 5)
  result = a * b + c
  puts "El resultado es, #{resultado}"
end

def print_results(base = 10)
  total = base + y * 2
  puts "El total es, #{total}"
end

#Errores
x == 5
exclusive_range = 1...
for i in 1..5 do
  total = i * 2 + x
def print_results(base = 10)
  total = base + y * 2
  puts "El total es, #{total}"
endd