# Algoritmo Complejo: Sistema de Gestión de Productos
# Demostrando validaciones semánticas avanzadas

# Declaración de constantes
IMPUESTO = 0.21
DESCUENTO_MAYOR = 0.15
NOMBRE_EMPRESA = "TiendaRuby"

# Inicialización de variables
cantidad = 5
precio_unitario = 25.50
descripcion = "Producto Premium"

# Operaciones válidas
precio_total = precio_unitario * cantidad
impuesto_calculado = precio_total * IMPUESTO

# Concatenación válida
mensaje = NOMBRE_EMPRESA + " - " + descripcion

# Conversión explícita válida (string 100% numérico)
cantidad_texto = "10"
cantidad_convertida = cantidad_texto.to_i
total_cantidad = cantidad + cantidad_convertida

# Operación válida con conversión explícita
precio_descuento_texto = "150.75"
precio_descuento = precio_descuento_texto.to_f
precio_final = precio_descuento - impuesto_calculado

# ---------- ERRORES SEMÁNTICOS A DETECTAR ----------

# Error 1: Casting indebido - string no numérico a integer
usuario = "Juan"
id_usuario = usuario.to_i  # ADVERTENCIA: casting indebido, "Juan" no es numérico

# Error 2: Operación inválida - string + integer (sin conversión)
resultado_invalido = "Cantidad: " + cantidad

# Error 3: Casting indebido - string con espacios y caracteres
codigo_producto = "PROD-001-ABC"
codigo_numerico = codigo_producto.to_i  # ADVERTENCIA: contiene caracteres no numéricos

# Error 4: Operación aritmética con string
costo_erroneo = "100" - 20  # ERROR: operación no permitida

# Error 5: Conversión inválida de string mixto a float
valor_mixto = "3.14px"
valor_convertido = valor_mixto.to_f  # ADVERTENCIA: contiene caracteres no numéricos

# Operación válida con conversión segura
temperatura_texto = "25.5"
temperatura = temperatura_texto.to_f
temperatura_aumentada = temperatura + 5.0

# Declaración de función con validaciones
def calcular_precio_final(cantidad_str, precio_str)
  cantidad_val = cantidad_str.to_i
  precio_val = precio_str.to_f
  
  # Operación válida dentro de función
  total = cantidad_val * precio_val
  
  return total
end

# Llamada a función
precio_articulo = "45.99"
cantidad_articulos = "3"
monto_total = calcular_precio_final(cantidad_articulos, precio_articulo)

# Bucle con conversiones
contador = 0
datos = ["100", "200", "300"]
for item in datos
  valor_numerico = item.to_i
  contador = contador + valor_numerico
end

# Condicional con conversiones
numero_texto = "42"
numero = numero_texto.to_i
if numero > 40
  puts "Número válido"
end

resultado_final = usuario + " compró " + descripcion

# Validación exitosa: Todas las operaciones posteriores
resumen = "Total: " + precio_total.to_s
