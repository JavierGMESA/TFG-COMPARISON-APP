# Módulo "ficheros" encargado de la generación de instrucciones, su guardado en disco y su lectura posterior
import random

# Lee las instrucciones del fichero "instrucciones.txt" y las devuelve en forma de lista de diccionarios
def read_instructions() -> list:
    instr: list
    instr = []

    file = open("instrucciones.txt", "r")
    for line in file:
        line = line.strip()
        operands = line.split(" ")
        instr.append(dict(op=operands[0], dir=int(operands[1]), lat1=int(operands[2]), lat2=int(operands[3])))

    file.close()
    return instr

# Genera el nº de instrucciones que se desea por parámetros de manera aleatoria y las guarda en el fichero "instrucciones.txt".
# Las instrucciones pueden ser de lectura o escritura, influir en la dirección 0 o 1 de la memoria, y dar más o menos latencia
# al resto de procesadores que no están ejecutando dicha instrucción.
def generate_instructions(N_INSTR: int):
    file = open("instrucciones.txt", "w")
    
    for i in range(N_INSTR):
        op = ""
        if random.randint(0, 1) == 0:
            op = "r"
        else:
            op = "w"
        dir = random.randint(0, 1)
        # La latencia de cada procesador siempre son entre 0 y 4 ciclos ambos incluidos
        lat1 = random.randint(0, 4)
        lat2 = random.randint(0, 4)
        
        if(i != N_INSTR - 1):
            file.write(op + " " + str(dir) + " " + str(lat1) + " " + str(lat2) + '\n')
        else:
            file.write(op + " " + str(dir) + " " + str(lat1) + " " + str(lat2))
    
    file.close()