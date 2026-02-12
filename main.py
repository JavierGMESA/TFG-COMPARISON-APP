import ficheros

if __name__ == "__main__":
    instr = ficheros.read_instructions()
    for ins in instr:
        print(ins)
