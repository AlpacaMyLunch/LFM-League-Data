import colorama
import re
import sys
import textwrap
from termcolor import colored as col

colorama.init()

# PRETTY
COLOR_RED = 'red'
COLOR_GREEN= 'green'
COLOR_CYAN = 'cyan'
COLOR_YELLOW = 'yellow'
COLOR_BLUE = 'blue'
COLOR_WHITE = 'white'
COLOR_PURPLE = 'magenta'
COLOR_GREY = 'grey'
# PROMPT_ARROW = colored(' ->> ', COLOR_PROMPT)
# / PRETTY




def len_no_ansi(string):
    return len(re.sub(
        r'[\u001B\u009B][\[\]()#;?]*((([a-zA-Z\d]*(;[-a-zA-Z\d\/#&.:=?%@~_]*)*)?\u0007)|((\d{1,4}(?:;\d{0,4})*)?[\dA-PR-TZcf-ntqry=><~]))', '', string))

def colored(msg, color, attributes=[]):
    output = col(msg, color, attrs=attributes)
    with open('colortest.txt', 'w') as f:
        f.write(output)
    return output

def clear_terminal():
    print ('\033c')

def replace_print(msg: str):
    sys.stdout.write(f'\r{msg}')
    sys.stdout.flush()





def print_side_by_side(msgs: list, at_a_time: int=2, line_len: int=30, left_margin: int=3, dynamic_height=False):

    most_lines = 0
    temp = []
    for msg in msgs:

        while True:
            msg = msg.split('\n')
            breakout = True
            for idx in range(0, len(msg)):
                line = msg[idx]
                if len(line) > line_len:
                    line = textwrap.fill(line, line_len)
                    msg[idx] = line
                    breakout = False
            
            if breakout:
                break
            else:
                msg = '\n'.join(msg)

            


        temp.append(msg)
        lines = len(msg)
        if lines > most_lines:
            most_lines = lines

    msgs = temp

    for i in range(0, len(msgs), at_a_time):
        current_messages = msgs[i:i+at_a_time]
        if dynamic_height:
            most_lines = 0
            for msg in current_messages:
                if len(msg) > most_lines:
                    most_lines = len(msg)

        for line_number in range(0, most_lines):
            current_line = ' '  * left_margin
            for msg in current_messages:
                if len(msg) > line_number:
                    new_entry = msg[line_number]
                else:
                    new_entry = ''
                temp_len = len_no_ansi(new_entry)
                current_line = f'{current_line}{new_entry}{" " * (line_len - temp_len)}'
            print(current_line)



