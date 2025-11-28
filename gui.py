import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import sys
import os

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from lexico import lexer, errores_lexicos, tokens
    import main
    from main import errores_sintacticos, errores_semanticos, advertencias_semanticas, analizar_desde_gui
except ImportError as e:
    print(f"Error importando módulos: {e}")
    sys.exit(1)

from datetime import datetime


class AnalizadorRubyGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Analizador Ruby - Sistema Completo")
        self.root.geometry("1400x800")

        # Estilo
        style = ttk.Style()
        style.theme_use('clam')

        # Frame principal
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Frame superior - Editor
        editor_frame = ttk.LabelFrame(main_frame, text="📝 Editor de Código Ruby", padding=10)
        editor_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=(0, 10))

        # Área de texto para código
        self.code_text = scrolledtext.ScrolledText(
            editor_frame,
            wrap=tk.WORD,
            height=15,
            font=("Courier New", 10),
            bg="#f5f5f5"
        )
        self.code_text.pack(fill=tk.BOTH, expand=True)

        # Frame de botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))

        # Botón Analizar
        analyze_btn = ttk.Button(
            button_frame,
            text="🔍 Analizar Código",
            command=self.analizar_codigo
        )
        analyze_btn.pack(side=tk.LEFT, padx=5)

        # Botón Limpiar
        clear_btn = ttk.Button(
            button_frame,
            text="🗑️  Limpiar",
            command=self.limpiar
        )
        clear_btn.pack(side=tk.LEFT, padx=5)

        # Frame para resultados - UNA SOLA VENTANA
        results_frame = ttk.LabelFrame(main_frame, text="📊 Resultados del Análisis Completo", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True)

        # Una única área de texto para todos los resultados
        self.resultados_text = scrolledtext.ScrolledText(
            results_frame,
            wrap=tk.WORD,
            height=20,
            font=("Courier New", 9),
            bg="#f0f0f0"
        )
        self.resultados_text.pack(fill=tk.BOTH, expand=True)

    def limpiar_errores_globales(self):
        """Limpia los errores globales de los módulos"""
        errores_lexicos.clear()
        errores_sintacticos.clear()
        errores_semanticos.clear()
        advertencias_semanticas.clear()

    def analizar_codigo(self):
        """Ejecuta el análisis completo del código"""
        codigo = self.code_text.get("1.0", tk.END).strip()

        if not codigo:
            messagebox.showwarning("Advertencia", "Por favor ingresa código Ruby para analizar")
            return

        # Limpiar errores previos
        self.limpiar_errores_globales()
        self.resultados_text.delete("1.0", tk.END)
        self.root.update()  # Actualizar la GUI para mostrar que está procesando

        try:
            # Realizar análisis completo
            resultado_completo = self.realizar_analisis_completo(codigo)
            self.resultados_text.insert("1.0", resultado_completo)

        except Exception as e:
            import traceback
            error_detallado = f"Error durante el análisis:\n{str(e)}\n\n{traceback.format_exc()}"
            messagebox.showerror("Error", error_detallado)

    def realizar_analisis_completo(self, codigo):
        """Realiza el análisis completo (léxico, sintáctico, semántico)"""
        resultado = ""

        # ========== ANÁLISIS LÉXICO ==========
        resultado += "=" * 70 + "\n"
        resultado += "ANÁLISIS LÉXICO\n"
        resultado += "=" * 70 + "\n\n"

        try:
            # Reinicializar lexer completamente
            lexer.lineno = 1
            lexer.lexpos = 0
            lexer.input(codigo)

            tokens_encontrados = []
            while True:
                tok = lexer.token()
                if not tok:
                    break
                tokens_encontrados.append({
                    'tipo': tok.type,
                    'valor': tok.value,
                    'linea': tok.lineno
                })

            # Mostrar tokens encontrados (opcional)
            resultado += f"✅ Se encontraron {len(tokens_encontrados)} tokens\n"

        except Exception as e:
            resultado += f"❌ Error en análisis léxico: {str(e)}\n"
            return resultado

        # Verificar errores léxicos
        if errores_lexicos:
            resultado += "❌ ERRORES LÉXICOS ENCONTRADOS:\n"
            for error in errores_lexicos:
                resultado += f"   - {error}\n"
            resultado += "\n⚠️ No se continúa con análisis sintáctico debido a errores léxicos.\n"
            return resultado
        else:
            resultado += "✅ Análisis léxico válido\n"

        # ========== ANÁLISIS SINTÁCTICO ==========
        resultado += "\n" + "=" * 70 + "\n"
        resultado += "ANÁLISIS SINTÁCTICO\n"
        resultado += "=" * 70 + "\n\n"

        try:
            # Usar la función del main para análisis sintáctico
            resultado_parser = analizar_desde_gui(codigo)

            if errores_sintacticos:
                resultado += "❌ ERRORES SINTÁCTICOS DETECTADOS:\n"
                for error in errores_sintacticos:
                    resultado += f"   - {error}\n"
            else:
                resultado += "✅ Estructura sintáctica válida\n"

        except Exception as e:
            resultado += f"❌ Error durante análisis sintáctico: {str(e)}\n"
            if errores_sintacticos:
                for error in errores_sintacticos:
                    resultado += f"   - {error}\n"

        # ========== ANÁLISIS SEMÁNTICO ==========
        resultado += "\n" + "=" * 70 + "\n"
        resultado += "ANÁLISIS SEMÁNTICO\n"
        resultado += "=" * 70 + "\n\n"

        if errores_semanticos:
            resultado += "❌ ERRORES SEMÁNTICOS DETECTADOS:\n"
            for error in errores_semanticos:
                resultado += f"   - {error}\n"
        else:
            resultado += "✅ Análisis semántico válido\n"

        if advertencias_semanticas:
            resultado += "\n⚠️ ADVERTENCIAS SEMÁNTICAS:\n"
            for advertencia in advertencias_semanticas:
                resultado += f"   - {advertencia}\n"

        # ========== RESUMEN FINAL ==========
        resultado += "\n" + "=" * 70 + "\n"
        resultado += "RESUMEN FINAL\n"
        resultado += "=" * 70 + "\n\n"

        num_errores_lexicos = len(errores_lexicos)
        num_errores_sintacticos = len(errores_sintacticos)
        num_errores_semanticos = len(errores_semanticos)
        num_advertencias = len(advertencias_semanticas)

        resultado += f"📋 Errores Léxicos:      {num_errores_lexicos}\n"
        resultado += f"📋 Errores Sintácticos:  {num_errores_sintacticos}\n"
        resultado += f"📋 Errores Semánticos:   {num_errores_semanticos}\n"
        resultado += f"⚠️  Advertencias:         {num_advertencias}\n"

        total_errores = num_errores_lexicos + num_errores_sintacticos + num_errores_semanticos

        resultado += "\n" + "-" * 70 + "\n"

        if total_errores == 0 and num_advertencias == 0:
            resultado += "✅ ¡ANÁLISIS EXITOSO! El código es válido.\n"
        elif total_errores == 0:
            resultado += f"⚠️  CÓDIGO VÁLIDO pero con {num_advertencias} advertencia(s).\n"
        else:
            resultado += f"❌ SE ENCONTRARON {total_errores} ERROR(ES) en el análisis.\n"

        resultado += "-" * 70 + "\n"

        return resultado

    def limpiar(self):
        """Limpia el editor y los resultados"""
        self.code_text.delete("1.0", tk.END)
        self.resultados_text.delete("1.0", tk.END)
        self.limpiar_errores_globales()


def ejecutar_gui():
    root = tk.Tk()
    app = AnalizadorRubyGUI(root)
    root.mainloop()


if __name__ == "__main__":
    ejecutar_gui()