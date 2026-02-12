import random

N_INSTR = 5001

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

def generate_instructions():
    file = open("instrucciones.txt", "w")
    
    for i in range(N_INSTR):
        op = ""
        if random.randint(0, 1) == 0:
            op = "r"
        else:
            op = "w"
        dir = random.randint(0, 1)
        lat1 = random.randint(0, 4)
        lat2 = random.randint(0, 4)
        
        if(i != N_INSTR - 1):
            file.write(op + " " + str(dir) + " " + str(lat1) + " " + str(lat2) + '\n')
        else:
            file.write(op + " " + str(dir) + " " + str(lat1) + " " + str(lat2))
    
    file.close()