import re

Memory = ["0" * 8 for i in range(10)]
Registers = ["0"] * 8


def is_binary(elem):
    return re.match(r'^[01]+$', elem)


def is_hex(elem):
    if not is_binary(elem):
        return re.match(r'^[\d]+[0-9a-fA-F]+$', elem)
    return False


def is_dec(elem):
    return re.match(r'^[\d]+$', elem)


def zfill_right(string: str, zeroes: int):
    return string.ljust(zeroes, "0")


def hexadecimal(integer, bits=0):
    h = hex(integer)
    if h.startswith('-'):
        h = '-' + h[3:]
    else:
        h = h[2:]
    if len(h) < bits:
        h = h.zfill(bits)
    return h.upper()


def binary(integer, bits=0):
    b = bin(integer)
    if b.startswith('-'):
        b = '-' + b[3:]
    else:
        b = b[2:]
    if len(b) < bits:
        b = b.zfill(bits)
    return b


def bin_to_dec(value):
    return int(value, 2)


def hex_to_dec(value):
    return int(value, 16)


def hex_to_bin(hexadecimal: str, bits: int = 0) -> str:
    s: str = bin(int(hexadecimal, 16))[2:].upper()
    if len(s) < bits:
        return s.zfill(bits)
    return s


def bin_to_hex(bin_val: str, bits: int = 0) -> str:
    s: str = hex(int(bin_val, 2))[2:].upper()
    if len(s) < bits:
        return s.zfill(bits)
    return s


def twos_comp(value, bits=-1, Type=2):
    if Type <= 0:
        Type = 2
    val = int(value, Type)
    if bits <= -1:
        bits = len(value)
    if (val & (1 << (bits - 1))) != 0:  # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << bits)  # compute negative value
    return binary(val)


def twos_comp_binary(value, bits=-1):
    return twos_comp(value, bits, 2)


def twos_comp_decimal(value, bits=-1):
    return int(twos_comp(value, bits, 2), 2)


def twos_comp_hex(value, bits=-1):
    return twos_comp(value, bits, 16)


def complement(binary_value):
    return binary(~int(binary_value, 2))


def not_bin(binary_value: str):
    result = ""
    for b in binary_value:
        if b == "0":
            result += "1"
        elif b == "1":
            result += "0"
        elif b == "-":
            result += "-"
    return result


def get_addr(bit):
    c = int(bit % 8)
    r = int(bit // 8)
    return r, c


def write_to_memory_from_address(addr, elem):
    global Memory
    Memory[addr] = elem[:8]
    if len(elem) > 8:
        remainder = elem[8:]
        write_to_memory_from_address(addr + 1, zfill_right(remainder, 8))


def write_to_memory_from_bit(bit, *elem):
    global Memory
    if len(elem) == 1 and type(elem[0]) == str:
        elem = elem[0]
    if len(elem) == 1 and type(elem) == str:
        r, c = get_addr(bit)
        Memory[r] = Memory[r][:c] + elem + Memory[r][c + 1:]
        return
    if type(elem) == str:
        r, c = get_addr(bit)
        address_length = len(Memory[r])
        if c + len(elem) + 1 >= address_length:
            front = elem[:address_length - c]
            remainder = elem[address_length - c:]
            Memory[r] = Memory[r][:c] + front
            write_to_memory_from_bit(bit + len(front), remainder)
            return
        else:
            Memory[r] = Memory[r][:c] + elem + Memory[r][c + len(elem):]
            return
    for i in range(len(elem)):
        write_to_memory_from_bit(bit + i, elem[i])


def memory_to_hex():
    global Memory
    bin_memory = [Memory[i] + Memory[i + 1] for i in range(0, len(Memory), 2)]
    hex_memory = [bin_to_hex(b, 4) for b in bin_memory]
    return hex_memory


def format_function(opcode, f_number, *args):
    first = binary(opcode, 5)
    arguments = [binary(a, 3) for a in args]
    if f_number == 1:
        return zfill_right(first + "".join(arguments), 16)
    if f_number == 2:
        return first + arguments[0] + arguments[1].zfill(8)
    if f_number == 3:
        return first + ("".join(arguments)).zfill(11)


def DB(address: int, *args):
    global Memory
    for i in range(len(args)):
        e = args[i]
        write_to_memory_from_address(address + i, binary(e, 8))


def LOAD(R: int, address: int):
    global Registers
    return format_function(0, 2, R, address)


def LOADIM(R: int, const: str):
    global Registers  # const must be a hex
    Registers[R] = const
    return format_function(1, 2, R, hex_to_dec(str(const)))


def POP(R: int, current_address=0):
    global Registers, Memory
    Registers[R] = bin_to_hex(Memory[current_address + 1])
    return format_function(2, 2, R, current_address + 1)


def STORE(R: int, address: int):
    global Memory, Registers
    Memory[address] = hex_to_bin(Registers[R].zfill(len(Memory[address])))
    return format_function(3, 2, R, address)


def PUSH(R: int, current_address=1):
    global Registers, Memory
    Memory[current_address - 1] = hex_to_bin(Registers[R].zfill(len(Memory[current_address])))
    return format_function(4, 2, R, current_address - 1)

def LOADRIND(R1: int, R2: int):
    pass

def STORERIND(R1: int, R2: int):
    pass

def ADD(R1: int, R2: int, R3: int): #R1 and then args possibly?
    pass

def SUB(R1: int, R2: int, R3: int):
    pass

def ADDIM(R: int, const: str):
    global Registers
    current = hex_to_dec(Registers[R])
    decimal = hex_to_dec(const)
    Registers[R] = hexadecimal(current + decimal)
    # falta return aqui

def SUBIM(R: int, const: str):
    pass

def AND(R1: int, R2: int, R3: int):
    pass

def OR(R1: int, R2: int, R3: int):
    pass

def XOR(R1: int, R2: int, R3: int):
    pass

def NOT(R1: int, R2: int):
    pass

def NEG(R1: int, R2: int):
    pass

def SHIFTR(R1: int, R2: int, R3: int):
    pass

def SHIFTL(R1: int, R2: int, R3: int):
    pass

def ROTAR(R1: int, R2: int, R3: int):
    pass

def ROTAL(R1: int, R2: int, R3: int):
    pass

def JMPRIND(R: int):
    pass

def JMPADDR(*args):
    return format_function(21, 3, *args)

def JCONDRIN(R: int):
    pass

def JCONDADDR(address: int):
    pass

def LOOP(R: int, address: int):
    pass

def GRT(R1: int, R2: int):
    pass

def GRTEQ(R1: int, R2: int):
    pass

def EQ(R1: int, R2: int):
    pass

def NEQ(R1: int, R2: int):
    pass

def NOP(*args):
    return format_function(29,1,*args)

def CALL(current_address: int):
    pass

def RETURN():
    pass


write_to_memory_from_address(0, LOAD(5, 25))
write_to_memory_from_address(3, LOADIM(6, "2"))

print(*Memory, sep="\n")