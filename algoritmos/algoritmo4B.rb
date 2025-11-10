#Prueba de codigo sin errores
# 1) ingreso de datos por teclado
print "Ingresa tu nombre: "
nombre = gets

# 2) hash literal con las dos sintaxis
usuario = {
  nombre: nombre,         # estilo simbolo:
  "rol" => "estudiante"   # estilo => 
}

# 3) función sin retorno explícito
def saludar(persona)
  puts "Hola, #{persona}!"
  # sin return, Ruby devuelve la última expresión
end

# 4) asignaciones y expresiones
contador = 0
limite = 3
suma = 1 + 2 * 3   # para probar expr aritméticas

# 5) while ... end (con do)
while contador < limite do
  puts "Iteración #{contador}"
  contador = contador + 1
end

# 6) usar la función
saludar(nombre)

# 7) imprimir el hash para ver que lo tomó
puts "Hash de usuario:"
puts usuario

# Prueba con errores sintácticos intencionales

# 1. Falta comillas de cierre en cadena
#print "Hola mundo  #Si se descomenta señalara un error lexico y no continuara mostrando errores sintacticos

# 2. Falta palabra clave 'end' en la función
def sumar(a, b)
  resultado = a + b
  puts resultado
# <-- falta end aquí

# 3. Estructura while sin condición
while do
  puts "loop sin condición"
end

# 4. Asignación incorrecta (operador doble igual)
x == 10

# 5. Hash con coma extra y error de sintaxis
datos = { nombre: "Juan", edad: 20, , ciudad: "Quito" }

# 6. Error de indentación de bloque (end de más)
if true
  puts "Condición verdadera"
end
end

# 7. Error en paréntesis desbalanceado
puts("Hola mundo"

# 8. Uso de variable no declarada con símbolo extraño
$nombre? = "Error"

# 9. Operador aritmético mal puesto
total = 10 + * 5

# 10. Llamada de método mal escrita
puts "Finalizado"
saludar(   # falta paréntesis o argumento
