import re

Memory = ["0" * 8 for i in range(4096)]
Registers = ["0"] * 8
Buffer = ["0" * 8 for i in range(4)]
Current_Address = 0


def clear_memory():
    Memory = ["0" * 8 for i in range(4096)]
    Registers = ["0"] * 8


class Output(object):
    global Memory

    def __init__(self, address: int, space=1):
        self.address = address
        self.__space = space
        self.memory = []
        if address < 0:
            return
        if space == 1:
            self.memory = [Memory[address]]
        elif space > 1:
            self.memory = Memory[address:address + space]

    @property
    def space(self):
        return self.__space

    @space.setter
    def space(self, value):
        if value <= 0 or self.address < 0:
            return
        if value == 1:
            self.memory = [Memory[self.address]]
        else:
            self.memory = Memory[self.address:self.address + value]
        self.__space = value

    def __iter__(self):
        return iter(self.memory)


Things = {
    "Stoplight": Output(-1),
    "Seven Segment": Output(-1),
    "Ascii Display": Output(-1, 8)
}


def sliceAssig(l: list, lower: int, upper: int, value) -> list:
    l[lower:upper] = [value] * (upper - lower)
    return l


def is_binary(elem):
    return re.match(r'^[01]+$', elem)


def is_hex(elem):
    if not is_binary(elem):
        return re.match(r'^[\d]+[0-9a-fA-F]+$', elem)
    return False


def is_dec(elem):
    return re.match(r'^[\d]+$', elem)


def dec_to_ascii(dec: int):
    return chr(dec)


def bin_to_ascii(bin: str):
    return dec_to_ascii(int(bin, 2))


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
    value = str(value)
    # print(value,type(value))
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
    print(f'Wrote {elem[:8]} to {addr}')
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
    arguments = [binary(a, 3) if type(a) == int else hex_to_bin(a, 3) for a in args]
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
        print(f'Writing {e} to {address + i}...')
        write_to_memory_from_address(address + i, binary(e, 8))


def LOAD(R: int, address: int):
    global Registers, Memory
    Registers[R] = bin_to_hex(Memory[address])
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
    store = hex_to_bin(Registers[R], 8)
    print(f'Storing {store} from R{R} into Memory address:{address}')
    Memory[address] = store
    return format_function(3, 2, R, address)


def PUSH(R: int, current_address=1):
    global Registers, Memory
    Memory[current_address - 1] = hex_to_bin(Registers[R].zfill(len(Memory[current_address])))
    return format_function(4, 2, R, current_address - 1)


def LOADRIND(R1: int, R2: int):
    global Registers, Memory
    Registers[R1] = bin_to_hex(Memory[int(Registers[R2], 16)])
    return format_function(5, 1, R1, R2)


def STORERIND(R1: int, R2: int):
    global Registers, Memory
    Registers[R2] = bin_to_hex(Memory[int(Registers[R1], 16)])
    return format_function(6, 1, R1, R2)


def ADD(Ra: int, R1: int, R2: int):
    global Registers
    Registers[Ra] = hexadecimal(hex_to_dec(Registers[R1]) + hex_to_dec(Registers[R2]))
    return format_function(7, 1, Ra, R1, R2)


def SUB(Ra: int, R1: int, R2: int):
    global Registers
    Registers[Ra] = hexadecimal(hex_to_dec(Registers[R1]) - hex_to_dec(Registers[R2]))
    return format_function(8, 1, Ra, R1, R2)


def ADDIM(R: int, const: str):
    global Registers
    current = hex_to_dec(Registers[R])
    decimal = hex_to_dec(const)
    Registers[R] = hexadecimal(current + decimal)
    return format_function(9, 2, R, const)


def SUBIM(R: int, const: str):
    global Registers
    current = hex_to_dec(Registers[R])
    decimal = hex_to_dec(const)
    Registers[R] = hexadecimal(current - decimal)
    return format_function(10, 2, R, const)


def AND(Ra: int, R1: int, R2: int):
    global Registers
    Registers[Ra] = str(int(hex_to_dec(Registers[R1]) * hex_to_dec(Registers[R2]) != 0)).zfill(4)
    return format_function(11, 1, Ra, R1, R2)


def OR(Ra: int, R1: int, R2: int):
    global Registers
    Registers[Ra] = str(int(hex_to_dec(Registers[R1]) + hex_to_dec(Registers[R2]) != 0)).zfill(4)
    return format_function(12, 1, Ra, R1, R2)


def XOR(Ra: int, R1: int, R2: int):
    global Registers
    Registers[Ra] = str(int(hex_to_dec(Registers[R1]) != hex_to_dec(Registers[R2]))).zfill(4)
    return format_function(13, 1, Ra, R1, R2)


def NOT(Ra: int, R1: int):
    global Registers
    Registers[Ra] = bin_to_hex(not_bin(hex_to_bin(Registers[R1], 8)))
    return format_function(14, 1, Ra, R1)


def NEG(Ra: int, R1: int):
    global Registers
    Registers[Ra] = hexadecimal(-hex_to_dec(Registers[R1]))
    return format_function(15, 1, Ra, R1)


def SHIFTR(Ra: int, R1: int, R2: int):
    global Registers
    shifts = hex_to_dec(Registers[R2])
    b = hex_to_bin(Registers[1])
    if shifts >= len(b):
        Registers[Ra] = "0" * 8
        return format_function(16, 1, Ra, R1, R2)
    shifts %= len(b)
    b = "0" * shifts + b[:-shifts]
    h = bin_to_hex(b, 4)
    Registers[Ra] = h
    return format_function(16, 1, Ra, R1, R2)


def SHIFTL(Ra: int, R1: int, R2: int):
    global Registers
    shifts = hex_to_dec(Registers[R2])
    b = hex_to_bin(Registers[1])
    if shifts >= len(b):
        Registers[Ra] = "0" * 8
        return format_function(17, 1, Ra, R1, R2)
    shifts %= len(b)
    b = b[:shifts] + "0" * shifts
    h = bin_to_hex(b, 4)
    Registers[Ra] = h
    return format_function(17, 1, Ra, R1, R2)


def ROTAR(Ra: int, R1: int, R2: int):
    global Registers
    shifts = hex_to_dec(Registers[R2])
    b = hex_to_bin(Registers[1])
    shifts %= len(b)
    b = b[-shifts:] + b[:-shifts]
    h = bin_to_hex(b, 4)
    Registers[Ra] = h
    return format_function(18, 1, Ra, R1, R2)


def ROTAL(Ra: int, R1: int, R2: int):
    global Registers
    b = hex_to_bin(Registers[R1])
    shifts = hex_to_dec(Registers[R2])
    result = ""
    for i in range(len(b)):
        m = (i + shifts) % len(b)
        result += b[m]
    h = bin_to_hex(result, 4)
    Registers[Ra] = h
    return format_function(19, 1, Ra, R1, R2)


def JMPRIND(R: int):
    pass


def JMPADDR(*args):
    return format_function(21, 3, *args)


def JCONDRIN(R: int):
    pass


def JCONDADDR(address: int):
    pass


def LOOP(Ra: int, address: int):
    global Registers, Memory
    n = hex_to_dec(Registers[Ra])
    if address % 2 != 0:
        address += 1
    instruction = Memory[address] + Memory[address + 1]
    # print(f'The loop is gonna loop {n} times')
    for i in range(n):
        # print(f"looping instruction {instruction}")
        binary_to_instructions(instruction, address)
    Registers[Ra] = '0'
    return format_function(24, 2, Ra, address)


def GRT(R1: int, R2: int):
    pass


def GRTEQ(R1: int, R2: int):
    pass


def EQ(R1: int, R2: int):
    pass


def NEQ(R1: int, R2: int):
    pass


def NOP(*args):
    return format_function(29, 1, *args)


def CALL(current_address: int):
    pass


def RETURN():
    pass


def show_memory(num=-1):
    global Memory
    print("=== Memory ===")
    for i in range(num % len(Memory)):
        print(f'Memory {i}: = {Memory[i]}')


def show_hex_memory(num=-1):
    print("=== Hex Memory ===")
    hexm = memory_to_hex()
    for i in range(int(num / 2) % len(hexm)):
        print(f'Hex Memory {i * 2}: = {hexm[i]}')


def show_registers():
    global Registers
    print("=== Registers ===")
    for i in range(len(Registers)):
        print(f'R{i} = {Registers[i]}')


instruction_functions = [LOAD, LOADIM, POP, STORE, PUSH, LOADRIND, STORERIND, ADD, SUB, ADDIM, SUBIM,
                         AND, OR, XOR, NOT, NEG, SHIFTR, SHIFTL, ROTAR, ROTAL, JMPRIND, JMPADDR,
                         JCONDRIN, JCONDADDR, LOOP, GRT, GRTEQ, EQ, NEQ, NOP, CALL, RETURN]
instruction_format: list = [1] * len(instruction_functions)
instruction_format = sliceAssig(instruction_format, 0, 11, 2)
instruction_format[21] = 3
instruction_format[22] = 3
instruction_format[23] = 3
instruction_format[24] = 2
instruction_format[30] = 3


def binary_to_instructions(b: str, address: int):
    global instruction_functions
    opcode = int(b[:5], 2)
    instruction = instruction_functions[opcode]
    f = instruction_format[opcode]
    args = []
    if f == 1:
        ra = int(b[5:8], 2)
        rb = int(b[8:11], 2)
        rc = int(b[11:14], 2)
        args = [ra, rb, rc]
    if f == 2:
        ra = int(b[5:8], 2)
        rb = int(b[8:], 2)
        args = [ra, rb]
    if f == 3:
        ra = int(b[5:], 2)
        args = [ra]
    args = [a for a in args if a != 0]
    instruction(*args)

# write_to_memory_from_address(0, LOAD(5, 25))
# write_to_memory_from_address(3, LOADIM(6, "2"))

# show_memory(10)
# show_registers()

# wm = write_to_memory_from_address
# DB(25, 17, 7, 8, 9, 5, 2, 2, 20)
# write_to_memory_from_address(0, LOAD(5, 25))
# write_to_memory_from_address(2, LOAD(3, 26))
# write_to_memory_from_address(4, ADD(1, 5, 3))
# wm(6, ADDIM(6, '1'))
# wm(8, ADDIM(6, '8'))
# wm(10, NOT(4, 6))
# wm(12, NEG(7, 6))  ###WTF
# wm(14, LOOP(3, 6))
#
# show_memory(30)
# show_hex_memory(30)
# show_registers()