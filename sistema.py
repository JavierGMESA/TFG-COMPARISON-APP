cache_data: list
cache_data = [0x00, 0x00, 0x00]
states: list
states = [0, 0, 0]
ram = [0xb, 0x4]

def BusRd(op: dict, c_n: int, proto: str) -> tuple[int, int, int]:
    cicles_used = 0

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
    
    oc1_has = op["dir"] == (cache_data[oc1_n] >> 4) and states[oc1_n] > 0
    oc2_has = op["dir"] == (cache_data[oc2_n] >> 4) and states[oc2_n] > 0
    oc1_sta = states[oc1_n]
    oc2_sta = states[oc2_n]

    if(not oc1_has and not oc2_has):
        cicles_used = 48
        data = ram[op["dir"]]
        state = 1 if proto != "msi" else 2
    elif(not oc2_has):
        data = cache_data[oc1_n] & 0xf
        if(oc1_sta < 3):
            cicles_used = 11 + op["lat1"]
            state = 2
            states[oc1_n] = 2               #Lo ponemos en estado Shared en caso de que estuviera en Exclusive
        else:
            if(proto == "msi" or proto == "mesi"):
                cicles_used = 48
                state = 2
                states[oc1_n] = 2           #Lo ponemos en estado Shared a consecuencia del WB
            elif(proto == "moesi"):
                cicles_used = 11 + op["lat1"]
                state = 2
                states[oc1_n] = 4           #Si no está en estado Owner lo colocamos
            else:
                cicles_used = 11 + op["lat1"]
                state = 4
                states[oc1_n] = 4           #Lo ponemos en estado Shared*
    elif(not oc1_has):
        data = cache_data[oc2_n] & 0xf
        if(oc2_sta < 3):
            cicles_used = 11 + op["lat2"]
            state = 2
            states[oc2_n] = 2
        else:
            if(proto == "msi" or proto == "mesi"):
                cicles_used = 48
                state = 2
                states[oc2_n] = 2
            elif(proto == "moesi"):
                cicles_used = 11 + op["lat2"]
                state = 2
                states[oc2_n] = 4
            else:
                cicles_used = 11 + op["lat2"]
                state = 4
                states[oc2_n] = 4
    else:
        data = cache_data[oc1_n] & 0xf
        if(oc1_sta < 3 and oc2_sta < 3):
            cicles_used = 11 + min(op["lat1"], op["lat2"])
            state = 2
        elif(oc1_sta >= 3 and oc2_sta >= 3):
            if(proto == "msi" or proto == "mesi"):
                raise ValueError("proto es msi o mesi pero hay dos caches compartiendo un bloque dirty")
            elif(proto == "moesi"):
                raise ValueError("proto es moesi pero hay dos caches con un mismo bloque en estado Modified u Owner")
            else:
                cicles_used = 11 + min(op["lat1"], op["lat2"])
                state = 4
        elif(oc1_sta >= 3):
            if(proto == "msi" or proto == "mesi"):
                raise ValueError("proto es msi o mesi pero hay dos caches compartiendo un bloque dirty")
            elif(proto == "moesi"):
                cicles_used = 11 + op["lat1"]
                state = 2
                states[oc1_n] = 4
            else:
                raise ValueError("proto es mess*i y hay dos caches compartiendo un bloque dirty pero solo una está en Modified o Shared*")
        else:
            if(proto == "msi" or proto == "mesi"):
                raise ValueError("proto es msi o mesi pero hay dos caches compartiendo un bloque dirty")
            elif(proto == "moesi"):
                cicles_used = 11 + op["lat2"]
                state = 2
                states[oc1_n] = 4
            else:
                raise ValueError("proto es mess*i y hay dos caches compartiendo un bloque dirty pero solo una está en Modified o Shared*")        
    
    return cicles_used, data, state
    


def process_instruction(op: dict, c_n: int, proto: str) -> tuple[bool, int, bool]:
    cache_success = False
    cicles_used = 0
    extra_op = False

    if(op["op"] == 'r'):
        if(op["dir"] == (cache_data[c_n] >> 4)):
            if(states[c_n] > 0):
                cache_success = True
                cicles_used += 3
            else:
                cicles_used, data, state = BusRd(op, c_n, proto)
                cache_data[c_n] = (op["dir"] << 4) | data
                states[c_n] = state
        else:
            if(states[c_n] < 3):
                cicles_used, data, state = BusRd(op, c_n, proto)
                cache_data[c_n] = (op["dir"] << 4) | data
                states[c_n] = state
            elif(states[c_n] == 3):
                cicles_used, state = BusWB(op, c_n, proto)
                states[c_n] = state
                extra_op = True


    
    return cache_success, cicles_used, extra_op