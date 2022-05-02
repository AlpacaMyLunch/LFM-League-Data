import colorama
import re
import sys
import textwrap
from termcolor import colored as col
from os import get_terminal_size

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
    return output

def clear_terminal():
    print ('\033c')

def replace_print(msg: str):
    sys.stdout.write(f'\r{msg}')
    sys.stdout.flush()





def print_side_by_side(msgs: list, at_a_time: int=2, line_len: int=30, left_margin: int=3, dynamic_height: bool=False, organize_lengths: bool=False, dynamic_at_a_time: bool=False):

    most_lines = 0


    # Word-Wrap the text so it doesn't extend past the defined line_len
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
    # word-wrap complete

    # Organize the list of messages by number of lines, if organize_lengths is True
    if organize_lengths:
        temp = []
        for msg in msgs:
            temp.append('\n'.join(msg))
        temp.sort(key=len, reverse=True)
        msgs = []
        for msg in temp:
            msgs.append(msg.split('\n'))

    # end organize


    if dynamic_at_a_time:
        terminal_columns = get_terminal_size()[0] - left_margin
        new_at_a_time = int(round(terminal_columns / (line_len + (line_len * .25)), 0))
        print(f'{terminal_columns} / ({line_len} + ({line_len} * .25)) = {new_at_a_time}')
        at_a_time = new_at_a_time


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



