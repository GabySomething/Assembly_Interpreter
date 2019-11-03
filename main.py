import re
from enum import Enum
from Microcontroller import *


def isA(element, *what):
    return any(element == val for val in what)


instructions: list = ['LOAD', 'LOADIM', 'POP', 'STORE', 'PUSH', 'LOADRIND', 'STORERIND', 'ADD', 'SUB', 'ADDIM', 'SUBIM',
                      'AND', 'OR', 'XOR', 'NOT', 'NEG', 'SHIFTR', 'SHIFTL', 'ROTAR', 'ROTAL', 'JMPRIND', 'JMPADDR',
                      'JCONDRIN', 'JCONDADDR', 'LOOP', 'GRT', 'GRTEQ', 'EQ', 'NEQ', 'NOP', 'CALL', 'RETURN']

arguments: list = [2, 2, 1, 2, 1, 2, 2, 3, 3, 2, 2, 3, 3, 3, 2, 2, 3, 3, 3, 3, 1, 1, 1, 1, 2, 2, 2, 2, 2, 0, 1, 0]
argument_types: list = ["r,a", "r,c", "r", "r,a", "r", "r,r", "r,r", "r,r,r", "r,r,r", "r,c", "r,c", "r,r,r", "r,r,r",
                        "r,r,r", "r,r", "r,r", "r,r,r", "r,r,r", "r,r,r", "r,r,r", "r", "a", "r", "a", "r,a", "r,r",
                        "r,r", "r,r", "r,r", "0", "a", "0"]


# memory = [0] * 256
# Mem = ["0" * 8 for i in range(4096)]
# Registers = ["0"] * 8


class TokenType(Enum):
    INTEGER = "INTEGER"
    INSTRUCTION = "INSTRUCTION"
    LABEL = "LABEL"
    ORG = "ORG"
    CONST_ASSIGN = "CONST_ASSIGN"
    LIST_ASSIGN = "LIST_ASSIGN"
    VARIABLE = "VARIABLE"
    REGISTER = "REGISTER"
    EOF = "EOF"


class Token(object):
    def __init__(self, value, TokenType: TokenType, org: int = -1, form: int = -1, constant: bool = False,
                 line_number: int = -1):
        self.value = value
        self.org = org
        self.form = form
        self.TokenType = TokenType
        self.constant = constant
        self.line_number = line_number

    def __str__(self):
        name = "Token (VALUE: {value}, TYPE: {t}, ORIGIN: {org})".format(value=self.value, t=self.TokenType.value,
                                                                         org=hexadecimal(self.org, 2))
        if self.constant:
            name = name.replace(")", " CONSTANT: TRUE)")
        return name

    def __repr__(self):
        return str(self)


class Interpreter(object):
    errors = {}
    warnings = {}
    token_lines: list = list()
    variables = {}
    dead = False

    def __init__(self, text: str):
        self.text = text
        self.dead = False
        self.errors = {}
        self.lines: list = list()
        self.token_lines = list()
        self.index = 0
        self.function_lines = None
        lines = text.replace(",", " ").split("\n")  ##hmmmmmmmmmmmm
        for line in lines:
            line: str = line
            if "//" in line:
                line = line[:line.index("//")]
            if len(line) == 0:
                continue
            elif len(line.strip()) == 0:
                continue
            if line.startswith("//"):
                continue
            self.lines.append(line)
        self.current_line: int = 0

    def token_type(self, word: str):
        if word.lower() == "org":
            return TokenType.ORG
        if word.lower() == "db":
            return TokenType.LIST_ASSIGN
        if word.lower() == "const":
            return TokenType.CONST_ASSIGN
        if word in instructions:
            return TokenType.INSTRUCTION
        if re.match("^[0-9]+[0-9a-fA-F]+", word) or re.match("^[0-9]+", word) or re.match("^#[0-9]+", word) or re.match(
                "^#[0-9a-fA-F]+", word):
            return TokenType.INTEGER
        if word.endswith(":"):
            return TokenType.LABEL
        if re.match("^R[0-9]+", word):
            if word.lower().replace("r", "").isdigit():
                return TokenType.REGISTER
        return TokenType.VARIABLE

    def get_tokens_in_list(self, token_list: list, line_number, *Token_Type: TokenType, save_errors: bool = True,
                           is_constant: bool = False):
        tokens: list = list()
        for word in token_list:
            word: str = word
            if isA(self.token_type(word), *Token_Type):
                t: TokenType = self.token_type(word)
                if t == TokenType.INTEGER:
                    if word.startswith("#"):
                        is_constant = True
                    word = word.replace("#", "")
                elif t == TokenType.REGISTER:
                    word = word.lower().replace("r", "")
                tokens.append(Token(word, t, constant=is_constant))
                continue
            self.error("Invalid token,  looking for: [" + (
                ", ".join(t.value for t in Token_Type)) + "] got " + self.token_type(word).value, line_number,
                       save_errors)
            return []
        return tokens

    def error(self, error: str, line_index: int = -1, save_errors: bool = True, is_warning: bool = False,
              no_line: bool = False, instruction: str = ""):
        if not no_line and line_index > 0:
            error += "\nNEAR LINE: " + str(line_index + 1)
        if instruction.strip() is not "":
            error += "\nINSTRUCTION: " + instruction
        if save_errors and not is_warning:
            self.errors[line_index] = "ERROR: " + error
        elif is_warning:
            self.warnings[line_index] = "WARNING: " + error
        else:
            print(error)

    def set_origin_in_list(self, l: list, org: int, increasing_origin=False):
        for token in l:
            if type(token) == Token:
                token.org = org
                if token.TokenType == TokenType.LIST_ASSIGN or token.TokenType == TokenType.VARIABLE:
                    continue
                if increasing_origin:
                    org += 1
        return l

    def set_line_number_in_list(self, l: list, line_number: int):
        for token in l:
            if type(token) == Token:
                token.line_number = line_number
        return l

    def get_variable(self, var: str):
        if var in self.variables:
            return self.variables[var]
        return None

    def get_tokens_from_line(self, line: str, line_number: int = -1, origin: int = 0, save_errors: bool = True):
        tokens: list = list()
        if line[0] == " " or line[0] == "\t":
            words = [w.strip() for w in line.split()]
            first_token_type = self.token_type(words[0])
            if first_token_type == TokenType.INSTRUCTION:
                if origin % 2 != 0:
                    origin += 1
                index: int = instructions.index(words[0])
                tokens.append(Token(words[0], first_token_type, instruction_format[index]))
                tokens += self.get_tokens_in_list(words[1:], line_number, TokenType.REGISTER, TokenType.INTEGER,
                                                  TokenType.VARIABLE, save_errors=save_errors)
                tokens = self.set_origin_in_list(tokens, origin)
                origin += 2
            elif first_token_type == TokenType.LIST_ASSIGN:
                tokens.append(Token(words[0], first_token_type, -2))
                tokens += self.get_tokens_in_list(words[1:], line_number, TokenType.INTEGER, save_errors=save_errors)
                tokens = self.set_origin_in_list(tokens, origin)
                origin += 1
            elif first_token_type == TokenType.CONST_ASSIGN:
                if len(words) < 3:
                    self.error("Invalid token, not enough arguments", line_number, save_errors)
                    return None, origin
                elif len(words) > 3:
                    self.error("Invalid token, too many arguments", line_number, save_errors)
                    return None, origin
                if self.token_type(words[1]) == TokenType.VARIABLE:
                    tokens.append(Token(words[0], first_token_type))
                    tokens.append(Token(words[1], TokenType.VARIABLE))
                    tokens += self.get_tokens_in_list(words[2:], line_number, TokenType.INTEGER,
                                                      save_errors=save_errors, is_constant=True)
                    tokens = self.set_origin_in_list(tokens, origin)
                else:
                    self.error("Invalid token, after declaring const, you must declare a variable name", line_number,
                               save_errors)
                    return None, origin
            elif first_token_type == TokenType.ORG:
                if len(words) != 2:
                    self.error("Invalid token, origin not set correctly", line_number, save_errors)
                    return None, origin
                org: int = int(words[1], 16)
                if origin > org:
                    self.error("---Possible risk of overwriting addresses.---", line_number, False, True)
                origin = org
                tokens.append(Token(words[0], first_token_type, org))
                tokens.append(Token(org, TokenType.INTEGER, org))
            else:
                self.error("Invalid token, the second column is only for instructions", line_number, save_errors)
                return None, origin
        else:
            words = [w.strip() for w in line.split()]
            first_token_type = self.token_type(words[0])
            if first_token_type == TokenType.LABEL:
                tokens.append(Token(words[0].replace(":", ""), TokenType.LABEL, origin))
                if len(words) >= 3:
                    token_type = self.token_type(words[1])
                    if token_type != TokenType.INSTRUCTION:
                        self.error("Invalid token, can't have a {type} after a label".format(type=token_type),
                                   line_number, save_errors)
                    else:
                        if origin % 2 != 0:
                            origin += 1
                        tokens.append(
                            Token(words[1], TokenType.INSTRUCTION, origin,
                                  instruction_format[instructions.index(words[1])]))
                    tokens += self.get_tokens_in_list(words[2:], line_number, TokenType.REGISTER, TokenType.INTEGER,
                                                      TokenType.VARIABLE, save_errors=save_errors)
                    tokens = self.set_origin_in_list(tokens, origin)
                    origin += 2
                elif 1 < len(words) < 3:
                    self.error("Not enough arguments", line_number, save_errors)
            elif first_token_type == TokenType.VARIABLE:
                if len(words) < 3:
                    self.error("Invalid token, too few arguments", line_number, save_errors)
                    return None, origin
                if words[1].lower() == "db":
                    tokens.append(Token(words[0], first_token_type))
                    tokens.append(Token(words[1], TokenType.LIST_ASSIGN))
                    integers = self.get_tokens_in_list(words[2:], line_number, TokenType.INTEGER,
                                                       save_errors=save_errors)
                    bits_used: int = len(integers)
                    tokens += integers
                    tokens = self.set_origin_in_list(tokens, origin)
                    origin += bits_used
                else:
                    self.error("Invalid token, you must assign the variable with the instruction db", line_number,
                               save_errors)
                    return None, origin

        if len(tokens) <= 0:
            self.error("Bad formatting", line_number, save_errors)
            return None, origin
        return tokens, origin

    def get_tokens_from_line_3(self, line: str, line_number: int = -1, origin: int = 0, save_errors: bool = True):
        tokens: list = list()
        if line[0] == " " or line[0] == "\t":
            words = [w.strip() for w in line.split()]
            first_token_type = self.token_type(words[0])
            if first_token_type == TokenType.INSTRUCTION:
                if origin % 2 != 0:
                    origin += 1
                index: int = instructions.index(words[0])
                tokens.append(Token(words[0], first_token_type, instruction_format[index]))
                tokens += self.get_tokens_in_list(words[1:], line_number, TokenType.REGISTER, TokenType.INTEGER,
                                                  TokenType.VARIABLE, save_errors=save_errors)
                tokens = self.set_origin_in_list(tokens, origin)
                origin += 2
            elif first_token_type == TokenType.LIST_ASSIGN:
                # tokens.append(Token(words[0], first_token_type, -2))
                # tokens += self.get_tokens_in_list(words[1:], line_number, TokenType.INTEGER, save_errors=save_errors)
                # tokens = self.set_origin_in_list(tokens, origin)
                # origin += 1

                tokens.append(Token(words[0], first_token_type))
                # tokens.append(Token(words[1], TokenType.LIST_ASSIGN))
                integers = self.get_tokens_in_list(words[1:], line_number, TokenType.INTEGER,
                                                   save_errors=save_errors)
                bits_used: int = len(integers)
                tokens += integers
                tokens = self.set_origin_in_list(tokens, origin, True)
                origin += bits_used

            elif first_token_type == TokenType.CONST_ASSIGN:
                if len(words) < 3:
                    self.error("Invalid token, not enough arguments", line_number, save_errors)
                    return None, origin
                elif len(words) > 3:
                    self.error("Invalid token, too many arguments", line_number, save_errors)
                    return None, origin
                if self.token_type(words[1]) == TokenType.VARIABLE:
                    tokens.append(Token(words[0], first_token_type))
                    tokens.append(Token(words[1], TokenType.VARIABLE))
                    tokens += self.get_tokens_in_list(words[2:], line_number, TokenType.INTEGER,
                                                      save_errors=save_errors, is_constant=True)
                    tokens = self.set_origin_in_list(tokens, origin)
                else:
                    self.error("Invalid token, after declaring const, you must declare a variable name", line_number,
                               save_errors)
                    return None, origin
            elif first_token_type == TokenType.ORG:
                if len(words) != 2:
                    self.error("Invalid token, origin not set correctly", line_number, save_errors)
                    return None, origin
                org: int = int(words[1], 16)
                if origin > org:
                    self.error("---Possible risk of overwriting addresses.---", line_number, False, True)
                origin = org
                tokens.append(Token(words[0], first_token_type, org))
                tokens.append(Token(org, TokenType.INTEGER, org))
            else:
                self.error("Invalid token, the second column is only for instructions", line_number, save_errors)
                return None, origin
        else:
            words = [w.strip() for w in line.split()]
            first_token_type = self.token_type(words[0])
            if first_token_type == TokenType.LABEL:
                tokens.append(Token(words[0].replace(":", ""), TokenType.LABEL, origin))
                if len(words) >= 3:
                    token_type = self.token_type(words[1])
                    if token_type != TokenType.INSTRUCTION:
                        self.error("Invalid token, can't have a {type} after a label".format(type=token_type),
                                   line_number, save_errors)
                    else:
                        if origin % 2 != 0:
                            origin += 1
                        tokens.append(
                            Token(words[1], TokenType.INSTRUCTION, origin,
                                  instruction_format[instructions.index(words[1])]))
                    tokens += self.get_tokens_in_list(words[2:], line_number, TokenType.REGISTER, TokenType.INTEGER,
                                                      TokenType.VARIABLE, save_errors=save_errors)
                    tokens = self.set_origin_in_list(tokens, origin)
                    origin += 2
                elif 1 < len(words) < 3:
                    self.error("Not enough arguments", line_number, save_errors)
            elif first_token_type == TokenType.VARIABLE:
                if len(words) < 3:
                    self.error("Invalid token, too few arguments", line_number, save_errors)
                    return None, origin
                if words[1].lower() == "db":
                    tokens.append(Token(words[0], first_token_type))
                    tokens.append(Token(words[1], TokenType.LIST_ASSIGN))
                    integers = self.get_tokens_in_list(words[2:], line_number, TokenType.INTEGER,
                                                       save_errors=save_errors)
                    bits_used: int = len(integers)
                    tokens += integers
                    tokens = self.set_origin_in_list(tokens, origin, True)
                    origin += bits_used
                else:
                    self.error("Invalid token, you must assign the variable with the instruction db", line_number,
                               save_errors)
                    return None, origin

        if len(tokens) <= 0:
            self.error("Bad formatting", line_number, save_errors)
            return None, origin
        return tokens, origin

    def make_tokens_2(self, save_errors: bool = True):
        token_lines: list = list()
        org: int = 0
        for i in range(len(self.lines)):
            line: str = self.lines[i]
            tokens, org = self.get_tokens_from_line_3(line, i, org, save_errors)
            if tokens is None:
                continue
            if any(t.TokenType == TokenType.LIST_ASSIGN for t in tokens):
                if tokens[0].TokenType == TokenType.VARIABLE:
                    self.variables[tokens[0].value] = [
                        t.org if not t.constant or not t.TokenType == TokenType.REGISTER else t.value for t in
                        tokens[2:]]
            elif tokens[0].TokenType == TokenType.CONST_ASSIGN:
                self.variables[tokens[1].value] = tokens[2].value
            elif tokens[0].TokenType == TokenType.LABEL:
                self.variables[tokens[0].value] = tokens[0].org
            token_lines.append(tokens)
        self.token_lines = token_lines
        return token_lines

    def make_tokens_3(self, save_errors: bool = True):
        token_lines: list = list()
        org: int = 0
        for i in range(len(self.lines)):
            line: str = self.lines[i]
            tokens, org = self.get_tokens_from_line(line, i, org, save_errors)
            if tokens is None:
                continue
            if any(t.TokenType == TokenType.LIST_ASSIGN for t in tokens):
                if tokens[0].TokenType == TokenType.VARIABLE:
                    self.variables[tokens[0].value] = [t.value for t in tokens[2:]]
            elif tokens[0].TokenType == TokenType.CONST_ASSIGN:
                self.variables[tokens[1].value] = tokens[2].value
            elif tokens[0].TokenType == TokenType.LABEL:
                self.variables[tokens[0].value] = tokens[0].org
            token_lines.append(tokens)
        self.token_lines = token_lines
        return token_lines

    def is_clean(self):
        if len(self.token_lines) == 0:
            self.make_tokens_2()
        if None in self.token_lines:
            return False
        return len(self.errors) == 0

    def exit_system(self, code: int = 1):
        for key in self.warnings:
            print(self.warnings.get(key))
        for key in self.errors:
            print(self.errors.get(key))
        self.dead = True
        # exit(code)

    def to_memory(self):
        memory_line: list = [[]] * 256
        if not self.is_clean():
            return None
        for line in self.token_lines:
            if line is not None:
                if any(
                        token.TokenType == TokenType.CONST_ASSIGN or token.TokenType == TokenType.LIST_ASSIGN or token.TokenType == TokenType.LABEL or token.TokenType == TokenType.ORG
                        for token in line):
                    continue
                for token in line:
                    token: Token = token
                    addr = int(token.org)
                    if token.TokenType == TokenType.INSTRUCTION:
                        opcode = instructions.index(token.value)
                        memory_line[addr] = [opcode]
                    if token.TokenType == TokenType.VARIABLE:
                        var = self.get_variable(token.value)
                        if type(var) == list:
                            memory_line[addr].append(int(str(var[0]), 16))
                        else:
                            if type(var) == str:
                                var = int(var, 16)
                            if var is None:
                                self.error("Variable " + token.value + " is not defined")
                                self.exit_system()
                                if self.dead:
                                    return
                            memory_line[addr].append(var)
                    if token.TokenType == TokenType.INTEGER or token.TokenType == TokenType.REGISTER:
                        var = token.value
                        if type(var) == str:
                            var = int(var, 16)
                        memory_line[addr].append(var)

        return [x if len(x) > 0 else [0] for x in memory_line]

    def get_value(self, *tokens: Token):
        result = []
        for token in tokens:
            if token.TokenType == TokenType.REGISTER:
                result.append(int(token.value))
            if token.TokenType == TokenType.INTEGER:
                result.append(token.value)
            if token.TokenType == TokenType.VARIABLE:
                var = self.get_variable(token.value)
                if type(var) == list:
                    var = var[0]
                if var is None:
                    self.error("Variable " + token.value + " is not defined")
                    self.exit_system()
                    if self.dead:
                        return
                # print(var)
                result.append(var)
        return result

    def to_memory_2(self):
        table = []
        self.function_lines = None
        self.index = 0
        if not self.is_clean():
            clear_memory()
            print("Cleared memory")
            return None
        for line in self.token_lines:
            if line is not None:
                first_token_type = line[0].TokenType
                addr = line[0].org
                if first_token_type == TokenType.INSTRUCTION:
                    opcode = instructions.index(line[0].value)
                    remaining = line[1:]
                    values = self.get_value(*remaining)
                    if values is None:
                        continue
                    if any([v is None for v in values]):
                        # print(f"ERROR: Function {instructions[opcode]} is receiving an undefined value.")
                        continue
                    # print(f"ADDRESS: {addr}\t|", line[0].value, *values)
                    string = instructions[opcode] + " "
                    string += " ".join([str(v) for v in values])
                    table.append(f"INSTR : {string}")
                    # print([type(v) for v in values])
                    if opcode != 2:
                        output = instruction_functions[opcode](*values)
                    else:
                        output = instruction_functions[opcode](values[0], line[0].org)
                    if output is None:
                        output = "X" * 16
                    # print(f"Binary: {output}")
                    write_to_memory_from_address(addr, output)
                if first_token_type == TokenType.VARIABLE:
                    remaining = line[2:]
                    values = self.get_value(*remaining)
                    table_vals = values.copy()
                    values = [int(hex_to_dec(v)) for v in values]
                    # print(f"ADDRESS: {addr}\t|", line[0].value, "DB", *values)
                    string = line[0].value + " "
                    string += " ".join([str(v) for v in table_vals])
                    table.append(f'VAR : {string}')
                    DB(addr, *values)
                if first_token_type == TokenType.LIST_ASSIGN:
                    remaining = line[1:]
                    values = self.get_value(*remaining)
                    values = [int(hex_to_dec(v)) for v in values]
                    # print(f"ADDRESS: {addr}\t|", line[0].value, "DB", *values)
                    DB(addr, *values)
                if first_token_type == TokenType.CONST_ASSIGN:
                    table.append(f"CONST : {line[1].value} {line[2].value}")
                # print("-------")
        # for i in range(len(Registers)):
        #     r = get_registers()[i]
        #     table.append(f'R{i} : {r}')
        return get_memory(), list(dict.fromkeys(table))

    def to_step_memory(self):
        table = []
        functs = [None] * 4096
        if not self.is_clean():
            clear_memory()
            return None
        # i = 0
        for line in self.token_lines:
            if line is not None:
                # if i >= len(functs):
                #     functs.append([])
                first_token_type = line[0].TokenType
                addr = line[0].org
                if first_token_type == TokenType.INSTRUCTION:
                    opcode = instructions.index(line[0].value)
                    remaining = line[1:]
                    values = self.get_value(*remaining)
                    if values is None:
                        continue
                    if any([v is None for v in values]):
                        print(f"ERROR: Function {instructions[opcode]} is receiving an undefined value.")
                        continue
                    # print(f"ADDRESS: {addr}\t|", line[0].value, *values)
                    string = instructions[opcode] + " "
                    string += " ".join([str(v) for v in values])
                    table.append(f"INSTR : {string}")
                    # print([type(v) for v in values])
                    if opcode != 2:
                        # print(f"something in {i}")
                        functs[addr] = "INSTR", addr, instruction_functions[opcode], values, opcode
                    else:
                        # print(f"something in {i}")
                        functs[addr] = "INSTR", addr, instruction_functions[opcode], [values[0], line[0].org], opcode
                if first_token_type == TokenType.VARIABLE:
                    remaining = line[2:]
                    values = self.get_value(*remaining)
                    table_vals = values.copy()
                    values = [int(hex_to_dec(v)) for v in values]
                    # print(f"ADDRESS: {addr}\t|", line[0].value, "DB", *values)
                    string = line[0].value + " "
                    string += " ".join([str(v) for v in table_vals])
                    table.append(f'VAR : {string}')
                    functs[addr] = "DB", addr, DB, values, line[0].value
                    # DB(addr, *values)
                if first_token_type == TokenType.LIST_ASSIGN:
                    remaining = line[1:]
                    values = self.get_value(*remaining)
                    values = [int(hex_to_dec(v)) for v in values]
                    # print(f"ADDRESS: {addr}\t|", line[0].value, "DB", *values)
                    functs[addr] = "DB", addr, DB, values
                    # DB(addr, *values, memory=mem_lines)
                if first_token_type == TokenType.CONST_ASSIGN:
                    table.append(f"CONST : {line[1].value} {line[2].value}")
                # i += 1

        for i in range(len(Registers)):
            r = get_registers()[i]
            table.append(f'R{i} : {r}')
            # [f for f in functs if len(f) > 0]
        return functs, list(dict.fromkeys(table))

    def create_program_counter(self):
        self.index = 0
        unpack = self.to_step_memory()
        if unpack is None:
            self.exit_system()
            return
        mem_lines, _ = unpack
        # mem_lines = mem_lines.copy()
        # clear_memory()
        self.function_lines = mem_lines

    # def next(self):
    #     if self.function_lines is None:
    #         self.create_program_counter()
    #     i = self.index
    #     if i >= len(self.function_lines) - 1:
    #         self.index = 0
    #         return None
    #     current = self.function_lines[i] + self.function_lines[i + 1]
    #     self.index += 2
    #     if current == "0" * 16 or current == "X" * 16:
    #         for index in range(i, len(self.function_lines) - 1):
    #             i = index
    #             self.index = index + 2
    #             if self.function_lines[index] != "0" * 16 or self.function_lines[index] != "X" * 16:
    #                 current = self.function_lines[index] + self.function_lines[index + 1]
    #                 break
    #     if current == "0" * 16 or current == "X" * 16:
    #         current = None
    #     return current, i

    def set_program_counter(self, value):
        set_program_counter(value)

    def get_program_counter(self):
        return get_program_counter()

    def next(self):
        if self.index == 0:
            print("starting stepper....")
        if self.function_lines is None:
            self.create_program_counter()
        i = self.index
        fl = self.function_lines
        if fl is None:
            return
        if i >= len(fl):
            print("starting again....")
            self.index = 0
            return None
        self.index += 1
        if fl[i] is None or fl[i] == []:
            for index in range(i, len(fl)):
                if fl[index] is not None and fl[index] != []:
                    i = index
                    self.index = i + 1
                    break

        if fl[i] is None or fl[i] == []:
            print("starting again....")
            self.index = 0
            return None

        current: list = fl[i]
        addr = current[1]
        args = current[3]
        instruction = current[2]
        table = []
        set_program_counter(addr)
        print(f"Program Counter: {get_program_counter()}")
        if current[0] == "INSTR":
            opcode = current[4]
            write_to_memory_from_address(addr, instruction(*args))
            table = [f"INSTR | {instructions[opcode]} {args}"]
        elif current[0] == "DB":
            # print(*args)
            instruction(addr, *args)
            if len(current) == 5:
                table = [f"VAR | {current[4]} {args}"]

        return addr, table

    def get_register_table(self):
        return get_register_table()

    def run(self):
        addr, _ = self.next()
        while addr is not None:
            addr, _ = self.next()

    # def run_line(self,l):
    #     table = []
    #     line = self.token_lines[l]
    #     if line is not None:
    #         first_token_type = line[0].TokenType
    #         addr = line[0].org
    #         if first_token_type == TokenType.INSTRUCTION:
    #             opcode = instructions.index(line[0].value)
    #             remaining = line[1:]
    #             values = self.get_value(*remaining)
    #             if values is None:
    #                 continue
    #             if any([v is None for v in values]):
    #                 print(f"ERROR: Function {instructions[opcode]} is receiving an undefined value.")
    #                 continue
    #             print(f"ADDRESS: {addr}\t|", line[0].value, *values)
    #             string = instructions[opcode] + " "
    #             string += " ".join([str(v) for v in values])
    #             table.append(f"INSTR : {string}")
    #             # print([type(v) for v in values])
    #             if opcode != 2:
    #                 output = instruction_functions[opcode](*values)
    #             else:
    #                 output = instruction_functions[opcode](values[0], line[0].org)
    #             if output is None:
    #                 output = "X" * 16
    #             print(f"Binary: {output}")
    #             write_to_memory_from_address(addr, output)
    #         if first_token_type == TokenType.VARIABLE:
    #             remaining = line[2:]
    #             values = self.get_value(*remaining)
    #             table_vals = values.copy()
    #             values = [int(hex_to_dec(v)) for v in values]
    #             print(f"ADDRESS: {addr}\t|", line[0].value, "DB", *values)
    #             string = line[0].value + " "
    #             string += " ".join([str(v) for v in table_vals])
    #             table.append(f'VAR : {string}')
    #             DB(addr, *values)
    #         if first_token_type == TokenType.LIST_ASSIGN:
    #             remaining = line[1:]
    #             values = self.get_value(*remaining)
    #             values = [int(hex_to_dec(v)) for v in values]
    #             print(f"ADDRESS: {addr}\t|", line[0].value, "DB", *values)
    #             DB(addr, *values)
    #         if first_token_type == TokenType.CONST_ASSIGN:
    #             table.append(f"CONST : {line[1].value} {line[2].value}")
    #         print("-------")

    def to_decimal(self):
        decimal_lines: list = list()
        if not self.is_clean():
            return None
        for line in self.token_lines:
            if line is not None:
                if any(
                        token.TokenType == TokenType.CONST_ASSIGN or token.TokenType == TokenType.LIST_ASSIGN or token.TokenType == TokenType.LABEL or token.TokenType == TokenType.ORG
                        for token in line):
                    continue
                decimal_line: list = list()
                for token in line:
                    token: Token = token
                    if token.TokenType == TokenType.INSTRUCTION:
                        opcode = instructions.index(token.value)
                        decimal_line.append(opcode)
                    if token.TokenType == TokenType.VARIABLE:
                        var = self.get_variable(token.value)
                        if type(var) == list:
                            decimal_line.append(int(str(var[0]), 16))
                        else:
                            if type(var) == str:
                                var = int(var, 16)
                            if var is None:
                                self.error("Variable " + token.value + " is not defined")
                                self.exit_system()
                                if self.dead:
                                    return
                            decimal_line.append(var)
                    if token.TokenType == TokenType.INTEGER or token.TokenType == TokenType.REGISTER:
                        var = token.value
                        if type(var) == str:
                            var = int(var, 16)
                        decimal_line.append(var)

                decimal_lines.append(decimal_line)
        if decimal_lines is None:
            self.exit_system()
            if self.dead:
                return
        return decimal_lines

    def to_bin_list2(self):
        decimal_lines: list = self.to_memory()
        binary_lines: list = list()
        if decimal_lines is None:
            self.exit_system()
            if self.dead:
                return
        for line in decimal_lines:
            if line is None:
                self.exit_system()
                if self.dead:
                    return
            bits: int = 16
            binary_line: list = list()
            if len(line) == 1 and line[0] == 0:
                binary_line = ["".zfill(bits)]
                binary_lines.append(binary_line)
                continue
            instr_format: int = instruction_format[line[0]]
            binary_line.append(binary(line[0], 5))
            bits -= 5
            if instr_format == 1:
                for number in line[1:]:
                    binary_number = binary(number, 3)
                    binary_line.append(binary_number)
                    bits -= len(binary_number)
                if bits > 0:
                    binary_line.append("".zfill(bits))
                    bits = 0
            if instr_format == 2:
                for number in line[1:]:
                    binary_number = binary(number, 3)
                    binary_line.append(binary_number)
                    bits -= len(binary_number)
                if bits > 0:
                    binary_line.append("".zfill(bits))
                    bits = 0
            if instr_format == 3:
                binary_line.append(binary(line[1], bits))
            binary_lines.append(binary_line)
        return binary_lines

    def to_bin_list(self):
        decimal_lines: list = self.to_decimal()
        binary_lines: list = list()
        if decimal_lines is None:
            self.exit_system()
            if self.dead:
                return
        for line in decimal_lines:
            if line is None:
                self.exit_system()
                if self.dead:
                    return
            binary_line: list = list()
            instr_format: int = instruction_format[line[0]]
            bits: int = 16
            binary_line.append(binary(line[0], 5))
            bits -= 5
            if instr_format == 1:
                for number in line[1:]:
                    binary_number = binary(number, 3)
                    binary_line.append(binary_number)
                    bits -= len(binary_number)
                if bits > 0:
                    binary_line.append("".zfill(bits))
                    bits = 0
            if instr_format == 2:
                for number in line[1:]:
                    binary_number = binary(number, 3)
                    binary_line.append(binary_number)
                    bits -= len(binary_number)
                if bits > 0:
                    binary_line.append("".zfill(bits))
                    bits = 0
            if instr_format == 3:
                binary_line.append(binary(line[1], bits))
            binary_lines.append(binary_line)
        return binary_lines

    def instruction_check(self):
        if len(self.token_lines) == 0:
            self.make_tokens_2()
        for line_number in range(len(self.token_lines)):
            line: list = self.token_lines[line_number]
            token: Token = None
            token_pos = 0
            label = 0
            for ind in range(len(line)):
                tok: Token = line[ind]
                if tok.TokenType == TokenType.LABEL:
                    label += 1
                    continue
                if tok.TokenType == TokenType.INSTRUCTION:
                    token = tok
                    token_pos = ind
                    break
            if token is not None:
                index = instructions.index(token.value.upper())
                arg_number = arguments[index]
                arg_types = argument_types[index].replace(",", " ").split()
                token_number = len(line) - 1 - label
                if token_number != arg_number:
                    self.error("Incorrect number of arguments for instruction {instr}, expected {expected}".format(
                        instr=token.value, expected=arg_number), instruction=token.value.upper())
                    self.exit_system()
                    if self.dead:
                        return
                if arg_number == 0:
                    continue
                for ind in range(len(arg_types)):
                    tok: Token = line[ind + token_pos + 1]
                    arg = arg_types[ind]
                    if arg == "r" and tok.TokenType != TokenType.REGISTER:
                        self.error("Expected a REGISTER, got a {typ}".format(typ=tok.TokenType.value), -1, True,
                                   instruction=token.value.upper())
                        self.exit_system()
                        if self.dead:
                            return
                    if arg == "a" and tok.TokenType != TokenType.VARIABLE:
                        self.error("Expected a VARIABLE or ADDRESS, got a {typ}".format(typ=tok.TokenType.value),
                                   -1, True, instruction=token.value.upper())
                        self.exit_system()
                        if self.dead:
                            return
                    if arg == "c" and not tok.constant:
                        self.error("Expected a CONSTANT, got a {typ}".format(typ=tok.TokenType.value), -1, True,
                                   instruction=token.value.upper())
                        self.exit_system()
                        if self.dead:
                            return
                continue

    @property
    def memory(self):
        return get_memory()

    def clear_memory(self):
        clear_memory()

    def to_bin(self):
        return ["".join(line) for line in self.to_bin_list()]

    def to_hex(self):
        return [bin_to_hex("".join(line)) for line in self.to_bin_list()]

    def to_hex2(self):
        try:
            return [bin_to_hex("".join(line), 4) for line in self.to_bin_list2()]
        except TypeError:
            print("...")

    def to_hex3(self, m=None):
        # clear_memory()
        if m is None:
            m, _ = self.to_memory_2()
        try:
            bin_memory = [m[i] + m[i + 1] for i in range(0, len(m), 2)]
            hm = [bin_to_hex(b, 4) if b != "XXXXXXXXXXXXXXXX" else "XXXX" for b in bin_memory]
            return hm
        except TypeError:
            print("...")

    def from_hex(self, hex_lines: list):
        return [hex_to_bin(line, 16) for line in hex_lines]

# inter: Interpreter = Interpreter(Code)
# inter.instruction_check()
# for key in inter.warnings:
#     print(inter.warnings.get(key))
# print(*inter.to_hex2(),sep="\n")
# for key in inter.errors:
#     print(inter.errors.get(key))
# output = open("Output.obj", "w+")
# output.write("\n".join(inter.to_hex()))
# print("Hex code written to Output.obj")
# output.close()
