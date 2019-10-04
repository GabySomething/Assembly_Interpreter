import re
from enum import Enum as E


def sliceAssig(l: list, lower: int, upper: int, value) -> list:
    l[lower:upper] = [value] * (upper - lower)
    return l


def binary(decimal: int, bits: int = 0) -> str:
    s: str = bin(decimal)[2:]
    if len(s) < bits:
        return s.zfill(bits)
    return s


def hexadecimal(decimal: int, bits: int = 0) -> str:
    s: str = hex(decimal)[2:].upper()
    if len(s) < bits:
        return s.zfill(bits)
    return s


def bin_to_hex(binary: str, bits: int = 0) -> str:
    s: str = hex(int(binary, 2))[2:].upper()
    if len(s) < bits:
        return s.zfill(bits)
    return s


def hex_to_bin(hexadecimal: str, bits: int = 0) -> str:
    s: str = bin(int(hexadecimal, 16))[2:].upper()
    if len(s) < bits:
        return s.zfill(bits)
    return s


def isA(element, *what):
    return any(element == val for val in what)


instructions: list = ['LOAD', 'LOADIM', 'POP', 'STORE', 'PUSH', 'LOADRIND', 'STORERIND', 'ADD', 'SUB', 'ADDIM', 'SUBIM',
                      'AND', 'OR', 'XOR', 'NOT', 'NEG', 'SHIFTR', 'SHIFTL', 'ROTAR', 'ROTAL', 'JMPRIND', 'JMPADDR',
                      'JCONDRIN', 'JCONDADDR', 'LOOP', 'GRT', 'GRTEQ', 'EQ', 'NEQ', 'NOP', 'CALL', 'RETURN']

arguments: list = [2, 2, 1, 2, 1, 2, 2, 3, 3, 2, 2, 3, 3, 3, 2, 2, 3, 3, 3, 3, 1, 1, 1, 1, 2, 2, 2, 2, 2, 0, 1, 0]
argument_types: list = ["r,a", "r,c", "r", "r,a", "r", "r,r", "r,r", "r,r,r", "r,r,r", "r,c", "r,c", "r,r,r", "r,r,r",
                        "r,r,r", "r,r", "r,r", "r,r,r", "r,r,r", "r,r,r", "r,r,r", "r", "a", "r", "a", "r,a", "r,r",
                        "r,r", "r,r", "r,r", "0", "a", "0"]

itype: list = [1] * len(instructions)
itype = sliceAssig(itype, 0, 11, 2)
itype[21] = 3
itype[22] = 3
itype[23] = 3
itype[24] = 2
itype[30] = 3
Code = ""
try:
    Code = open(input("Please specify file name: "), "r").read()
except FileNotFoundError:
    print("File does not exist!")
    exit(1)

Code = Code.upper()

# Code = Code.replace(",", "")
# lines = Code.split("\n")
# for l in lines:
#     if len(l) == 0:
#         continue
#     elif len(l.strip()) == 0:
#         continue
#     print(l)

class TokenType(E):
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
    def __init__(self, value, TokenType: TokenType, org: int = -1, form: int = -1, constant: bool = False, line_number: int = -1):
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

    def __init__(self, text: str):
        self.text = text
        self.errors = {}
        self.lines: list = list()
        self.token_lines = list()
        lines = text.replace(",", "").split("\n")
        for l in lines:
            l: str = l
            if "//" in l:
                l = l[:l.index("//")]
            if len(l) == 0:
                continue
            elif len(l.strip()) == 0:
                continue
            if l.startswith("//"):
                continue
            self.lines.append(l)
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
        if re.match("^[0-9]+[0-9a-fA-F]+", word) or re.match("^[0-9]+", word) or re.match("^#[0-9]+", word):
            return TokenType.INTEGER
        if word.endswith(":"):
            return TokenType.LABEL
        if re.match("^R[0-9]+", word):
            if word.lower().replace("r", "").isdigit():
                return TokenType.REGISTER
        return TokenType.VARIABLE

    def get_tokens_in_list(self, l: list, line_number, *Token_Type: TokenType, save_errors: bool = True,
                           is_constant: bool = False):
        tokens: list = list()
        for word in l:
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
            error += "\nLINE: " + str(line_index + 1)
        if instruction.strip() is not "":
            error += "\nINSTRUCTION: " + instruction
        if save_errors and not is_warning:
            self.errors[line_index] = "ERROR: " + error
        elif is_warning:
            self.warnings[line_index] = "WARNING: " + error
        else:
            print(error)

    def set_origin_in_list(self, l: list, org: int):
        for token in l:
            if type(token) == Token:
                token.org = org
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
        if line[0] == " ":
            words = [w.strip() for w in line.split()]
            next_tokens: list = line[1:]
            first_token_type = self.token_type(words[0])
            if first_token_type == TokenType.INSTRUCTION:
                if origin % 2 != 0:
                    origin += 1
                index: int = instructions.index(words[0])
                tokens.append(Token(words[0], first_token_type, itype[index]))
                tokens += self.get_tokens_in_list(words[1:], line_number, TokenType.REGISTER, TokenType.INTEGER,
                                                  TokenType.VARIABLE, save_errors=save_errors)
                tokens = self.set_origin_in_list(tokens, origin)
                origin += 2  ################
            elif first_token_type == TokenType.LIST_ASSIGN:
                tokens.append(Token(words[0], first_token_type, -2))
                tokens += self.get_tokens_in_list(words[1:], line_number, TokenType.INTEGER, save_errors=save_errors)
                tokens = self.set_origin_in_list(tokens, origin)
                origin += 1  ################
            elif first_token_type == TokenType.ORG:
                if len(words) != 2:
                    self.error("Invalid token, origin not set correctly", line_number, save_errors)
                    return None, origin
                org: int = int(words[1], 16)
                if origin > org:
                    self.error("Possible risk of overwriting addresses.", line_number, False, True)
                origin = org
                tokens.append(Token(words[0], first_token_type, org))
                tokens.append(Token(org, TokenType.INTEGER, org))
            else:
                self.error("Invalid token, the second column is only for instructions", line_number, save_errors)
                return None, origin
        else:
            words = [w.strip() for w in line.split()]
            next_tokens: list = words[1:]
            first_token_type = self.token_type(words[0])
            if first_token_type == TokenType.LABEL:
                # if origin % 2 != 0:
                #     origin += 1
                tokens.append(Token(words[0].replace(":", ""), TokenType.LABEL, origin))
                # origin += 2  ################
                if len(words) >= 3:
                    token_type = self.token_type(words[1])
                    if token_type != TokenType.INSTRUCTION:
                        self.error("Invalid token, can't have a {type} after a label".format(type=token_type),
                                   line_number, save_errors)
                    else:
                        if origin % 2 != 0:
                            origin += 1
                        tokens.append(
                            Token(words[1], TokenType.INSTRUCTION, origin, itype[instructions.index(words[1])]))
                    tokens += self.get_tokens_in_list(words[2:], line_number, TokenType.REGISTER, TokenType.INTEGER,
                                                      TokenType.VARIABLE, save_errors=save_errors)
                    tokens = self.set_origin_in_list(tokens, origin)
                    origin += 2
                elif len(words) > 1 and len(words) < 3:
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
                    # self.variables[words[0]] = [integer.value for integer in integers]
                    bits_used: int = len(integers)
                    tokens += integers
                    tokens = self.set_origin_in_list(tokens, origin)
                    origin += bits_used  ################
                else:
                    self.error("Invalid token, you must assign the variable with the instruction db", line_number,
                               save_errors)
                    return None, origin
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
                    # origin += 1  ################
                else:
                    self.error("Invalid token, after declaring const, you must declare a variable name", line_number,
                               save_errors)
                    return None, origin
        if len(tokens) <= 0:
            self.error("Bad formatting", line_number, save_errors)
            return None, origin
        return tokens, origin

    # def make_tokens(self):
    #     token_lines: list = list()
    #     origin: int = 0
    #     for i in range(len(self.lines)):
    #         l: str = self.lines[i]
    #         tokens: list = list()
    #         if l[0] == " ":
    #             words = [w.strip() for w in l.split()]
    #             next_tokens: list = l[1:]
    #             first_token_type = self.token_type(words[0])
    #             if first_token_type == TokenType.INSTRUCTION:
    #                 if origin % 2 != 0:
    #                     origin += 1
    #                 index: int = instructions.index(words[0])
    #                 tokens.append(Token(words[0], first_token_type, itype[index]))
    #                 tokens += self.get_tokens_in_list(words[1:], i, TokenType.REGISTER, TokenType.INTEGER,
    #                                                   TokenType.VARIABLE)
    #                 tokens = self.set_origin_in_list(tokens, origin)
    #                 origin += 2  ################
    #             elif first_token_type == TokenType.LIST_ASSIGN:
    #                 tokens.append(Token(words[0], first_token_type, -2))
    #                 tokens += self.get_tokens_in_list(words[1:], i, TokenType.INTEGER)
    #                 tokens = self.set_origin_in_list(tokens, origin)
    #                 origin += 1  ################
    #             elif first_token_type == TokenType.ORG:
    #                 if len(words) != 2:
    #                     self.error("Invalid token, origin not set correctly", i)
    #                     token_lines.append(None)
    #                     continue
    #                 org: int = int(words[1], 16)
    #                 origin = org
    #                 tokens.append(Token(words[0], first_token_type, org))
    #                 tokens.append(Token(org, TokenType.INTEGER, org))
    #             else:
    #                 self.error("Invalid token, the second column is only for instructions", i)
    #                 token_lines.append(None)
    #                 continue
    #         else:
    #             words = [w.strip() for w in l.split()]
    #             next_tokens: list = words[1:]
    #             first_token_type = self.token_type(words[0])
    #             if first_token_type == TokenType.LABEL:
    #                 if origin % 2 != 0:
    #                     origin += 1
    #                 tokens.append(Token(words[0].replace(":", ""), TokenType.LABEL, origin))
    #                 origin += 2  ################
    #                 # continue
    #             elif first_token_type == TokenType.VARIABLE:
    #                 if len(words) < 3:
    #                     self.error("Invalid token, too few arguments", i)
    #                     token_lines.append(None)
    #                     continue
    #                 if words[1] == "db":
    #                     tokens.append(Token(words[0], first_token_type))
    #                     tokens.append(Token(words[1], TokenType.LIST_ASSIGN))
    #                     integers = self.get_tokens_in_list(words[2:], i, TokenType.INTEGER)
    #                     # self.variables[words[0]] = [integer.value for integer in integers]
    #                     tokens += integers
    #                     tokens = self.set_origin_in_list(tokens, origin)
    #                     origin += 1  ################
    #                 else:
    #                     self.error("Invalid token, you must assign the variable with the instruction db", i)
    #                     token_lines.append(None)
    #                     continue
    #             elif first_token_type == TokenType.CONST_ASSIGN:
    #                 if len(words) < 3:
    #                     self.error("Invalid token, too few arguments", i)
    #                     token_lines.append(None)
    #                     continue
    #                 if self.token_type(words[1]) == TokenType.VARIABLE:
    #                     tokens.append(Token(words[0], first_token_type))
    #                     tokens.append(Token(words[1], TokenType.VARIABLE))
    #                     tokens += self.get_tokens_in_list(words[2:], i, TokenType.INTEGER)
    #                     tokens = self.set_origin_in_list(tokens, origin)
    #
    #                     origin += 1  ################
    #                 else:
    #                     self.error("Invalid token, after declaring const, you must declare a variable name", i)
    #                     token_lines.append(None)
    #                     continue
    #         if len(tokens) <= 0:
    #             self.error("No tokens found", i)
    #             token_lines.append(None)
    #             continue
    #         token_lines.append(tokens)
    #     self.token_lines = token_lines
    #     return token_lines

    def make_tokens_2(self, save_errors: bool = True):
        token_lines: list = list()
        org: int = 0
        for i in range(len(self.lines)):
            line: str = self.lines[i]
            tokens, org = self.get_tokens_from_line(line, i, org, save_errors)
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
            # print(tokens)
            token_lines.append(tokens)
        self.token_lines = token_lines
        return token_lines

    def is_clean(self):
        if len(self.token_lines) == 0:
            self.make_tokens_2()
        if None in self.token_lines:
            return False
        return len(self.errors) == 0

    def exit_system(self,code: int=1):
        for k in self.warnings:
            print(self.warnings.get(k))
        for k in self.errors:
            print(self.errors.get(k))
        exit(code)

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
                        # decimal_line.append(token.org)
                        var = self.get_variable(token.value)
                        if type(var) == list:
                            decimal_line.append(int(str(var[0]), 16))
                            # decimal_line += [int(str(v), 16) for v in var]
                        else:
                            if type(var) == str:
                                var = int(var, 16)
                            if var is None:
                                self.error("Variable "+token.value+" is not defined")
                                self.exit_system()
                            decimal_line.append(var)
                    if token.TokenType == TokenType.INTEGER or token.TokenType == TokenType.REGISTER:
                        var = token.value
                        if type(var) == str:
                            var = int(var, 16)
                        decimal_line.append(var)

                decimal_lines.append(decimal_line)
        if decimal_lines is None:
            self.exit_system()
        return decimal_lines

    def to_bin_list(self):
        decimal_lines: list = self.to_decimal()
        binary_lines: list = list()
        if decimal_lines is None:
            self.exit_system()
        for line in decimal_lines:
            if line is None:
                self.exit_system()
            binary_line: list = list()
            instr_format: int = itype[line[0]]
            bits: int = 16  ##bits
            binary_line.append(binary(line[0], 5))  ##4 bits????
            bits -= 5  ##4 bits?
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
                bits = 0
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
                if arg_number == 0:
                    continue
                for ind in range(len(arg_types)):
                    tok: Token = line[ind + token_pos + 1]
                    arg = arg_types[ind]
                    if arg == "r" and tok.TokenType != TokenType.REGISTER:
                        self.error("Expected a REGISTER, got a {typ}".format(typ=tok.TokenType.value), -1, True,
                                   instruction=token.value.upper())
                        self.exit_system()
                    if arg == "a" and tok.TokenType != TokenType.VARIABLE:
                        self.error("Expected a VARIABLE or ADDRESS, got a {typ}".format(typ=tok.TokenType.value),
                                   -1, True, instruction=token.value.upper())
                        self.exit_system()
                    if arg == "c" and not tok.constant:
                        self.error("Expected a CONSTANT, got a {typ}".format(typ=tok.TokenType.value), -1, True,
                                   instruction=token.value.upper())
                        self.exit_system()
                continue

    def to_bin(self):
        return ["".join(line) for line in self.to_bin_list()]

    def to_hex(self):
        return [bin_to_hex("".join(line)) for line in self.to_bin_list()]

    def from_hex(self, hex_lines: list):
        return [hex_to_bin(line, 16) for line in hex_lines]


lex: Interpreter = Interpreter(Code)
lex.instruction_check()
for k in lex.warnings:
    print(lex.warnings.get(k))

for k in lex.errors:
    print(lex.errors.get(k))
output = open("Output.obj", "w+")
output.write("\n".join(lex.to_hex()))
print("Hex code written to Output.obj")
output.close()
