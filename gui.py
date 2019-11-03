from tkinter import *
from tkinter import ttk
from tkinter import filedialog
import re
from main import Interpreter as inter
from main import sliceAssig, instructions, bin_to_hex
from time import sleep
global_interpreter = None
stepping = False
step_table = []
Font = "Courier New"  # Courier New
Font_Size = 12
Show_Full_Memory = False

regex_instr = "|".join(instructions[::-1])
line_numbers = []
line_numbers_hex = [None] * 2048


#
# def sliceAssig(l: list, lower: int, upper: int, value) -> list:
#     l[lower:upper] = [value] * (upper - lower)
#     return l


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
    text_hex.config(state=NORMAL)
    text_hex.delete('1.0', END)
    show_line_numbers(text_hex, line_numbers_hex)
    text_hex.config(state=DISABLED)


def show_line_numbers(text: Text, line_num):
    text_lines = text.get("1.0", END).split("\n")
    label_width = 40
    yoffset = 20

    # if len(text_lines) == 1:
    #     for label in line_num:
    #         if label is not None:
    #             label.place(x=-100, y=-100, height=18, width=label_width)

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
            if text_lines[i] != "0000":
                line_num[i].config(bg=rgb(0, 0, 50), fg=rgb(0, 255, 255), text=str(i * 2))
            else:
                line_num[i].config(bg=rgb(10, 10, 10), fg=rgb(125, 125, 125), text=str(i * 2))
        elif line_num == line_numbers_hex:
            line_num[i].config(bg=rgb(25, 25, 25), fg='white')
        line_num[i].place(x=0, y=y + yoffset, height=height, width=label_width)


def compText(*args, step=False):
    global line_numbers_hex, global_interpreter, stepping, step_table
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
    if not step:
        step_table = []
        interpreter.clear_memory()
        _, mem_table = interpreter.to_memory_2()
        hex_lines = interpreter.to_hex3()
    else:
        if not stepping:
            global_interpreter = inter(text_lines)
            interpreter = global_interpreter
        stepping = True
        unpack = interpreter.next()
        if unpack is None:
            print("Stepping is done")
            step_table = []
            return
        c_addr, table = unpack
        step_table+=table
        mem_table = step_table
        m = interpreter.memory
        hex_lines = interpreter.to_hex3(m)
        # bin_memory = [m[i] + m[i + 1] for i in range(0, len(m), 2)]
        # hex_lines = [bin_to_hex(b, 4) if b != "XXXXXXXXXXXXXXXX" else "XXXX" for b in bin_memory]

    if hex_lines is None:
        print("Can't compile due to error.")
        return
    if not Show_Full_Memory:
        hex_lines = hex_lines[:50]
    for hox in hex_lines:
        text_hex.insert(END, hox + "\n")

    for k in mem_table:
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
    f = filedialog.askopenfilename(filetypes=(("ASM  Files", "*.asm"),))
    code = None
    try:
        code = open(f).read()
    except FileNotFoundError:
        return
    if f is None:
        return
    text.delete("1.0", END)
    text.insert("1.0", code)
    formatText(text)


def file_save(*args):
    f = filedialog.asksaveasfile(mode='w', defaultextension=".obj")
    if f is None:
        return
    text2save = str(text_hex.get(1.0, END))
    f.write(text2save)
    f.close()


def toggle_mem(*args):
    global Show_Full_Memory
    Show_Full_Memory = not Show_Full_Memory
    print(Show_Full_Memory)
    if not Show_Full_Memory:
        butt_show_mem.config(text="Show Unused Memory")
    else:
        butt_show_mem.config(text="Hide Unused Memory")


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
text_tables = Text(root, width=40, height=10, bg=rgb((50, 12, 12)), fg="white", font=(Font, Font_Size - 2),
                   highlightthickness=0)
text_hex = Text(root, width=40, height=10, bg=rgb((12, 20, 50)), fg="white", font=(Font, Font_Size - 2),
                highlightthickness=0)
scrollbar = Scrollbar(root, orient="vertical")
scrollbar_hex = Scrollbar(root, orient="vertical")
text.scrollbar = scrollbar
scrollbar.place(x=724, y=20, width=15, height=610)
scrollbar_hex.place(x=90, y=20, width=15, height=610)
scrollbar.config(command=f(text.yview, req=formatText, reqArg=text))
scrollbar_hex.config(command=f(text_hex.yview, req=show_line_numbers, reqArg=[text_hex, line_numbers_hex]))
text.bind("<KeyPress>", (lambda event: formatText(text)))
text.bind("<KeyRelease>", (lambda event: formatText(text)))
text.bind("<MouseWheel>", (lambda event: formatText(text)))
text.config(yscrollcommand=scrollbar.set)
text_hex.config(yscrollcommand=scrollbar_hex.set)
text_hex.bind("<MouseWheel>", (lambda event: show_line_numbers(text_hex, line_numbers_hex)))
text.place(x=150, y=20, height=610, width=524)  # x=200
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
butt_show_mem = Button(root, bg=rgb(25, 25, 25), fg="white", text="Show Unused Memory", command=toggle_mem,
                       highlightthickness=0, font=(Font, Font_Size - 3))
butt_compile = Button(root, bg=rgb(0, 125, 0), fg="white", text="Compile", command=compText, highlightthickness=0)
butt_step= Button(root, bg=rgb(100, 125, 0), fg="white", text="Step", command=(lambda: compText(step=True)), highlightthickness=0)
butt_save.place(x=40, y=0, width=65, height=20)
butt_save_project.place(x=150, y=0, width=80, height=20)
butt_open_project.place(x=230, y=0, width=80, height=20)
butt_show_mem.place(x=0, y=630, width=150, height=20)

butt_compile.place(x=310, y=0, width=60, height=20)
butt_step.place(x=370, y=0, width=80, height=20)
butt_clear.place(x=450, y=0, width=80, height=20)

root.mainloop()
