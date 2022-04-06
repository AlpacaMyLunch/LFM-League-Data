from datetime import datetime
from termcolor import colored

from classes.printing import print_side_by_side


class Lap:
    time: str
    sectors: list
    number: int
    valid: bool

    def __init__(self, number: int):
        self.time = ''
        self.sectors = []
        self.number = number
        self.valid = True


    def add_sector(self, sector):
        self.sectors.append(sector)
        self.time = tally_times(self.sectors)


    def print(self):
        print(f'Lap {self.number}:')
        for idx in range(1, 1 + len(self.sectors)):
            sector = self.return_sector(idx)
            sector.print()

        print(f'Total: {self.time}')

    
    def text(self):
        """
        Same as Print, but returns a string instead of output to console
        """

        output = f'Lap {self.number}:\n'
        for idx in range(1, 1 + len(self.sectors)):
            sector = self.return_sector(idx)
            output = f'{output}{sector.text()}\n'

        output = f"{output}Total: {self.time}"
        return output

    def invalidate(self):
        self.valid = False

    def json(self):
        output = {
            'time': self.time,
            'number': self.number,
            'valid': self.valid,
        }

        for idx in range(1, 1 + len(self.sectors)):
            output[f'Sector {idx}'] = self.return_sector(idx).json()

        return output




    def compare_to(self, compare_lap):
        """
        Print a comparison to another lap
        """

        for sector_number in range(1, 4):
            my_sector = self.return_sector(sector_number)
            compare_sector = compare_lap.return_sector(sector_number)
            delta = compare_times(my_sector.time, compare_sector.time)
            print(f'Sector {sector_number}:  {my_sector.time}  |  {compare_sector.time} ({delta})')

        delta = compare_times(self.time, compare_lap.time)
        print(f'Lap:  {self.time}  |  {compare_lap.time} ({delta})')


    def return_sector(self, number):
        for sector in self.sectors:
            if sector.number == number:
                return sector


def compare_times(time_1: str, time_2: str):
    """
    Returns the difference between two times in seconds.
    Accepts Minutes:Seconds.milliseconds
    00:35.927
    """

    t1 = datetime.strptime(time_1, '%M:%S.%f')
    t2 = datetime.strptime(time_2, '%M:%S.%f')

    diff = t2 - t1

    return diff.total_seconds()

def tally_times(sectors):
    
    minutes = 0
    seconds = 0
    milliseconds = 0

    for sector in sectors:
        minutes += int(sector.time[:2])
        seconds += int(sector.time[3:5])
        milliseconds += int(sector.time[6:9])

    
    milliseconds = float(milliseconds / 1000)

    sec = int(str(milliseconds).split('.')[0])
    seconds += sec

    milliseconds = str(round(float(milliseconds - sec), 3)).split('.')[1]

    

    m, s = divmod(seconds, 60)


    seconds = s 
    minutes += m

    if minutes < 10:
        minutes = f'0{minutes}'
    if seconds < 10:
        seconds = f'0{seconds}'

    if len(str(milliseconds)) == 1:
        milliseconds = f'{milliseconds}00'
    elif len(str(milliseconds)) == 2:
        milliseconds = f'{milliseconds}0'
    

    return f'{minutes}:{seconds}.{milliseconds}'