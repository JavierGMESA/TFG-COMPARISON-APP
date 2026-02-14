import tkinter as tk
from tkinter import ttk
import ficheros
import sistema

#def run_simulation():
#    n_instr = int(entry_instr.get())
#    proto = combo_proto.get()
#    generate = var_generate.get()
#
#    cycles, success, fail = simulate(n_instr, proto, generate)
#
#
#    label_cycles.config(text=f"Ciclos: {cycles}")
#    label_success.config(text=f"Aciertos: {success}")
#    label_fail.config(text=f"Fallos: {fail}")

def run_generation():
    n_instr = int(entry_instr.get())
    ficheros.generate_instructions(n_instr)

def run_simulation_all():

    #n_instr = int(entry_instr.get())
    #generate = var_generate.get()

    #if generate:
    #    ficheros.generate_instructions(n_instr)

    protocolos = ["msi", "mesi", "moesi", "mess*i"]

    resultados = {}

    for proto in protocolos:
        cycles, success, fail = simulate(proto)
        resultados[proto] = (cycles, success, fail)

    mostrar_resultados(resultados)

def mostrar_resultados(resultados):

    texto = "PROTOCOLO | CICLOS | ACIERTOS | FALLOS\n"
    texto += "-"*45 + "\n"

    for proto, valores in resultados.items():
        cycles, success, fail = valores
        texto += f"{proto.upper():9} | {cycles:6} | {success:8} | {fail:6}\n"

    label_results.config(text=texto)


def simulate(PROTO):

    instr = ficheros.read_instructions()
    c_instr = [[], [], []]

    for i in range(len(instr)):
        c_instr[i % 3].append(instr[i])

    i = 0
    cicles_used = 0
    total_success = 0
    total_fail = 0

    while (len(c_instr[0]) > 0 or len(c_instr[1]) > 0 or len(c_instr[2]) > 0):
        if(len(c_instr[i % 3]) > 0):
            success, cicles, extra_op = sistema.process_instruction(c_instr[i % 3][0], i % 3, PROTO)
            cicles_used += cicles

            if success:
                total_success += 1
            else:
                total_fail += 1

            if not extra_op:
                c_instr[i % 3].pop(0)

        i += 1
    
    sistema.restart()

    #print(PROTO)            #DEBUG

    return cicles_used, total_success, total_fail


# --- GUI ---
#Creamos la GUI esencial
root = tk.Tk()
root.title("Simulador de Protocolos de Coherencia")

tk.Label(root, text="Número de instrucciones:").pack() #Texto para indicar el nº de instrucciones
#Caja para indicar el nº de instrucciones a ejecutar
entry_instr = tk.Entry(root)
entry_instr.insert(0, "5001")     #Valor por defecto 5001
entry_instr.pack()

tk.Button(root, text="Generar Instrucciones", command=run_generation).pack(pady=10)

#tk.Label(root, text="Protocolo:").pack()
#combo_proto = ttk.Combobox(root, values=["msi", "mesi", "moesi", "mess*i"])
#combo_proto.current(2)
#combo_proto.pack()

#var_generate = tk.BooleanVar()
#tk.Checkbutton(root, text="Generar nuevas instrucciones", variable=var_generate).pack()

tk.Button(root, text="Ejecutar simulación", command=run_simulation_all).pack(pady=10)

#label_cycles = tk.Label(root, text="Ciclos: -")
#label_cycles.pack()

#label_success = tk.Label(root, text="Aciertos: -")
#label_success.pack()

#label_fail = tk.Label(root, text="Fallos: -")
#label_fail.pack()

label_results = tk.Label(root, text="", font=("Courier", 10), justify="left")
label_results.pack()


root.mainloop()
