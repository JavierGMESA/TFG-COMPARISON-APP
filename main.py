import ficheros
import sistema

N_INSTR = 8
PROTO = "mess*i"

if __name__ == "__main__":
    c_instr: list
    c_instr = [[], [], []]

    cicles = 0
    cicles_used = 0
    success = False
    total_success = 0
    total_fail = 0
    extra_op = False

    #ficheros.generate_instructions(N_INSTR)
    instr = ficheros.read_instructions()
    for i in range(len(instr)):

        print(instr[i])                 #DEBUG

        c_instr[i % 3].append(instr[i])

    print()

    i = 0
    while (len(c_instr[0]) > 0 or len(c_instr[1]) > 0 or len(c_instr[2]) > 0):
        if(len(c_instr[i % 3]) > 0):
            print(f"{(i % 3) + 1}: {c_instr[i % 3][0]}")
            success, cicles, extra_op = sistema.process_instruction(c_instr[i % 3][0], i % 3, PROTO)
            cicles_used += cicles
            if(success):
                total_success += 1
            else:
                total_fail += 1
            if(not extra_op):
                c_instr[i % 3].pop(0)
            else:
                print("Ha habido WB")   #DEBUG
            print()
            
        i += 1

    print(f"Utilizando el protocolo {PROTO} se han utilizado {cicles_used} ciclos para la ejecucion de {N_INSTR} instrucciones")
    print(f"Han habido {total_success} aciertos de caché y {total_fail} fallos de caché")
        

    
