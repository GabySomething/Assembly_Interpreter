from tkinter import *
from tkinter import font as tkfont
from tkinter import ttk
from tkinter.messagebox import showinfo
import re
from main import Interpreter as inter
from main import TokenType

Font = "Courier New"  # Courier New
Font_Size = 12
instructions: list = ['LOAD', 'LOADIM', 'POP', 'STORE', 'PUSH', 'LOADRIND', 'STORERIND', 'ADD', 'SUB', 'ADDIM', 'SUBIM',
                      'AND', 'OR', 'XOR', 'NOT', 'NEG', 'SHIFTR', 'SHIFTL', 'ROTAR', 'ROTAL', 'JMPRIND', 'JMPADDR',
                      'JCONDRIN', 'JCONDADDR', 'LOOP', 'GRT', 'GRTEQ', 'EQ', 'NEQ', 'NOP', 'CALL', 'RETURN']

regex_instr = "|".join(instructions[::-1])
line_numbers = []


def sliceAssig(l: list, lower: int, upper: int, value) -> list:
    l[lower:upper] = [value] * (upper - lower)
    return l


def rgb(color, *args):
    if len(args) == 2:
        color = color, args[0], args[1]
    return "#%02x%02x%02x" % color


colors = (rgb(255, 200, 50), rgb(50, 255, 50), rgb(0, 170, 255), rgb(255, 125, 255), rgb(60, 60, 255), rgb(0, 125, 0),
          rgb(0, 125, 125), rgb(10, 10, 10))


def tk_pos(line: int, index: int):
    return f'{line}.{index}'


def get_pos(pos: str):
    line, index = pos.split(".")
    return int(line), int(index)


def highlight_text(txt, tag_name, lineno, start_char, end_char, bg_color=None, fg_color=None, bold=False):
    txt.tag_add(tag_name, f'{lineno}.{start_char}', f'{lineno}.{end_char}')
    if not bold:
        txt.tag_config(tag_name, background=bg_color, foreground=fg_color)
    else:
        txt.tag_config(tag_name, background=bg_color, foreground=fg_color, font=(Font, Font_Size, "bold"))


def delText(*args):
    text.delete('1.0', END)


def compText(*args):
    text_hex.config(state=NORMAL)
    text_tables.config(state=NORMAL)
    text_hex.delete("1.0", END)
    text_tables.delete("1.0", END)
    text_lines = text.get("1.0", END).upper()
    interpreter = inter(text_lines)
    hex_lines = interpreter.to_hex2()
    for hox in hex_lines:
        if hox != '0000':
            text_hex.insert('1.0', hox + "\n")

    memory = interpreter.to_memory()
    for i in range(len(memory)):
        m = memory[i]
        if m == [0]:
            continue
        text_tables.insert('1.0', "{name}\t| {typ}\t| {addr}\n".format(name=instructions[m[0]], typ="INSTR",
                                                                       addr=hex(i)[2:].upper()))
        # print("NAME: {name}\t| TYPE: {typ}\t| ADDR: {addr}".format(name=instructions[m[0]],typ=TokenType.,addr=hex(i)[2:].upper()))

    # for token_line in token_lines:
    #     for token in token_line:
    #         if token.TokenType == TokenType.LIST_ASSIGN or token.TokenType == TokenType.CONST_ASSIGN:
    #             text_tables.insert('1.0', token.value + token.TokenType + token.org + "\n")

    text_tables.config(state=DISABLED)
    text_hex.config(state=DISABLED)


def formatText(text: Text):
    global line_numbers
    yoffset = 20
    for tag in text.tag_names():
        text.tag_delete(tag)
    positions = []
    new_instr = instructions + ["db", "const", "org"]
    for i in range(len(new_instr) - 1, -3, -1):
        bg = None
        bold = True
        color = colors[0]
        length = StringVar()
        search = r'(?i)(([^\w]{instruction})|(^{instruction}))+(\s)'.format(instruction=new_instr[i])
        if i == -1:
            search = r'[\w]+:[\s]*'
            bold = False
            color = rgb(255, 175, 175)
        if i == -2:
            search = r'(//)+.*'
            bold = False
            color = rgb(100, 255, 100)
        if 7 <= i <= 10:
            color = colors[1]
        elif 11 <= i <= 19:
            color = colors[2]
        elif 20 <= i <= 31:
            color = colors[3]
        elif i == 32 or i == 34:
            bold = False
            color = colors[4]
        elif i == 33:
            bold = False
            color = colors[5]
        pos = text.search(search, "1.0", END, count=length, regexp=True)
        last_pos = 0
        while pos:
            if pos == last_pos:
                break
            last_pos = pos
            line, index = get_pos(pos)
            positions.append([line, index, int(length.get()), color, bg, bold])
            pos = text.search(search, tk_pos(line, index + int(length.get())), stopindex="end", count=length,
                              regexp=True)
        for t in positions:
            highlight_text(text, t[3], t[0], t[1], t[1] + t[2], t[4], t[3], False)
    del positions
    text_lines = text.get("1.0", END).split("\n")
    label_width = 40

    if len(line_numbers) > len(text_lines):
        for i in range(len(line_numbers) - 1, len(text_lines), -1):
            line_numbers[i].destroy()
            del line_numbers[i]

    for i in range(len(text_lines)):
        dline = text.dlineinfo(tk_pos(i + 1, 0))
        if dline is None:
            if len(line_numbers) > i:
                line_numbers[i].place(x=-100, y=-100, height=18, width=label_width)
            continue
        x, y, width, height, baseline = dline
        line = text_lines[i]
        correct = False
        if i >= len(line_numbers):
            label = Label(root, bg='black', fg='white', font=(Font, Font_Size), text=str(i + 1))
            label.place(x=200 - label_width, y=y+yoffset, height=height, width=label_width)
            line_numbers.append(label)
        if len(line) > 0 and not line.isspace():
            if re.match(r'^(const)[\s]+[\w]+[\s]+[0-9a-fA-F]+([\s]|((//)+.*)*)*$', line):
                correct = True
            elif re.match(r'(^[\s]+|(^[\w]+[\s]+))(db)[\s]+[\w]+(([\s]|,)+[\w]+)*([\s]|((//)+.*)*)*$', line):
                correct = True
            elif re.match(r'^[\w]+:([\s]|((//)+.*)*)*$', line):
                correct = True
            elif re.match(r'(^(//)+.*)|(^[\s]+(//)+.*)$', line):
                correct = True
            elif re.match(
                    r'(?i)(((?=[^{instr}])|^[\s]+)([\s]+({instr})))(([\s|,]+([\w]|(#[0-9a-fA-F]))+)*)([\s]|((//)+.*)*)*$'.format(
                        instr=regex_instr + "|org"), line):
                correct = True
            if correct:
                line_numbers[i].config(bg=rgb(0, 125, 0), fg='white')
            else:
                line_numbers[i].config(bg=rgb(255, 0, 0), fg='black')
        else:
            line_numbers[i].config(bg='black', fg='white')
        line_numbers[i].place(x=200 - label_width, y=y+yoffset, height=height, width=label_width)


def getText(*args):
    print(args)


def f(*funcs, req=None, reqArg=None):
    def combined_func(*args, **kwargs):
        for F in funcs:
            F(*args, **kwargs)
        if req is not None:
            req(reqArg)

    return combined_func


root = Tk()
root.configure(bg='black')
root.geometry("1024x650")
root.resizable(0, 0)
style = ttk.Style()
text = Text(root, width=40, height=10, bg=rgb((25, 25, 25)), fg="white", font=(Font, Font_Size))
text_tables = Text(root, width=40, height=10, bg=rgb((50, 12, 12)), fg="white", font=(Font, Font_Size))
text_hex = Text(root, width=40, height=10, bg=rgb((12, 20, 50)), fg="white", font=(Font, Font_Size))
scrollbar = Scrollbar(root, orient="vertical")
text.scrollbar = scrollbar
scrollbar.place(x=724, y=20, width=20, height=630)
scrollbar.config(command=f(text.yview, req=formatText, reqArg=text))
text.bind("<KeyPress>", (lambda event: formatText(text)))
text.bind("<KeyRelease>", (lambda event: formatText(text)))
text.bind("<MouseWheel>", (lambda event: formatText(text)))
text.config(yscrollcommand=scrollbar.set)
text.place(x=200, y=20, height=630, width=524)
text_tables.place(x=744, y=20, height=630, width=1024 - 744)
text_hex.place(x=0, y=20, height=630, width=160)
text_tables.config(state=DISABLED)
text_hex.config(state=DISABLED)
butt_clear = Button(root, bg="red", fg="white", text="Clear", command=delText)
butt_compile = Button(root, bg=rgb(0,125,0), fg="white", text="Compile", command=compText)
butt_clear.place(x=0, y=0, width=40, height=20)
butt_compile.place(x=40, y=0, width=60, height=20)
root.mainloop()
