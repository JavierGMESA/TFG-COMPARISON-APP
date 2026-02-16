import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import Optional
import ficheros
import nuevo_sistema as sistema

canvas1: Optional[FigureCanvasTkAgg]
canvas1 = None
canvas2: Optional[FigureCanvasTkAgg]
canvas2 = None

DEBUG = False       # Variable para activar ciertas instrucciones de depuración

if(DEBUG):
    sistema.DEBUG = True

#def mostrar_resultados(resultados):
#
#    texto = "PROTOCOLO | CICLOS | ACIERTOS | FALLOS\n"
#    texto += "-"*45 + "\n"
#
#    for proto, valores in resultados.items():
#        cycles, success, fail = valores
#        texto += f"{proto.upper():9} | {cycles:6} | {success:8} | {fail:6}\n"
#
#    label_results.config(text=texto)



# Genera nuevas instrucciones llamando a la función del módulo ficheros
def run_generation():
    n_instr = int(entry_instr.get())
    ficheros.generate_instructions(n_instr)
    label_instructions.config(text=f"Intrucciones generadas")

# Hace una simulación completa con todos los protocolos, obtiene los resultado y llama a la función de generar gráficas
def run_simulation_all():
    counter = var_counter.get()

    label_instructions.config(text=f"")

    protocols = ["msi", "mesi", "moesi", "mess*i"]

    results = {}
    cycles_graphics = []
    success_graphics = []

    for proto in protocols:
        cycles, success, fail = simulate(proto, counter)
        results[proto] = (cycles, success, fail)
        cycles_graphics.append(cycles)
        success_graphics.append(success / (success + fail) * 100)
    
    protocols_M = ["MSI", "MESI", "MOESI", "MESS*I"]

    mostrar_graficas(protocols_M, cycles_graphics, success_graphics)

# Muestra las gráficas dentro de la GUI
def mostrar_graficas(protocols: list, cycles: list, success: list):
    
    global canvas1
    global canvas2

    if canvas1 is not None:
        canvas1.get_tk_widget().destroy()
    if canvas2 is not None:
        canvas2.get_tk_widget().destroy()

    # Primera gráfica (ciclos según el protocolo)
    fig1, ax1 = plt.subplots(figsize=(7, 4))

    # Título y significado de los ejes
    ax1.set_title("Comparación de ciclos usados por protocolo (menos es mejor)")
    ax1.set_xlabel("Protocolo")
    ax1.set_ylabel("Ciclos")

    # La gráfica será de barras (se asginan los datos, color y valores)
    bars1 = ax1.bar(protocols, cycles, width=0.5, color='#4c72b0')
    ax1.bar_label(bars1, labels=[str(c) for c in cycles], padding=1)

    # Colores de fondo
    fig1.patch.set_facecolor('#f3f3f3')
    ax1.set_facecolor('#f3f3f3')

    # Se elimina el marco
    for spine in ax1.spines.values():
        spine.set_visible(False)

    # Segunda gráfica (porcentaje de acierto según el protocolo)
    fig2, ax2 = plt.subplots(figsize=(7, 4))

    # Título y significado de los ejes
    ax2.set_title("Comparación de porcentaje de acierto por protocolo (más es mejor)")
    ax2.set_xlabel("Protocolo")
    ax2.set_ylabel("Porcentaje aciertos")

    # La gráfica será de barras (se asginan los datos, color y valores)
    bars2 = ax2.bar(protocols, success, width=0.5, color='#55a868')
    ax2.bar_label(bars2, labels=[f"{s:.1f}%" for s in success], padding=1)

    # Colores de fondo
    fig2.patch.set_facecolor('#f3f3f3')
    ax2.set_facecolor('#f3f3f3')

    # Se elimina el marco
    for spine in ax2.spines.values():
        spine.set_visible(False)

    # Se pintan las gráficas
    canvas1 = FigureCanvasTkAgg(fig1, master=frame_graphics)
    canvas1.draw()
    canvas1.get_tk_widget().pack(side=tk.LEFT, padx=5)

    canvas2 = FigureCanvasTkAgg(fig2, master=frame_graphics)
    canvas2.draw()
    canvas2.get_tk_widget().pack(side=tk.LEFT, padx=5)

# Hace la simulación completa con uno de los protocolos utilizando las instrucciones leídas del fichero "instrucciones.txt"
def simulate(PROTO: str, counter: bool):

    instr = ficheros.read_instructions()
    c_instr: list
    c_instr = [[], [], []]

    for i in range(len(instr)):
        c_instr[i % 3].append(instr[i])

    system = sistema.CoherenceSystem()
    system.restart()

    i = 0
    cicles_used = 0
    total_success = 0
    total_fail = 0

    while (len(c_instr[0]) > 0 or len(c_instr[1]) > 0 or len(c_instr[2]) > 0):
        if(len(c_instr[i % 3]) > 0):
            # Se comprueba si el usuario marcó la opción de utilizar contadores en el protocolo MESS*I
            if(counter):
                success, cycles, extra_op = system.process_instruction(c_instr[i % 3][0], i % 3, PROTO)
                #success, cycles, extra_op = sistema.process_instruction(c_instr[i % 3][0], i % 3, PROTO)
            else:
                success, cycles, extra_op = system.process_instruction_no_counter(c_instr[i % 3][0], i % 3, PROTO)
                #success, cycles, extra_op = sistema.process_instruction_no_counter(c_instr[i % 3][0], i % 3, PROTO)
            cicles_used += cycles

            if success:
                total_success += 1
            else:
                total_fail += 1

            if not extra_op:
                c_instr[i % 3].pop(0)

        i += 1
    
    system.restart()
    #sistema.restart()

    if(DEBUG):
        print(PROTO)

    return cicles_used, total_success, total_fail

# Creamos la GUI en sí
root = tk.Tk()
root.title("Simulador de Protocolos de Coherencia")
root.configure(bg="#f3f3f3")
root.geometry("1500x720")

# Texto para la opción del nº de instrucciones
tk.Label(root, text="Número de instrucciones:", bg="#f3f3f3").pack()
# Caja para indicar el nº de instrucciones a generar
entry_instr = tk.Entry(root)
entry_instr.insert(0, "5001")     #Valor por defecto 5001
entry_instr.pack()

# Botón para generar instrucciones
tk.Button(root, text="Generar Instrucciones", command=run_generation).pack(pady=10)
# Texto para indicar que se han generado instrucciones
label_instructions = tk.Label(root, text="", bg="#f3f3f3")
label_instructions.pack()

# Casilla para marcar si se desea utilizar contadores con MESS*I
var_counter = tk.BooleanVar()
tk.Checkbutton(root, text="Añadir contadores en MESS*I", variable=var_counter, bg="#f3f3f3", highlightthickness=0, bd=0).pack()     # Los últimos parámetros son para quitar el marco

# Botón para comenzar la simulación completa
tk.Button(root, text="Ejecutar simulación", command=run_simulation_all).pack(pady=10)

#label_results = tk.Label(root, text="", font=("Courier", 10), justify="left", bg="#f3f3f3")
#label_results.pack()

# Frame aparte para colocar las gráficas correctamente
frame_graphics = tk.Frame(root, bg="#f3f3f3")
frame_graphics.pack(pady=10)

# Para activar los eventos de la GUI (que permanezca activa)
root.mainloop()
