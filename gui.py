from tkinter import *
from tkinter import ttk
from tkinter import filedialog
import re
from main import Interpreter as inter
from main import sliceAssig, instructions, bin_to_hex
from time import sleep
from Microcontroller import Stoplight, Seven_Segment, get_memory, ASCII_Characters, write_to_memory_from_address, \
    hex_to_bin, hexadecimal

global_interpreter = None
stepping = False
step_table = []
Font = "Courier New"  # Courier New
Font_Size = 12
Show_Full_Memory = False
write_queue = []
regex_instr = "|".join(instructions[::-1])
line_numbers = []
line_numbers_hex = [None] * 2048


def rgb(color, *args):
    if len(args) == 2:
        color = color, args[0], args[1]
    return "#%02x%02x%02x" % color


colors = (rgb(255, 200, 50), rgb(50, 255, 50), rgb(0, 170, 255), rgb(255, 125, 255), rgb(60, 60, 255), rgb(0, 125, 0),
          rgb(0, 125, 125), rgb(10, 10, 10))


def color_mult(t, t2):
    if type(t) == int:
        t = t, t, t
    if type(t2) == int:
        t2 = t2, t2, t2
    r, g, b = t
    r2, g2, b2 = t2
    r, g, b = r / 255, g / 255, b / 255
    r2, g2, b2 = r2 / 255, g2 / 255, b2 / 255
    return r * r2 * 255, g * g2 * 255, b * b2 * 255


def tuple_mult(t, scalar):
    return [e * scalar for e in t]


def refresh_outputs():
    global outputs
    for output in outputs:
        if hasattr(output, 'set_address'):
            output.set_address(output.address)
        output.render


def tk_pos(line: int, index: int):
    return f'{line}.{index}'


def get_pos(pos: str):
    line, index = pos.split(".")
    return int(line), int(index)


class StopLightUI(Stoplight):
    def __init__(self, address, x, y):
        super().__init__(address)
        self.x = x
        self.y = y

    def render(self):
        width = 100
        lrad = 30
        height = 135
        green = (0, self.green[0] * 255, 0), (0, self.green[1] * 255, 0)
        yellow = (self.yellow[0] * 255, self.yellow[0] * 255, 0), (self.yellow[1] * 255, self.yellow[1] * 255, 0)
        red = (self.red[0] * 255, 0, 0), (self.red[1] * 255, 0, 0)
        canvas = Canvas(root, width=width, height=height, highlightthickness=0, bg=rgb(25, 25, 25))
        x = self.x
        y = self.y
        canvas.create_oval(10, 10, lrad + 10, lrad + 10, outline=rgb(125, 0, 0), fill=rgb(*red[0]), width=2)
        canvas.create_oval(10, 20 + lrad, lrad + 10, lrad * 2 + 20, outline=rgb(125, 125, 0), fill=rgb(*yellow[0]),
                           width=2)
        canvas.create_oval(10, lrad * 2 + 32, lrad + 10, lrad * 3 + 32, outline=rgb(0, 125, 0), fill=rgb(*green[0]),
                           width=2)

        canvas.create_oval(60, 10, lrad + 60, lrad + 10, outline=rgb(125, 0, 0), fill=rgb(*red[1]), width=2)
        canvas.create_oval(60, 20 + lrad, lrad + 60, lrad * 2 + 20, outline=rgb(125, 125, 0), fill=rgb(*yellow[1]),
                           width=2)
        canvas.create_oval(60, lrad * 2 + 32, lrad + 60, lrad * 3 + 32, outline=rgb(0, 125, 0), fill=rgb(*green[1]),
                           width=2)
        label = Label(fg='white', bg='black', text='Intermittent')
        if self.intermittent:
            label.place(x=x, y=y - 20, width=width, height=20)
        canvas.place(x=x, y=y)
        binary_setter = Text(root, bg=rgb(125, 125, 125), fg='white', font=(Font, Font_Size - 2), highlightthickness=0)
        binary_setter.place(x=x, y=y + height, width=width - 30, height=20)
        if len(self.memory) > 0:
            binary_setter.insert("1.0", self.memory[0])
        address_setter = Text(root, bg=rgb(125, 125, 125), fg='white', font=(Font, Font_Size - 2), highlightthickness=0)
        address_setter.place(x=x, y=y + height + 20, width=40, height=20)
        address_setter.insert('1.0', hexadecimal(self.address))
        butt2 = Button(root, text="Set Addr", bg=rgb(25, 125, 25), fg='white', font=(Font, Font_Size - 3),
                       highlightthickness=0)
        butt2.place(x=x + 40, y=y + height + 20, width=60, height=20)
        butt = Button(root, text="Set", bg=rgb(25, 125, 25), fg='white', font=(Font, Font_Size - 3),
                      highlightthickness=0)
        butt.place(x=x + width - 30, y=y + height, width=30, height=20)
        butt.config(command=(lambda: self.set_memory(binary_setter.get("1.0", "1.8"), canvas, butt, butt2, label)))
        butt2.config(command=(lambda: self.set_address(int(str(address_setter.get("1.0", "1.5")),16), canvas, butt, butt2, label)))

    def clear_ui(self, canvas=None, *buttons):
        if canvas is not None:
            canvas.delete('all')
        for b in buttons:
            if b is not None:
                b.destroy()

    def set_memory(self, value: str, canvas=None, *buttons):
        if re.match(r'^[01]+$', value):
            value = value.zfill(8)[:8]
        else:
            value = "0" * 8
        self.memory = [value]
        self.set_values()
        self.clear_ui(canvas, *buttons)
        if 0 <= self.address < 4096:
            write_to_memory_from_address(self.address, self.memory[0].zfill(8))
            compText(refresh=True)
        self.render()

    def set_address(self, addr, canvas=None, *buttons):
        # addr = str(int(str(addr), 16))
        addr = str(addr)
        if re.match(r'^[\d]+$', addr):
            addr = int(addr)
        else:
            self.address = -1
            self.set_memory('0', canvas, *buttons)
            return
        if addr >= 4096:
            addr = 4095
        memory = self.memory
        self.address = addr
        if len(memory) > 0:
            if self.memory == '0' * 8:
                self.memory = memory
        self.clear_ui(canvas, *buttons)
        self.set_values()
        self.render()


class SevenSegmentUI(Seven_Segment):
    def __init__(self, address, x, y):
        super().__init__(address)
        self.x = x
        self.y = y
        self.memory = ["00000000"]
        self.set_values()

    def render(self):
        width = 150
        height = 135

        canvas = Canvas(root, width=width, height=height, highlightthickness=0, bg=rgb(25, 25, 25))
        x = self.x
        y = self.y

        L = [(0, 0, 0) if not i else (0, 255, 0) for i in self.lights]
        a = [rgb(*tuple_mult(l, int(self.control))) for l in L]
        b = [rgb(*tuple_mult(l, int(not self.control))) for l in L]

        canvas.create_rectangle(10, 10, 10, 57, fill=a[5], outline=a[5], width=0)  # 5
        canvas.create_rectangle(10, 10, 10 + 60, 10, fill=a[0], outline=a[0], width=0)  # 0
        canvas.create_rectangle(10 + 60, 10, 10 + 60, 57, fill=a[1], outline=a[1], width=0)  # 1
        canvas.create_rectangle(10 + 60, 57, 10 + 60, 57 + 57, fill=a[2], outline=a[2], width=0)  # 2
        canvas.create_rectangle(10, 57 + 57, 10 + 60, 57 + 57, fill=a[3], outline=a[3], width=0)  # 3
        canvas.create_rectangle(10, 57, 10, 57 + 57, fill=a[4], outline=a[4], width=0)  # 4
        canvas.create_rectangle(10, 57, 10 + 60, 57, fill=a[6], outline=a[6], width=0)  # 6

        canvas.create_rectangle(10 + 70, 10, 10 + 70, 10 + 57, fill=b[5], outline=b[5], width=0)
        canvas.create_rectangle(10 + 70, 10, 10 + 130, 10, fill=b[0], outline=b[0], width=0)
        canvas.create_rectangle(10 + 70 + 60, 10, 10 + 70 + 60, 10 + 57, fill=b[1], outline=b[1], width=0)
        canvas.create_rectangle(10 + 70 + 60, 57, 10 + 70 + 60, 57 + 57, fill=b[2], outline=b[2], width=0)
        canvas.create_rectangle(10 + 70, 57 + 57, 10 + 130, 57 + 57, fill=b[3], outline=b[3], width=0)
        canvas.create_rectangle(10 + 70, 57, 10 + 70, 57 + 57, fill=b[4], outline=b[4], width=0)
        canvas.create_rectangle(10 + 70, 57, 10 + 130, 57, fill=b[6], outline=b[6], width=0)

        canvas.place(x=x, y=y)

        binary_setter = Text(root, bg=rgb(125, 125, 125), fg='white', font=(Font, Font_Size - 2), highlightthickness=0)
        binary_setter.place(x=x, y=y + height, width=width - 30, height=20)
        if len(self.memory) > 0:
            binary_setter.insert("1.0", self.memory[0])
        address_setter = Text(root, bg=rgb(125, 125, 125), fg='white', font=(Font, Font_Size - 2), highlightthickness=0)
        address_setter.place(x=x, y=y + height + 20, width=40, height=20)
        address_setter.insert('1.0', hexadecimal(self.address))
        butt2 = Button(root, text="Set Addr", bg=rgb(25, 125, 25), fg='white', font=(Font, Font_Size - 3),
                       highlightthickness=0)
        butt2.place(x=x + 40, y=y + height + 20, width=60, height=20)
        butt = Button(root, text="Set", bg=rgb(25, 125, 25), fg='white', font=(Font, Font_Size - 3),
                      highlightthickness=0)
        butt.place(x=x + width - 30, y=y + height, width=30, height=20)
        butt.config(command=(lambda: self.set_memory(binary_setter.get("1.0", "1.8"), canvas, butt, butt2)))
        butt2.config(command=(lambda: self.set_address(int(str(address_setter.get("1.0", "1.5")),16), canvas, butt, butt2)))

    def clear_ui(self, canvas=None, *buttons):
        if canvas is not None:
            canvas.delete('all')
        for b in buttons:
            if b is not None:
                b.destroy()

    def set_memory(self, value: str, canvas=None, *buttons):
        if re.match(r'^[01]+$', value):
            value = value.zfill(8)[:8]
        else:
            value = "0" * 8
        self.memory = [value]
        self.set_values()
        self.clear_ui(canvas, *buttons)
        if 0 <= self.address < 4096:
            write_to_memory_from_address(self.address, self.memory[0].zfill(8))
            compText(refresh=True)
        self.render()

    def set_address(self, addr, canvas=None, *buttons):
        addr = str(addr)
        # addr = str(int(str(addr), 16))
        if re.match(r'^[\d]+$', addr):
            addr = int(addr)
        else:
            self.address = -1
            self.set_memory('0', canvas, *buttons)
            return
        if addr >= 4096:
            addr = 4095
        memory = self.memory
        self.address = addr
        if len(memory) > 0:
            if self.memory == '0' * 8:
                self.memory = memory
        self.clear_ui(canvas, *buttons)
        self.set_values()
        self.render()


class ASCIICharactersUI(ASCII_Characters):
    def __init__(self, address: int, x, y):
        super().__init__(address)
        self.x = x
        self.y = y

    def render(self):
        width = Font_Size * 8 + 4
        height = Font_Size * 2
        x = self.x
        y = self.y
        l1 = Label(root, bg=rgb(25, 25, 25), fg='white', font=(Font, Font_Size), text="".join(self.ascii_list))
        l1.place(x=x, y=y, width=width, height=height)

        address_setter = Text(root, bg=rgb(125, 125, 125), fg='white', font=(Font, Font_Size - 2), highlightthickness=0)
        address_setter.place(x=x, y=y + height, width=40, height=20)
        address_setter.insert('1.0', hexadecimal(self.address))
        butt2 = Button(root, text="Set Addr", bg=rgb(25, 125, 25), fg='white', font=(Font, Font_Size - 3),
                       highlightthickness=0)
        butt2.place(x=x + 40, y=y + height, width=60, height=20)
        butt2.config(command=(lambda: self.set_address(int(str(address_setter.get("1.0", "1.5")),16), butt2)))

    def clear_ui(self, *buttons):
        for b in buttons:
            if b is not None:
                b.destroy()

    def set_address(self, addr, *buttons):
        # addr = str(int(str(addr), 16))
        addr = str(addr)
        if re.match(r'^[\d]+$', addr):
            addr = int(addr)
        else:
            # print("no")
            self.address = -1
            self.memory = ['00000000'] * 8
            return
        mem = get_memory()
        self.address = addr
        self.memory = mem[addr:addr + 8]
        self.clear_ui(*buttons)
        self.set_values()
        self.render()

def add_to_write_queue(addr, string):
    write_queue.append((addr,string))

def empty_write_queue():
    global write_queue
    for tup in write_queue:
        print(f'Writing to {tup[0]}:  {tup[1]}')
        if tup[0] <= -1:
            continue
        write_to_memory_from_address(tup[0],tup[1])
    write_queue = []

class HexKeyboard(object):
    def __init__(self, addr, x, y):
        self.address = addr
        self.x = x
        self.y = y
        self.buttons = []
        b = Button(root, bg=rgb(25, 25, 25), fg='white', font=(Font, Font_Size), text=f'{0}')
        b.config(command=(lambda: self.sendText(0)))
        self.buttons.append(b)
        b = Button(root, bg=rgb(25, 25, 25), fg='white', font=(Font, Font_Size), text=f'{1}')
        b.config(command=(lambda: self.sendText(1)))
        self.buttons.append(b)
        b = Button(root, bg=rgb(25, 25, 25), fg='white', font=(Font, Font_Size), text=f'{2}')
        b.config(command=(lambda: self.sendText(2)))
        self.buttons.append(b)
        b = Button(root, bg=rgb(25, 25, 25), fg='white', font=(Font, Font_Size), text=f'{3}')
        b.config(command=(lambda: self.sendText(3)))
        self.buttons.append(b)
        b = Button(root, bg=rgb(25, 25, 25), fg='white', font=(Font, Font_Size), text=f'{4}')
        b.config(command=(lambda: self.sendText(4)))
        self.buttons.append(b)
        b = Button(root, bg=rgb(25, 25, 25), fg='white', font=(Font, Font_Size), text=f'{5}')
        b.config(command=(lambda: self.sendText(5)))
        self.buttons.append(b)
        b = Button(root, bg=rgb(25, 25, 25), fg='white', font=(Font, Font_Size), text=f'{6}')
        b.config(command=(lambda: self.sendText(6)))
        self.buttons.append(b)
        b = Button(root, bg=rgb(25, 25, 25), fg='white', font=(Font, Font_Size), text=f'{7}')
        b.config(command=(lambda: self.sendText(7)))
        self.buttons.append(b)
        b = Button(root, bg=rgb(25, 25, 25), fg='white', font=(Font, Font_Size), text=f'{8}')
        b.config(command=(lambda: self.sendText(8)))
        self.buttons.append(b)
        b = Button(root, bg=rgb(25, 25, 25), fg='white', font=(Font, Font_Size), text=f'{9}')
        b.config(command=(lambda: self.sendText(9)))
        self.buttons.append(b)
        b = Button(root, bg=rgb(25, 25, 25), fg='white', font=(Font, Font_Size), text=f'A')
        b.config(command=(lambda: self.sendText('A')))
        self.buttons.append(b)
        b = Button(root, bg=rgb(25, 25, 25), fg='white', font=(Font, Font_Size), text=f'B')
        b.config(command=(lambda: self.sendText('B')))
        self.buttons.append(b)
        b = Button(root, bg=rgb(25, 25, 25), fg='white', font=(Font, Font_Size), text=f'C')
        b.config(command=(lambda: self.sendText('C')))
        self.buttons.append(b)
        b = Button(root, bg=rgb(25, 25, 25), fg='white', font=(Font, Font_Size), text=f'D')
        b.config(command=(lambda: self.sendText('D')))
        self.buttons.append(b)
        b = Button(root, bg=rgb(25, 25, 25), fg='white', font=(Font, Font_Size), text=f'E')
        b.config(command=(lambda: self.sendText('E')))
        self.buttons.append(b)
        b = Button(root, bg=rgb(25, 25, 25), fg='white', font=(Font, Font_Size), text=f'F')
        b.config(command=(lambda: self.sendText('F')))
        self.buttons.append(b)
        b = Button(root, bg=rgb(100, 25, 25), fg='white', font=(Font, Font_Size - 2), text=f'<<')
        b.config(command=(lambda: self.move_addr(-1)))
        self.buttons.append(b)
        b = Button(root, bg=rgb(100, 25, 25), fg='white', font=(Font, Font_Size - 2), text=f'>>')
        b.config(command=(lambda: self.move_addr(1)))
        self.buttons.append(b)
        b = Button(root, bg=rgb(100, 25, 25), fg='white', font=(Font, Font_Size - 4), text=f'ENTER')
        b.config(command=(lambda: self.setText()))
        self.buttons.append(b)
        b = Button(root, bg=rgb(100, 25, 25), fg='white', font=(Font, Font_Size - 4), text=f'Clear')
        b.config(command=(lambda: self.clearText()))
        self.buttons.append(b)
        b3 = Text(root, bg=rgb(125, 125, 125), fg='white', font=(Font, Font_Size - 2), highlightthickness=0)
        b3.insert('1.0', '-1')
        b = Button(root, bg=rgb(25, 125, 25), fg='white', font=(Font, Font_Size - 2), text=f'Set Addr:')
        b.config(command=(lambda: self.set_address(int(b3.get('1.0',END),16))))
        # b = Label(root, bg=rgb(100, 25, 25), fg='white', font=(Font, Font_Size - 2), text=f'ADDR: 0')
        self.buttons.append(b)
        self.buttons.append(b3)
        self.text = Text(root, bg=rgb(125, 125, 125), fg='white', font=(Font, Font_Size - 2), highlightthickness=0)
        self.text.config(state=DISABLED)

    def move_addr(self, val):
        self.address = min(max(-1, self.address + val), 4095)
        self.render()

    def set_address(self, addr):
        self.address = min(max(-1, addr), 4095)
        self.render()

    def setText(self):
        # if global_interpreter is not None:
        #     compText(refresh=True)

        txt = self.text.get('1.0', END)
        # print(txt)
        if len(txt.strip()) == 0:
            return
        add_to_write_queue(self.address,hex_to_bin(txt).zfill(8))
        # write_to_memory_from_address(self.address, hex_to_bin(txt).zfill(8))
        # compText(refresh=True)

    def sendText(self, txt):
        txt = str(txt)
        self.text.config(state=NORMAL)
        self.text.insert(END, txt)
        self.text.config(state=DISABLED)

    def clearText(self):
        self.text.config(state=NORMAL)
        self.text.delete('1.0', END)
        self.text.config(state=DISABLED)

    def render(self):
        width = 40 * 4
        height = 160
        self.text.place(x=self.x, y=self.y, width=width, height=20)
        for i in range(20):
            x = (i % 4) * 40 + self.x
            y = (i // 4) * 20 + self.y + 20
            b = self.buttons[i]
            b.place(x=x, y=y, width=40, height=20)
        self.buttons[20].place(x=self.x, y=5 * 20 + self.y + 20, width=width*(3/4), height=20)
        self.buttons[20].config(text=f"Set Addr: ")
        self.buttons[21].place(x=self.x+width*(3/4), y=5 * 20 + self.y + 20, width=width / 4, height=20)
        self.buttons[21].delete('1.0', END)
        self.buttons[21].insert('1.0', f"{hexadecimal(self.address)}")


def highlight_text(txt, tag_name, lineno, start_char, end_char, bg_color=None, fg_color=None, bold=False):
    txt.tag_add(tag_name, f'{lineno}.{start_char}', f'{lineno}.{end_char}')
    if not bold:
        txt.tag_config(tag_name, background=bg_color, foreground=fg_color)
    else:
        txt.tag_config(tag_name, background=bg_color, foreground=fg_color, font=(Font, Font_Size, "bold"))


def delText(*args):
    text.delete('1.0', END)
    text_hex.config(state=NORMAL)
    text_hex.delete('1.0', END)
    show_line_numbers(text_hex, line_numbers_hex)
    text_hex.config(state=DISABLED)
    compText()


def stop_stepper(*args):
    text_lines = text.get("1.0", END).replace('\n\n','\n')
    if text_lines is None:
        return
    if text_lines.isspace():
        return
    text.delete('1.0', END)
    compText()
    text.insert('1.0',text_lines)
    formatText(text)


def cleanText(*args):
    string: str = text.get('1.0', END)
    new_text = "\t".join(re.split(r'[ \t]+', string))
    text.delete('1.0', END)
    text.insert('1.0', new_text)
    formatText(text)


def show_line_numbers(text: Text, line_num):
    text_lines = text.get("1.0", END).split("\n")
    label_width = 40
    yoffset = 20

    for i in range(len(text_lines)):
        dline = text.dlineinfo(tk_pos(i + 1, 0))
        if dline is None:
            if len(line_num) > i:
                if line_num[i] is None:
                    continue
                line_num[i].place(x=-100, y=-100, height=18, width=label_width)
            continue
        x, y, width, height, baseline = dline
        if len(text_lines[i]) == 0:
            continue

        if line_num[i] is None:
            label = Label(root, bg='black', fg='white', font=(Font, Font_Size), text=str(i + 1))
            label.place(x=0, y=y + yoffset, height=height, width=label_width)
            line_num[i] = label

        if line_num == line_numbers_hex:
            txt = hex(i * 2)[2:].upper()
            if text_lines[i] != "0000":
                line_num[i].config(bg=rgb(0, 0, 50), fg=rgb(0, 255, 255), text=txt)
            else:
                line_num[i].config(bg=rgb(10, 10, 10), fg=rgb(125, 125, 125), text=txt)
        elif line_num == line_numbers_hex:
            line_num[i].config(bg=rgb(25, 25, 25), fg='white')
        line_num[i].place(x=0, y=y + yoffset, height=height, width=label_width)


def compText(*args, step=False, refresh=False):
    global line_numbers_hex, global_interpreter, stepping, step_table, outputs
    text_hex.config(state=NORMAL)
    text_tables.config(state=NORMAL)
    text_hex.delete("1.0", END)
    text_tables.delete("1.0", END)
    text_lines = text.get("1.0", END).upper()
    if global_interpreter is None or not step or not stepping:
        global_interpreter = inter(text_lines)

    interpreter = global_interpreter
    interpreter.instruction_check()

    sleep(0.05)
    c_addr = 0
    hex_lines = None
    if refresh:
        prog_counter = interpreter.get_program_counter()
        mem_table = step_table
        m = interpreter.memory
        empty_write_queue()
        hex_lines = interpreter.to_hex3(m, False)
        interpreter.set_program_counter(prog_counter)
    elif not step:
        step_table = []
        table = []
        last_table = []
        interpreter.clear_memory()
        interpreter.clear_error_set()
        empty_write_queue()
        unpack = interpreter.next2()
        c_addr = 0
        l_addr = -2
        count = 0
        while unpack is not None:
            c_addr, t = unpack
            if t == last_table and c_addr == l_addr:
                count += 1
                # print("DONE")
                # break
            if count >= 2:
                break
            last_table = t
            l_addr = c_addr
            table += t
            unpack = interpreter.next2()
        mem_table = table
        m = interpreter.memory

        hex_lines = interpreter.to_hex3(m)
    else:
        if not stepping:
            global_interpreter = inter(text_lines)
            interpreter = global_interpreter
            interpreter.clear_memory()
            interpreter.clear_error_set()
        stepping = True
        empty_write_queue()
        unpack = interpreter.next2()
        if unpack is None:
            print("Stepping is done")
            step_table = []
            stepping = False
            refresh_outputs()
            compText(refresh=True)
            return
        c_addr, table = unpack
        step_table += table
        mem_table = step_table
        m = interpreter.memory

        hex_lines = interpreter.to_hex3(m)

    if hex_lines is None:
        print("Can't compile due to error.")
        return
    if not Show_Full_Memory:
        hex_lines = hex_lines[:50]
    for hox in hex_lines:
        text_hex.insert(END, hox + "\n")

    # if stepping:
    #     text_tables.insert(END, f'PC |\t{interpreter.get_program_counter()}\n')
    for k in interpreter.get_register_table().split("\n") + mem_table +['\n'] + interpreter.get_error_set().split('\n'):
        if k is None:
            continue
        if type(k) == list:
            continue
        text_tables.insert(END, str(k) + "\n")
    for tag in text_hex.tag_names():
        text_hex.tag_delete(tag)

    text_hex.tag_configure("center", justify='center')
    text_hex.tag_add("center", 1.0, "end")
    text_tables.config(state=DISABLED)
    text_hex.config(state=DISABLED)
    show_line_numbers(text_hex, line_numbers_hex)
    refresh_outputs()


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
            label.place(x=150 - label_width, y=y + yoffset, height=height, width=label_width)
            line_numbers.append(label)
        if len(line) > 0 and not line.isspace():
            if re.match(r'^[\s]+(const)[\s]+[\w]+[\s]+#?[0-9a-fA-F]+([\s]|((//)+.*)*)*$', line):
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
        line_numbers[i].place(x=150 - label_width, y=y + yoffset, height=height, width=label_width)


def getText(*args):
    print(args)


def file_save_project(*args):
    f = filedialog.asksaveasfile(mode='w', defaultextension=".asm")
    if f is None:
        return
    text2save = str(text.get(1.0, END))
    f.write(text2save)
    f.close()


def file_open_project(*args):
    opened_file = filedialog.askopenfilename(filetypes=(("ASM  Files", "*.asm"),))
    code = None
    try:
        code = open(opened_file).read()
    except FileNotFoundError:
        return
    if opened_file is None:
        return
    text.delete("1.0", END)
    text.insert("1.0", code)
    formatText(text)


def file_save(*args):
    file1 = filedialog.asksaveasfile(mode='w', defaultextension=".obj")
    if file1 is None:
        return
    text2save = str(text_hex.get(1.0, END))
    file1.write(text2save)
    file1.close()


def toggle_mem(*args):
    global Show_Full_Memory
    Show_Full_Memory = not Show_Full_Memory
    print(Show_Full_Memory)
    if not Show_Full_Memory:
        butt_show_mem.config(text="Show Full Memory")
    else:
        butt_show_mem.config(text="Hide Full Memory")


def f(*funcs, req=None, reqArg=None):
    def combined_func(*args, **kwargs):
        for F in funcs:
            F(*args, **kwargs)
        if req is not None:
            if type(reqArg) == list:
                req(*reqArg)
            else:
                req(reqArg)

    return combined_func


root = Tk()
root.title("Assembly Interpreter")
root.configure(bg='black')
root.geometry("1024x650")
root.resizable(0, 0)
style = ttk.Style()
text = Text(root, width=40, height=10, bg=rgb((25, 25, 25)), fg="white", font=(Font, Font_Size), highlightthickness=0)
text_tables = Text(root, width=40, height=10, bg=rgb((50, 12, 12)), fg="white", font=(Font, Font_Size - 3),
                   highlightthickness=0)
text_hex = Text(root, width=40, height=10, bg=rgb((12, 20, 50)), fg="white", font=(Font, Font_Size - 2),
                highlightthickness=0)
scrollbar = Scrollbar(root, orient="vertical")
scrollbar_hex = Scrollbar(root, orient="vertical")
text.scrollbar = scrollbar
scrollbar.place(x=530, y=20, width=15, height=610)
scrollbar_hex.place(x=90, y=20, width=15, height=610)
scrollbar.config(command=f(text.yview, req=formatText, reqArg=text))
scrollbar_hex.config(command=f(text_hex.yview, req=show_line_numbers, reqArg=[text_hex, line_numbers_hex]))
text.bind("<KeyPress>", (lambda event: formatText(text)))
text.bind("<KeyRelease>", (lambda event: formatText(text)))
text.bind("<MouseWheel>", (lambda event: formatText(text)))
text.config(yscrollcommand=scrollbar.set)
text_hex.config(yscrollcommand=scrollbar_hex.set)
text_hex.bind("<MouseWheel>", (lambda event: show_line_numbers(text_hex, line_numbers_hex)))
text.place(x=150, y=20, height=610, width=380)  # x=200 #w = 524
text_tables.place(x=744, y=20, height=610, width=1024 - 744)
text_hex.place(x=40, y=20, height=610, width=50)
text_tables.config(state=DISABLED)
text_hex.config(state=DISABLED)
butt_save = Button(root, bg=rgb(25, 25, 25), fg="white", text="Save File", command=file_save, highlightthickness=0)
butt_save_project = Button(root, bg=rgb(25, 25, 25), fg="white", text="Save Project", command=file_save_project,
                           highlightthickness=0)
butt_open_project = Button(root, bg=rgb(25, 25, 25), fg="white", text="Open Project", command=file_open_project,
                           highlightthickness=0)
butt_clear = Button(root, bg="red", fg="white", text="Clear", command=delText, highlightthickness=0)
butt_stop_stepper = Button(root, bg="purple", fg="white", text="Stop", command=stop_stepper, highlightthickness=0)

butt_format = Button(root, bg="blue", fg="white", text="Format Text", command=cleanText, highlightthickness=0)

butt_show_mem = Button(root, bg=rgb(25, 25, 25), fg="white", text="Show Full Memory", command=toggle_mem,
                       highlightthickness=0, font=(Font, Font_Size - 3))
butt_compile = Button(root, bg=rgb(0, 125, 0), fg="white", text="Run", command=compText, highlightthickness=0)
butt_step = Button(root, bg=rgb(100, 125, 0), fg="white", text="Step", command=(lambda: compText(step=True)),
                   highlightthickness=0)
butt_save.place(x=40, y=0, width=65, height=20)
butt_show_mem.place(x=0, y=630, width=150, height=20)
butt_format.place(x=150, y=630, width=150, height=20)
butt_save_project.place(x=150, y=0, width=80, height=20)
butt_open_project.place(x=230, y=0, width=80, height=20)
butt_compile.place(x=310, y=0, width=50, height=20)
butt_step.place(x=360, y=0, width=50, height=20)
butt_stop_stepper.place(x=410, y=0, width=50, height=20)
butt_clear.place(x=460, y=0, width=50, height=20)

sl = StopLightUI(-1, 595, 20)
ss = SevenSegmentUI(-1, 570, 210)
sl.render()
ss.render()
asc = ASCIICharactersUI(-1, 596, 400)
asc.render()
keyboard = HexKeyboard(-1, 565, 460)
keyboard.render()
outputs = [keyboard, asc, ss, sl]
root.mainloop()
