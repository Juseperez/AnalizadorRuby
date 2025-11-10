import ply.yacc as yacc
from lexico import tokens
import os
import datetime


errores_sintacticos = []
def p_expresion_suma(p):
    'expresion : valor PLUS valor'
    print("Reconocida una suma válida:", p[1], "+", p[3])
    p[0] = p[1] + p[3] if isinstance(p[1], (int, float)) and isinstance(p[3], (int, float)) else None

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

    opcion = input("Ingrese su opción: ").strip()

    if opcion == "1":
        analizar_sintaxis("algoritmo1E.rb", "emrubio85")
    elif opcion == "2":
        analizar_sintaxis("algoritmo2B.rb", "BrayanBriones")
    elif opcion == "3":
        analizar_sintaxis("algoritmo3J.rb", "Juseperez")
    else:
        print("Opción no válida.")