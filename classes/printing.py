import colorama

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


def colored(msg, color, attributes=[]):
    return col(msg, color, attrs=attributes)



def print_side_by_side(msgs: list, at_a_time: int=2, line_len: int=30, left_margin: int=3):

    most_lines = 0
    temp = []
    for msg in msgs:
        msg = msg.split('\n')
        temp.append(msg)
        lines = len(msg)
        if lines > most_lines:
            most_lines = lines

    msgs = temp

    for i in range(0, len(msgs), at_a_time):
        current_messages = msgs[i:i+at_a_time]
        for line_number in range(0, most_lines):
            current_line = ' '  * left_margin
            for msg in current_messages:
                if len(msg) > line_number:
                    new_entry = msg[line_number]
                else:
                    new_entry = ''
                temp_len = len(new_entry)
                current_line = f'{current_line}{new_entry}{" " * (line_len - temp_len)}'
            print(current_line)



