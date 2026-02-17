# Módulo "sistema" con las funciones para simular una instrucción dentro de un sistema de tres cachés, cada una de 5 bits
# donde los 4 menos significativos es el bloque en sí y el bit más significativo es la etiqueta.
import random

DEBUG = False

# CICLOS NECESARIOS:
# - 3 ciclos para acceder a una caché para leer/escribir un bloque
# - 1 ciclo para transmitir una operación/bloque al bus
# - 40 ciclos para acceder a memoria RAM para leer/escribir un bloque

# Datos adicionales:
# Los bloques son de 4 bits
# En los estados: 0 = I, 1 = E, 2 = S, 3 = M, 4 = O si el protocolo es MOESI, 4 = S* si el protocolo es MESS*I

class CoherenceSystem:
    def __init__(self):
        # Sistema de coherencia formado por tres procesadores, cada uno con una sola caché de 5 bits donde
        # los 4 bits menos significativos son el bloque y el bit más significativo es la etiqueta. Las memorias
        # caché solo tendrán una dirección (solo almacenan un bloque). La memoria RAM solo tendrá dos direcciones
        # (solo habrán dos bloques en todo el sistema).
        self.cache_data = [0x00, 0x00, 0x00]
        self.states = [0, 0, 0]
        self.ram = [0xb, 0x4]

    # Método público
    def restart(self):
        # Función para resetear el sistema (poner todos los valores por defecto para comenzar una nueva simulación)
        for i in range(3):
            self.cache_data[i] = 0x00
            self.states[i] = 0
        self.ram[0] = 0xb
        self.ram[1] = 0x4

    # Método privado
    def BusRd(self, op: dict, c_n: int, proto: str) -> tuple[int, int, int]:
        # En base a los datos de la operación, el procesador que la ejecuta, el protocolo y el estado del sistema 
        # devuelve los ciclos necesarios para realizar un BusRd así como el dato a escribir y el estado que debe
        # tomar el bloque.
        # La operación BusRd toma los siguientes ciclos:
        # A. 3 ciclos para leer la caché del procesador que ejecuta para comprobar el estado del bloque almacenado.
        # B. 1 ciclo para enviar la operación BusRd al bus.
        # C. 3 ciclos para leer el bloque de otras cachés si estas lo poseen. A estos 3 ciclos hay que sumar la
        # latencia del procesador que envía el bloque o el mínimo de latencia entre los procesadores que pueden
        # enviar el bloque. 
        # D. En caso de que ninguna de estas lo tenga habrá que leer el bloque de la RAM, lo cual provoca 
        # que en vez de gastar 3 ciclos se gasten 40.
        # E. 1 ciclo para transmitir el bloque por el bus.
        # F. 3 ciclos para escribir el bloque en la caché destino y actualizar su estado. 
        # G. En caso de que haya que actualizar la memoria RAM debido a que alguna caché tuviera el bloque desactualizado 
        # y el protocolo sea "msi" o "mesi" en lugar de 3 ciclos serán 40.
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

        # Ninguna de las otras cachés tiene el bloque
        if(not oc1_has and not oc2_has):
            cycles_used = 48                        # A + B + D + E + F
            data = self.ram[op["dir"]]
            state = 1 if proto != "msi" else 2
        # Solo la primera caché tiene el bloque
        elif(not oc2_has):
            data = self.cache_data[oc1_n] & 0xf
            # Tiene el bloque en estado I, E o S
            if(oc1_sta < 3):
                cycles_used = 11 + op["lat1"]       # A + B + C + E + F
                state = 2
                self.states[oc1_n] = 2              #Lo ponemos en estado Shared en caso de que estuviera en Exclusive
            # Tiene el bloque en estado M, O o S*
            else:
                if(proto == "msi" or proto == "mesi"):
                    cycles_used = 48                # A + B + C + E + G
                    state = 2
                    self.states[oc1_n] = 2          #Lo ponemos en estado Shared a consecuencia del WB
                    self.ram[op["dir"]] = data      #Actualizamos la self.ram debido al WB
                elif(proto == "moesi"):
                    cycles_used = 11 + op["lat1"]   # A + B + C + E + F
                    state = 2
                    self.states[oc1_n] = 4          #Si no está en estado Owner lo colocamos
                else:
                    cycles_used = 11 + op["lat1"]   # A + B + C + E + F
                    state = 4
                    self.states[oc1_n] = 4          #Lo ponemos en estado Shared*
        # Solo la segunda caché tiene el bloque
        elif(not oc1_has):
            data = self.cache_data[oc2_n] & 0xf
            # Tiene el bloque en estado I, E o S
            if(oc2_sta < 3):
                cycles_used = 11 + op["lat2"]       # A + B + C + E + F
                state = 2
                self.states[oc2_n] = 2
            # Tiene el bloque en estado M, O o S*
            else:
                if(proto == "msi" or proto == "mesi"):
                    cycles_used = 48                # A + B + C + E + G
                    state = 2
                    self.states[oc2_n] = 2
                    self.ram[op["dir"]] = data
                elif(proto == "moesi"):
                    cycles_used = 11 + op["lat2"]   # A + B + C + E + F
                    state = 2
                    self.states[oc2_n] = 4
                else:
                    cycles_used = 11 + op["lat2"]   # A + B + C + E + F
                    state = 4
                    self.states[oc2_n] = 4
        # Las otras dos cachés tienen el bloque
        else:
            data = self.cache_data[oc1_n] & 0xf
            # Ambas tienen el bloque en estado S
            if(oc1_sta < 3 and oc2_sta < 3):
                cycles_used = 11 + min(op["lat1"], op["lat2"])          # A + B + C + E + F
                state = 2
            # Ambas tienen el bloque en estado S*
            elif(oc1_sta >= 3 and oc2_sta >= 3):
                if(proto == "msi" or proto == "mesi"):
                    raise ValueError("proto es msi o mesi pero hay dos caches compartiendo un bloque dirty")
                elif(proto == "moesi"):
                    raise ValueError("proto es moesi pero hay dos caches con un mismo bloque en estado Modified u Owner")
                else:
                    cycles_used = 11 + min(op["lat1"], op["lat2"])      # A + B + C + E + F
                    state = 4
            # La primera caché tiene el bloque en estado O y la otra en estado S
            elif(oc1_sta >= 3):
                if(proto == "msi" or proto == "mesi"):
                    raise ValueError("proto es msi o mesi pero hay dos caches compartiendo un bloque dirty")
                elif(proto == "moesi"):
                    cycles_used = 11 + op["lat1"]                       # A + B + C + E + F
                    state = 2
                    self.states[oc1_n] = 4
                else:
                    raise ValueError("proto es mess*i y hay dos caches compartiendo un bloque dirty pero solo una está en Modified o Shared*")
            # La segunda caché tiene el bloque en estado O y la otra en estado S
            else:
                if(proto == "msi" or proto == "mesi"):
                    raise ValueError("proto es msi o mesi pero hay dos caches compartiendo un bloque dirty")
                elif(proto == "moesi"):
                    cycles_used = 11 + op["lat2"]                       # A + B + C + E + F
                    state = 2
                    self.states[oc2_n] = 4
                else:
                    raise ValueError("proto es mess*i y hay dos caches compartiendo un bloque dirty pero solo una está en Modified o Shared*")        
        
        return cycles_used, data, state

    # Método privado
    def BusRdX(self, op: dict, c_n: int, proto: str) -> tuple[int, int]:
        # En base a los datos de la operación, el procesador que la ejecuta, el protocolo y el estado del sistema 
        # devuelve los ciclos necesarios para realizar un BusRdX y el estado que debe tomar el bloque.
        # La operación BusRdX toma los siguientes ciclos:
        # A. 3 ciclos para leer la caché del procesador que ejecuta para comprobar el estado del bloque almacenado.
        # B. 1 ciclo para enviar la operación BusRdX al bus.
        # C. 3 ciclos para leer el bloque de otras cachés si estas lo poseen. A estos 3 ciclos hay que sumar la
        # latencia del procesador que envía el bloque o el mínimo de latencia entre los procesadores que pueden
        # enviar el bloque. 
        # D. En caso de que ninguna de estas lo tenga habrá que leer el bloque de la RAM, lo cual provoca 
        # que en vez de gastar 3 ciclos se gasten 40.
        # E. 1 ciclo para transmitir el bloque por el bus.
        # F. 3 ciclos para escribir el bloque actualizado en la caché destino y actualizar su estado. 
        # G. En caso de que haya que actualizar la memoria RAM debido a que alguna caché tuviera el bloque desactualizado 
        # y el protocolo sea "msi" o "mesi" en lugar de 3 ciclos serán 40.
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

        # Ninguna de las otras cachés tiene el bloque
        if(not oc1_has and not oc2_has):
            cycles_used = 48                        # A + B + D + E + F
        # Solo la primera caché tiene el bloque
        elif(not oc2_has):
            # Tiene el bloque en estado I, E o S
            if(oc1_sta < 3):
                cycles_used = 11 + op["lat1"]       # A + B + C + E + F
            # Tiene el bloque en estado M, O o S*
            else:
                if(proto == "msi" or proto == "mesi"):
                    cycles_used = 48                # A + B + C + E + G
                    self.ram[op["dir"]] = self.cache_data[oc1_n] & 0xf
                else:
                    cycles_used = 11 + op["lat1"]   # A + B + C + E + F
            self.states[oc1_n] = 0
        # Solo la segunda caché tiene el bloque
        elif(not oc1_has):
            # Tiene el bloque en estado I, E o S
            if(oc2_sta < 3):
                cycles_used = 11 + op["lat2"]       # A + B + C + E + F
            # Tiene el bloque en estado M, O o S*
            else:
                if(proto == "msi" or proto == "mesi"):
                    cycles_used = 48                # A + B + C + E + G
                    self.ram[op["dir"]] = self.cache_data[oc2_n] & 0xf
                else:
                    cycles_used = 11 + op["lat2"]   # A + B + C + E + F
            self.states[oc2_n] = 0
        # Las otras dos cachés tienen el bloque
        else:
            # Ambas tienen el bloque en estado S
            if(oc1_sta < 3 and oc2_sta < 3):
                cycles_used = 11 + min(op["lat1"], op["lat2"])          # A + B + C + E + F
            # Ambas tienen el bloque en estado S*
            elif(oc1_sta >= 3 and oc2_sta >= 3):
                if(proto == "msi" or proto == "mesi"):
                    raise ValueError("proto es msi o mesi pero hay dos caches compartiendo un bloque dirty")
                elif(proto == "moesi"):
                    raise ValueError("proto es moesi pero hay dos caches con un mismo bloque en estado Modified u Owner")
                else:
                    cycles_used = 11 + min(op["lat1"], op["lat2"])      # A + B + C + E + F
            # La primera caché tiene el bloque en estado O y la otra en estado S
            elif(oc1_sta >= 3):
                if(proto == "msi" or proto == "mesi"):
                    raise ValueError("proto es msi o mesi pero hay dos caches compartiendo un bloque dirty")
                elif(proto == "moesi"):
                    cycles_used = 11 + op["lat1"]                       # A + B + C + E + F
                else:
                    raise ValueError("proto es mess*i y hay dos caches compartiendo un bloque dirty pero solo una está en Modified o Shared*")
            # La segunda caché tiene el bloque en estado O y la otra en estado S
            else:
                if(proto == "msi" or proto == "mesi"):
                    raise ValueError("proto es msi o mesi pero hay dos caches compartiendo un bloque dirty")
                elif(proto == "moesi"):
                    cycles_used = 11 + op["lat2"]                       # A + B + C + E + F
                else:
                    raise ValueError("proto es mess*i y hay dos caches compartiendo un bloque dirty pero solo una está en Modified o Shared*")  
            self.states[oc1_n] = self.states[oc2_n] = 0

        return cycles_used, state

    # Método privado
    def BusUpgr(self, op: dict, c_n: int) -> tuple[int, int]:
        # En base a los datos de la operación, el procesador que la ejecuta y el estado del sistema 
        # devuelve los ciclos necesarios para realizar un BusUpgr y el estado que debe tomar el bloque.
        # La operación BusUpgr toma siempre 7 ciclos:
        # A. 3 ciclos para leer la caché del procesador que ejecuta para comprobar el estado del bloque almacenado.
        # B. 1 ciclo para enviar la operación BusRdX al bus.
        # C. 3 ciclos para invalidar los bloques en las otras cachés en caso de que estas compartan el bloque.
        cycles_used = 7
        state = 3

        oc1_has = op["dir"] == (self.cache_data[(c_n - 1) % 3] >> 4) and self.states[(c_n - 1) % 3] > 0
        oc2_has = op["dir"] == (self.cache_data[(c_n + 1) % 3] >> 4) and self.states[(c_n + 1) % 3] > 0

        #Se invalidan los bloques en caso de que estén presentes en las otras cachés.
        if(oc1_has):
            self.states[(c_n - 1) % 3] = 0
        if(oc2_has):
            self.states[(c_n + 1) % 3] = 0

        return cycles_used, state
        
    # Método privado
    def BusWB(self, op: dict, c_n: int) -> tuple[int, int]:
        # En base a los datos de la operación, el procesador que la ejecuta y el estado del sistema 
        # devuelve los ciclos necesarios para realizar un BusWB con contadores para el protocolo MESS*I
        # y el estado que debe tomar el bloque.
        # La operación BusWB toma siempre 44 ciclos:
        # A. 3 ciclos para leer la caché del procesador que ejecuta para comprobar el estado del bloque almacenado.
        # B. 1 ciclo para enviar la operación BusWB al bus.
        # C. 40 ciclos para actualizar la memoria RAM.
        cycles_used = 44
        state = 2

        self.ram[op["dir"]] = self.cache_data[c_n] & 0xf

        return cycles_used, state

    # Método privado
    def BusWB_no_counter(self, op: dict, c_n: int, proto: str) -> tuple[int, int]:
        # En base a los datos de la operación, el procesador que la ejecuta y el estado del sistema 
        # devuelve los ciclos necesarios para realizar un BusWB sin contadores para el protocolo MESS*I
        # y el estado que debe tomar el bloque.
        # La operación BusWB toma siempre 44 ciclos:
        # A. 3 ciclos para leer la caché del procesador que ejecuta para comprobar el estado del bloque almacenado.
        # B. 1 ciclo para enviar la operación BusWB al bus.
        # C. 40 ciclos para actualizar la memoria RAM. Durante estos ciclos también se actuliza el estado del
        # bloque en otras cachés en caso de que estas también tuvieran el bloque en estado S*
        cycles_used = 44
        state = 2

        self.ram[op["dir"]] = self.cache_data[c_n] & 0xf

        # Si estamos en el protocolo MESS*I actualizamos el estado del bloque en otras cachés en caso de que estas
        # lo tuvieran en estado S*
        if(proto == "mess*i"):
            if ((self.cache_data[c_n] >> 4) == (self.cache_data[(c_n - 1) % 3] >> 4) and self.states[(c_n - 1) % 3] == 4):
                self.states[(c_n - 1) % 3] = 2
            if ((self.cache_data[c_n] >> 4) == (self.cache_data[(c_n + 1) % 3] >> 4) and self.states[(c_n + 1) % 3] == 4):
                self.states[(c_n + 1) % 3] = 2

        return cycles_used, state

    # Método público
    def process_instruction(self, op: dict, c_n: int, proto: str, counter) -> tuple[bool, int, bool]:
        # En base a los datos de la operación, el procesador que la ejecuta, el protocolo, el estado del sistema
        # y si se desean utilizar contadores, devuelve si ha ocurrido un acierto de caché, los ciclos necesarios 
        # para realizar la operación de lectura o escritura que se desea, y si hay operación extra (significa que
        # para completar la operación que se desea se ha tenido que reemplazar un bloque que se encontraba
        # desactualizado en la caché del procesador que está realizando la operación, lo cual provoca hacer un WB
        # y retrasar la ejecución de la operación deseada)
        cache_success = False
        cycles_used = 0
        extra_op = False

        # La operación es de lectura
        if(op["op"] == 'r'):
            # La etiqueta coincide con la dirección (el bloque deseado puede estar en caché)
            if(op["dir"] == (self.cache_data[c_n] >> 4)):
                # El bloque se encuentra en caché (acierto de caché)
                if(self.states[c_n] > 0):
                    cache_success = True
                    cycles_used = 3
                # El bloque no se encuentra en caché (fallo de caché) -> hay que pedirlo
                else:
                    cycles_used, data, state = self.BusRd(op, c_n, proto)
                    self.cache_data[c_n] = (op["dir"] << 4) | data
                    self.states[c_n] = state
            # La etiqueta no coincide (el bloque deseado no se encuentra en caché)
            else:
                # El bloque que se encuentra en caché está actualizado con memoria (fallo de
                # caché) -> se pide el nuevo
                if(self.states[c_n] < 3):
                    cycles_used, data, state = self.BusRd(op, c_n, proto)
                    self.cache_data[c_n] = (op["dir"] << 4) | data
                    self.states[c_n] = state
                # El bloque que se encuentra en caché está desactualizado con memoria y solo se encuentra
                # en la caché del procesador que ejecuta (fallo de caché) -> hay que hacer un WB y retrasar
                # la ejecución de la operación de lectura
                elif(self.states[c_n] == 3):
                    cycles_used, state = self.BusWB(op, c_n)
                    self.states[c_n] = state
                    extra_op = True
                # El bloque que se encuentra en caché está desactulizado y en estado O o S* (fallo de caché)
                else:
                    # Se usan contadores para el MESS*I
                    if(counter):
                        # El bloque desactualizado se encuentra en otras cachés -> se pide el nuevo
                        if((self.cache_data[(c_n - 1) % 3] == self.cache_data[c_n] and self.states[(c_n - 1) % 3] == 4) or (self.cache_data[(c_n + 1) % 3] == self.cache_data[c_n] and self.states[(c_n + 1) % 3] == 4)):
                            cycles_used, data, state = self.BusRd(op, c_n, proto)
                            self.cache_data[c_n] = (op["dir"] << 4) | data
                            self.states[c_n] = state
                        # El bloque desactualizado solo se encuentra en la caché del procesador que 
                        # ejecuta -> hay que hacer un WB y retrasar la ejecución de la operación
                        # de lectura
                        else:
                            cycles_used, state = self.BusWB(op, c_n)
                            self.states[c_n] = state
                            extra_op = True
                    # No se usan contadores -> hay que hacer un WB y retrasar la ejecución de la operación
                    # de lectura
                    else:
                        cycles_used, state = self.BusWB_no_counter(op, c_n, proto)
                        self.states[c_n] = state
                        extra_op = True
        # La operación es de escritura
        else:
            data = (random.randint(0, 15) & 0xf)                        # Valor que se escribirá en la caché
            # La etiqueta coincide con la dirección (el bloque deseado puede estar en caché)
            if(op["dir"] == (self.cache_data[c_n] >> 4)):
                # El bloque no se encuentra en caché (fallo de caché) -> hay que pedirlo
                if(self.states[c_n] == 0):
                    cycles_used, state = self.BusRdX(op, c_n, proto)
                    self.cache_data[c_n] = (op["dir"] << 4) | data
                    self.states[c_n] = state
                # El bloque se encuentra en caché (acierto de caché) y solo lo tiene el procesador que ejecuta
                elif(self.states[c_n] == 1 or self.states[c_n] == 3):
                    cache_success = True
                    cycles_used = 3
                    self.cache_data[c_n] = (op["dir"] << 4) | data
                    self.states[c_n] = 3
                # El bloque se encuentra en caché (acierto de caché) pero está presente en más cachés
                else:
                    cache_success = True
                    cycles_used, state = self.BusUpgr(op, c_n)
                    self.cache_data[c_n] = (op["dir"] << 4) | data
                    self.states[c_n] = state
            # La etiqueta no coincide (el bloque deseado no se encuentra en caché)
            else:
                # El bloque que se encuentra en caché está actualizado con memoria (fallo de
                # caché) -> se pide el nuevo
                if(self.states[c_n] < 3):
                    cycles_used, state = self.BusRdX(op, c_n, proto)
                    self.cache_data[c_n] = (op["dir"] << 4) | data
                    self.states[c_n] = state
                # El bloque que se encuentra en caché está desactualizado con memoria y solo se encuentra
                # en la caché del procesador que ejecuta (fallo de caché) -> hay que hacer un WB y retrasar
                # la ejecución de la operación de escritura
                elif(self.states[c_n] == 3):
                    cycles_used, state = self.BusWB(op, c_n)
                    self.states[c_n] = state
                    extra_op = True
                # El bloque que se encuentra en caché está desactulizado y en estado O o S* (fallo de caché)
                else:
                    # Se usan contadores para el MESS*I
                    if(counter):
                        # El bloque desactualizado se encuentra en otras cachés -> se pide el nuevo
                        if((self.cache_data[(c_n - 1) % 3] == self.cache_data[c_n] and self.states[(c_n - 1) % 3] == 4) or (self.cache_data[(c_n + 1) % 3] == self.cache_data[c_n] and self.states[(c_n + 1) % 3] == 4)):
                            cycles_used, state = self.BusRdX(op, c_n, proto)
                            self.cache_data[c_n] = (op["dir"] << 4) | data
                            self.states[c_n] = state
                        # El bloque desactualizado solo se encuentra en la caché del procesador que 
                        # ejecuta -> hay que hacer un WB y retrasar la ejecución de la operación
                        # de escritura
                        else:
                            cycles_used, state = self.BusWB(op, c_n)
                            self.states[c_n] = state
                            extra_op = True
                    # No se usan contadores -> hay que hacer un WB y retrasar la ejecución de la operación
                    # de escritura
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

    # Método público
    # Misma función que la anterior pero no existe el contador para el protocolo MESS*I. Es decir, si un procesador quiere hacer un reemplazo y tanto
    # él como otros procesadores tienen el mismo bloque en estado S*, todos deberán pasar S haciendo un BusWB.
#    def process_instruction_no_counter(self, op: dict, c_n: int, proto: str) -> tuple[bool, int, bool]:
#        cache_success = False
#        cycles_used = 0
#        extra_op = False
#
#        if(op["op"] == 'r'):
#            if(op["dir"] == (self.cache_data[c_n] >> 4)):
#                if(self.states[c_n] > 0):
#                    cache_success = True
#                    cycles_used += 3
#                else:
#                    cycles_used, data, state = self.BusRd(op, c_n, proto)
#                    self.cache_data[c_n] = (op["dir"] << 4) | data
#                    self.states[c_n] = state
#            else:
#                if(self.states[c_n] < 3):
#                    cycles_used, data, state = self.BusRd(op, c_n, proto)
#                    self.cache_data[c_n] = (op["dir"] << 4) | data
#                    self.states[c_n] = state
#                elif(self.states[c_n] == 3):
#                    cycles_used, state = self.BusWB(op, c_n)
#                    self.states[c_n] = state
#                    extra_op = True
#                else:
#                    cycles_used, state = self.BusWB_no_counter(op, c_n, proto)
#                    self.states[c_n] = state
#                    extra_op = True
#        else:
#            data = (random.randint(0, 15) & 0xf)
#            if(op["dir"] == (self.cache_data[c_n] >> 4)):
#                if(self.states[c_n] == 0):
#                    cycles_used, state = self.BusRdX(op, c_n, proto)
#                    self.cache_data[c_n] = (op["dir"] << 4) | data
#                    self.states[c_n] = state
#                elif(self.states[c_n] == 1 or self.states[c_n] == 3):
#                    cache_success = True
#                    cycles_used = 3
#                    self.cache_data[c_n] = (op["dir"] << 4) | data
#                    self.states[c_n] = 3
#                else:
#                    cache_success = True
#                    cycles_used, state = self.BusUpgr(op, c_n)
#                    self.cache_data[c_n] = (op["dir"] << 4) | data
#                    self.states[c_n] = state
#            else:
#                if(self.states[c_n] < 3):
#                    cycles_used, state = self.BusRdX(op, c_n, proto)
#                    self.cache_data[c_n] = (op["dir"] << 4) | data
#                    self.states[c_n] = state
#                elif(self.states[c_n] == 3):
#                    cycles_used, state = self.BusWB(op, c_n)
#                    self.states[c_n] = state
#                    extra_op = True
#                else:
#                    cycles_used, state = self.BusWB_no_counter(op, c_n, proto)
#                    self.states[c_n] = state
#                    extra_op = True
#
#        if(DEBUG):
#            states_str: list
#            states_str = ["", "", ""]
#            for i in range(3):
#                if(self.states[i] == 0):
#                    states_str[i] = "I"
#                elif(self.states[i] == 1):
#                    states_str[i] = "E"
#                elif(self.states[i] == 2):
#                    states_str[i] = "S"
#                elif(self.states[i] == 3):
#                    states_str[i] = "M"
#                elif(self.states[i] == 4 and proto == "moesi"):
#                    states_str[i] = "O"
#                else:
#                    states_str[i] = "S*"
#            print(f"Cache {c_n + 1}: {op}")
#            print(f"0x{self.cache_data[0]:02x} {states_str[0]} | 0x{self.cache_data[1]:02x} {states_str[1]} | 0x{self.cache_data[2]:02x} {states_str[2]} | {hex(self.ram[1])} {hex(self.ram[0])}")
#            print(f"Ciclos usados: {cycles_used}")
#        
#        return cache_success, cycles_used, extra_op