# Módulo "sistema" con las funciones para simular una instrucción dentro de un sistema de tres cachés, cada una de 5 bits
# donde los 4 menos significativos es el bloque en sí y el bit más significativo es la etiqueta.
import random

DEBUG = False

class CoherenceSystem:
    def __init__(self):
        self.cache_data = [0x00, 0x00, 0x00]
        self.states = [0, 0, 0]
        self.ram = [0xb, 0x4]

    # Método público
    def restart(self):
        for i in range(3):
            self.cache_data[i] = 0x00
            self.states[i] = 0
        self.ram[0] = 0xb
        self.ram[1] = 0x4

    # Método privado
    def BusRd(self, op: dict, c_n: int, proto: str) -> tuple[int, int, int]:
        cycles_used = 0

        oc1_n = 0
        oc2_n = 0
        oc1_has = False
        oc2_has = False
        oc1_sta = 0
        oc2_sta = 0

        data = 0x0
        state = 0

        if((c_n - 1) % 3 < (c_n + 1) % 3):
            oc1_n = (c_n - 1) % 3
            oc2_n = (c_n + 1) % 3
        else:
            oc2_n = (c_n - 1) % 3
            oc1_n = (c_n + 1) % 3
        
        oc1_has = op["dir"] == (self.cache_data[oc1_n] >> 4) and self.states[oc1_n] > 0
        oc2_has = op["dir"] == (self.cache_data[oc2_n] >> 4) and self.states[oc2_n] > 0
        oc1_sta = self.states[oc1_n]
        oc2_sta = self.states[oc2_n]

        if(not oc1_has and not oc2_has):
            cycles_used = 48
            data = self.ram[op["dir"]]
            state = 1 if proto != "msi" else 2
        elif(not oc2_has):
            data = self.cache_data[oc1_n] & 0xf
            if(oc1_sta < 3):
                cycles_used = 11 + op["lat1"]
                state = 2
                self.states[oc1_n] = 2               #Lo ponemos en estado Shared en caso de que estuviera en Exclusive
            else:
                if(proto == "msi" or proto == "mesi"):
                    cycles_used = 48
                    state = 2
                    self.states[oc1_n] = 2           #Lo ponemos en estado Shared a consecuencia del WB
                    self.ram[op["dir"]] = data       #Actualizamos la self.ram debido al WB
                elif(proto == "moesi"):
                    cycles_used = 11 + op["lat1"]
                    state = 2
                    self.states[oc1_n] = 4           #Si no está en estado Owner lo colocamos
                else:
                    cycles_used = 11 + op["lat1"]
                    state = 4
                    self.states[oc1_n] = 4           #Lo ponemos en estado Shared*
        elif(not oc1_has):
            data = self.cache_data[oc2_n] & 0xf
            if(oc2_sta < 3):
                cycles_used = 11 + op["lat2"]
                state = 2
                self.states[oc2_n] = 2
            else:
                if(proto == "msi" or proto == "mesi"):
                    cycles_used = 48
                    state = 2
                    self.states[oc2_n] = 2
                    self.ram[op["dir"]] = data
                elif(proto == "moesi"):
                    cycles_used = 11 + op["lat2"]
                    state = 2
                    self.states[oc2_n] = 4
                else:
                    cycles_used = 11 + op["lat2"]
                    state = 4
                    self.states[oc2_n] = 4
        else:
            data = self.cache_data[oc1_n] & 0xf
            if(oc1_sta < 3 and oc2_sta < 3):
                cycles_used = 11 + min(op["lat1"], op["lat2"])
                state = 2
            elif(oc1_sta >= 3 and oc2_sta >= 3):
                if(proto == "msi" or proto == "mesi"):
                    raise ValueError("proto es msi o mesi pero hay dos caches compartiendo un bloque dirty")
                elif(proto == "moesi"):
                    raise ValueError("proto es moesi pero hay dos caches con un mismo bloque en estado Modified u Owner")
                else:
                    cycles_used = 11 + min(op["lat1"], op["lat2"])
                    state = 4
            elif(oc1_sta >= 3):
                if(proto == "msi" or proto == "mesi"):
                    raise ValueError("proto es msi o mesi pero hay dos caches compartiendo un bloque dirty")
                elif(proto == "moesi"):
                    cycles_used = 11 + op["lat1"]
                    state = 2
                    self.states[oc1_n] = 4
                else:
                    raise ValueError("proto es mess*i y hay dos caches compartiendo un bloque dirty pero solo una está en Modified o Shared*")
            else:
                if(proto == "msi" or proto == "mesi"):
                    raise ValueError("proto es msi o mesi pero hay dos caches compartiendo un bloque dirty")
                elif(proto == "moesi"):
                    cycles_used = 11 + op["lat2"]
                    state = 2
                    self.states[oc2_n] = 4
                else:
                    raise ValueError("proto es mess*i y hay dos caches compartiendo un bloque dirty pero solo una está en Modified o Shared*")        
        
        return cycles_used, data, state

    # Método privado
    def BusRdX(self, op: dict, c_n: int, proto: str) -> tuple[int, int]:
        cycles_used = 0
        state = 3

        oc1_n = 0
        oc2_n = 0
        oc1_has = False
        oc2_has = False
        oc1_sta = 0
        oc2_sta = 0

        if((c_n - 1) % 3 < (c_n + 1) % 3):
            oc1_n = (c_n - 1) % 3
            oc2_n = (c_n + 1) % 3
        else:
            oc2_n = (c_n - 1) % 3
            oc1_n = (c_n + 1) % 3
        
        oc1_has = op["dir"] == (self.cache_data[oc1_n] >> 4) and self.states[oc1_n] > 0
        oc2_has = op["dir"] == (self.cache_data[oc2_n] >> 4) and self.states[oc2_n] > 0
        oc1_sta = self.states[oc1_n]
        oc2_sta = self.states[oc2_n]

        if(not oc1_has and not oc2_has):
            cycles_used = 48
        elif(not oc2_has):
            if(oc1_sta < 3):
                cycles_used = 11 + op["lat1"]
            else:
                if(proto == "msi" or proto == "mesi"):
                    cycles_used = 48
                    self.ram[op["dir"]] = self.cache_data[oc1_n] & 0xf
                else:
                    cycles_used = 11 + op["lat1"]
            self.states[oc1_n] = 0
        elif(not oc1_has):
            if(oc2_sta < 3):
                cycles_used = 11 + op["lat2"]
            else:
                if(proto == "msi" or proto == "mesi"):
                    cycles_used = 48
                    self.ram[op["dir"]] = self.cache_data[oc2_n] & 0xf
                else:
                    cycles_used = 11 + op["lat2"]
            self.states[oc2_n] = 0
        else:
            if(oc1_sta < 3 and oc2_sta < 3):
                cycles_used = 11 + min(op["lat1"], op["lat2"])  
            elif(oc1_sta >= 3 and oc2_sta >= 3):
                if(proto == "msi" or proto == "mesi"):
                    raise ValueError("proto es msi o mesi pero hay dos caches compartiendo un bloque dirty")
                elif(proto == "moesi"):
                    raise ValueError("proto es moesi pero hay dos caches con un mismo bloque en estado Modified u Owner")
                else:
                    cycles_used = 11 + min(op["lat1"], op["lat2"])
            elif(oc1_sta >= 3):
                if(proto == "msi" or proto == "mesi"):
                    raise ValueError("proto es msi o mesi pero hay dos caches compartiendo un bloque dirty")
                elif(proto == "moesi"):
                    cycles_used = 11 + op["lat1"]
                else:
                    raise ValueError("proto es mess*i y hay dos caches compartiendo un bloque dirty pero solo una está en Modified o Shared*")
            else:
                if(proto == "msi" or proto == "mesi"):
                    raise ValueError("proto es msi o mesi pero hay dos caches compartiendo un bloque dirty")
                elif(proto == "moesi"):
                    cycles_used = 11 + op["lat2"]
                else:
                    raise ValueError("proto es mess*i y hay dos caches compartiendo un bloque dirty pero solo una está en Modified o Shared*")  
            self.states[oc1_n] = self.states[oc2_n] = 0

        return cycles_used, state

    # Método privado
    def BusUpgr(self, op: dict, c_n: int) -> tuple[int, int]:
        cycles_used = 7
        state = 3

        oc1_has = op["dir"] == (self.cache_data[(c_n - 1) % 3] >> 4) and self.states[(c_n - 1) % 3] > 0
        oc2_has = op["dir"] == (self.cache_data[(c_n + 1) % 3] >> 4) and self.states[(c_n + 1) % 3] > 0

        if(oc1_has):
            self.states[(c_n - 1) % 3] = 0
        if(oc2_has):
            self.states[(c_n + 1) % 3] = 0

        return cycles_used, state
        
    # Método privado
    def BusWB(self, op: dict, c_n: int) -> tuple[int, int]:
        cycles_used = 45
        state = 2

        self.ram[op["dir"]] = self.cache_data[c_n] & 0xf

        return cycles_used, state

    # Método privado
    def BusWB_no_counter(self, op: dict, c_n: int, proto: str) -> tuple[int, int]:
        cycles_used = 45
        state = 2

        self.ram[op["dir"]] = self.cache_data[c_n] & 0xf

        if(proto == "mess*i"):
            if ((self.cache_data[c_n] >> 4) == (self.cache_data[(c_n - 1) % 3] >> 4) and self.states[(c_n - 1) % 3] == 4):
                self.states[(c_n - 1) % 3] = 2
            if ((self.cache_data[c_n] >> 4) == (self.cache_data[(c_n + 1) % 3] >> 4) and self.states[(c_n + 1) % 3] == 4):
                self.states[(c_n + 1) % 3] = 2

        return cycles_used, state

    # Método público
    def process_instruction(self, op: dict, c_n: int, proto: str) -> tuple[bool, int, bool]:
        cache_success = False
        cycles_used = 0
        extra_op = False

        if(op["op"] == 'r'):
            if(op["dir"] == (self.cache_data[c_n] >> 4)):
                if(self.states[c_n] > 0):
                    cache_success = True
                    cycles_used += 3
                else:
                    cycles_used, data, state = self.BusRd(op, c_n, proto)
                    self.cache_data[c_n] = (op["dir"] << 4) | data
                    self.states[c_n] = state
            else:
                if(self.states[c_n] < 3):
                    cycles_used, data, state = self.BusRd(op, c_n, proto)
                    self.cache_data[c_n] = (op["dir"] << 4) | data
                    self.states[c_n] = state
                elif(self.states[c_n] == 3):
                    cycles_used, state = self.BusWB(op, c_n)
                    self.states[c_n] = state
                    extra_op = True
                else:
                    if((self.cache_data[(c_n - 1) % 3] == self.cache_data[c_n] and self.states[(c_n - 1) % 3] == 4) or (self.cache_data[(c_n + 1) % 3] == self.cache_data[c_n] and self.states[(c_n + 1) % 3] == 4)):
                        cycles_used, data, state = self.BusRd(op, c_n, proto)
                        self.cache_data[c_n] = (op["dir"] << 4) | data
                        self.states[c_n] = state
                    else:
                        cycles_used, state = self.BusWB(op, c_n)
                        self.states[c_n] = state
                        extra_op = True
        else:
            data = (random.randint(0, 15) & 0xf)
            if(op["dir"] == (self.cache_data[c_n] >> 4)):
                if(self.states[c_n] == 0):
                    cycles_used, state = self.BusRdX(op, c_n, proto)
                    self.cache_data[c_n] = (op["dir"] << 4) | data
                    self.states[c_n] = state
                elif(self.states[c_n] == 1 or self.states[c_n] == 3):
                    cache_success = True
                    cycles_used = 3
                    self.cache_data[c_n] = (op["dir"] << 4) | data
                    self.states[c_n] = 3
                else:
                    cache_success = True
                    cycles_used, state = self.BusUpgr(op, c_n)
                    self.cache_data[c_n] = (op["dir"] << 4) | data
                    self.states[c_n] = state
            else:
                if(self.states[c_n] < 3):
                    cycles_used, state = self.BusRdX(op, c_n, proto)
                    self.cache_data[c_n] = (op["dir"] << 4) | data
                    self.states[c_n] = state
                elif(self.states[c_n] == 3):
                    cycles_used, state = self.BusWB(op, c_n)
                    self.states[c_n] = state
                    extra_op = True
                else:
                    if((self.cache_data[(c_n - 1) % 3] == self.cache_data[c_n] and self.states[(c_n - 1) % 3] == 4) or (self.cache_data[(c_n + 1) % 3] == self.cache_data[c_n] and self.states[(c_n + 1) % 3] == 4)):
                        cycles_used, state = self.BusRdX(op, c_n, proto)
                        self.cache_data[c_n] = (op["dir"] << 4) | data
                        self.states[c_n] = state
                    else:
                        cycles_used, state = self.BusWB(op, c_n)
                        self.states[c_n] = state
                        extra_op = True

        if(DEBUG):
            states_str: list
            states_str = ["", "", ""]
            for i in range(3):
                if(self.states[i] == 0):
                    states_str[i] = "I"
                elif(self.states[i] == 1):
                    states_str[i] = "E"
                elif(self.states[i] == 2):
                    states_str[i] = "S"
                elif(self.states[i] == 3):
                    states_str[i] = "M"
                elif(self.states[i] == 4 and proto == "moesi"):
                    states_str[i] = "O"
                else:
                    states_str[i] = "S*"
            print(f"Cache {c_n + 1}: {op}")
            print(f"0x{self.cache_data[0]:02x} {states_str[0]} | 0x{self.cache_data[1]:02x} {states_str[1]} | 0x{self.cache_data[2]:02x} {states_str[2]} | {hex(self.ram[1])} {hex(self.ram[0])}")
            print(f"Ciclos usados: {cycles_used}")
        
        return cache_success, cycles_used, extra_op

    # Método público
    # Misma función que la anterior pero no existe el contador para el protocolo MESS*I. Es decir, si un procesador quiere hacer un reemplazo y tanto
    # él como otros procesadores tienen el mismo bloque en estado S*, todos deberán pasar S haciendo un BusWB.
    def process_instruction_no_counter(self, op: dict, c_n: int, proto: str) -> tuple[bool, int, bool]:
        cache_success = False
        cycles_used = 0
        extra_op = False

        if(op["op"] == 'r'):
            if(op["dir"] == (self.cache_data[c_n] >> 4)):
                if(self.states[c_n] > 0):
                    cache_success = True
                    cycles_used += 3
                else:
                    cycles_used, data, state = self.BusRd(op, c_n, proto)
                    self.cache_data[c_n] = (op["dir"] << 4) | data
                    self.states[c_n] = state
            else:
                if(self.states[c_n] < 3):
                    cycles_used, data, state = self.BusRd(op, c_n, proto)
                    self.cache_data[c_n] = (op["dir"] << 4) | data
                    self.states[c_n] = state
                elif(self.states[c_n] == 3):
                    cycles_used, state = self.BusWB(op, c_n)
                    self.states[c_n] = state
                    extra_op = True
                else:
                    cycles_used, state = self.BusWB_no_counter(op, c_n, proto)
                    self.states[c_n] = state
                    extra_op = True
        else:
            data = (random.randint(0, 15) & 0xf)
            if(op["dir"] == (self.cache_data[c_n] >> 4)):
                if(self.states[c_n] == 0):
                    cycles_used, state = self.BusRdX(op, c_n, proto)
                    self.cache_data[c_n] = (op["dir"] << 4) | data
                    self.states[c_n] = state
                elif(self.states[c_n] == 1 or self.states[c_n] == 3):
                    cache_success = True
                    cycles_used = 3
                    self.cache_data[c_n] = (op["dir"] << 4) | data
                    self.states[c_n] = 3
                else:
                    cache_success = True
                    cycles_used, state = self.BusUpgr(op, c_n)
                    self.cache_data[c_n] = (op["dir"] << 4) | data
                    self.states[c_n] = state
            else:
                if(self.states[c_n] < 3):
                    cycles_used, state = self.BusRdX(op, c_n, proto)
                    self.cache_data[c_n] = (op["dir"] << 4) | data
                    self.states[c_n] = state
                elif(self.states[c_n] == 3):
                    cycles_used, state = self.BusWB(op, c_n)
                    self.states[c_n] = state
                    extra_op = True
                else:
                    cycles_used, state = self.BusWB_no_counter(op, c_n, proto)
                    self.states[c_n] = state
                    extra_op = True

        if(DEBUG):
            states_str: list
            states_str = ["", "", ""]
            for i in range(3):
                if(self.states[i] == 0):
                    states_str[i] = "I"
                elif(self.states[i] == 1):
                    states_str[i] = "E"
                elif(self.states[i] == 2):
                    states_str[i] = "S"
                elif(self.states[i] == 3):
                    states_str[i] = "M"
                elif(self.states[i] == 4 and proto == "moesi"):
                    states_str[i] = "O"
                else:
                    states_str[i] = "S*"
            print(f"Cache {c_n + 1}: {op}")
            print(f"0x{self.cache_data[0]:02x} {states_str[0]} | 0x{self.cache_data[1]:02x} {states_str[1]} | 0x{self.cache_data[2]:02x} {states_str[2]} | {hex(self.ram[1])} {hex(self.ram[0])}")
            print(f"Ciclos usados: {cycles_used}")
        
        return cache_success, cycles_used, extra_op