import requests
import json
import time
from classes.printing import COLOR_CYAN, print_side_by_side, replace_print

from classes.sector import Sector
from classes.lap import Lap

from datetime import datetime
from termcolor import colored
from os import path

# PRETTY
COLOR_RED = 'red'
COLOR_GREEN= 'green'
COLOR_PROMPT = 'cyan'
COLOR_YELLOW = 'yellow'
COLOR_REDORANGE = 'redorange'
COLOR_GREENYELLOW = 'greenyellow'
COLOR_WHITE = 'white'
COLOR_PURPLE = 'magenta'
COLOR_GREY = 'grey'
PROMPT_ARROW = colored(' ->> ', COLOR_PROMPT)
# colorama.init()
# / PRETTY

BASE_URL = 'https://api2.lowfuelmotorsport.com/api/'

SESSION_CACHE_DIR = './json/session_cache/'

class Race:
    session_id: int
    track: str
    date: str
    epoch: int
    laps: list
    weather: dict
    split: int
    car_class: str
    car_name: str
    car_year: int
    start_position: int
    finish_position: int
    incidents: int
    mandatory_pitstops: int
    chat: list
    best_lap: str
    total_time: str
    dnf: bool
    dns: bool
    gap: str
    best: dict
    opponents: list
    url: str
    analysis: dict
    event_id: int
    driver_elo: int
    driver_safety_rating: float
    valid_laps: int
    valid_lap_percentage: float
    invalid_laps: int
    invalid_lap_percentage: float
    countable_laps: int

    def __init__(self, session_id: int, driver_id: int):

        self.start_position = 0
        self.finish_position = 0
        self.split = None
        self.opponents = []

        self.session_id = session_id

        data = gather_data(session_id)

        self.track = data['track']['track_name']
        self.date = data['race_date']
        self.epoch = date_to_epoch(self.date)
        self.weather = {
                'ambient': data['server_settings']['server_settings']['event']['data']['ambientTemp'],
                'clouds': data['server_settings']['server_settings']['event']['data']['cloudLevel'],
                'rain': data['server_settings']['server_settings']['event']['data']['rain'],
                'randomness': data['server_settings']['server_settings']['event']['data']['weatherRandomness']
            }
        self.event_id = data['event_id']
        self.url = f'https://lowfuelmotorsport.com/events/{self.event_id}/race/{self.session_id}'
        self.mandatory_pitstops = data['event']['settings']['season_event_settings']['default_server_settings']['pitstop_mandatory']
        self.chat = data['chat']

        self.laps = []

        self.best = {}

        extracted = extract_laps(data, driver_id)

        self.laps = extracted['laps']
        self.best = extracted['best']
        self.analysis = extracted['analysis']
        self.best_lap = extracted['best_lap']
        self.car_class = extracted['car_class']
        self.car_name = extracted['car_name']
        self.car_year = extracted['car_year']
        self.total_time = extracted['total_time']
        self.dnf = extracted['dnf']
        self.dns = extracted['dns']
        self.gap = extracted['gap']
        self.incidents = extracted['incidents']
        self.split = extracted['split']
        self.driver_elo = extracted['elo']
        self.driver_safety_rating = extracted['safety_rating']
        
        self.invalid_laps = 0
        self.valid_laps = 0
        for lap in self.laps:
            # Don't count the first lap.  Sometimes the game says it's invalid for no reason.... also says the lap takes ____ minutes.
            if lap.number != 1:
                if not lap.valid:
                    self.invalid_laps += 1
                else:
                    self.valid_laps += 1
                    

        if self.mandatory_pitstops:
            if self.invalid_laps > 1:
                self.invalid_laps -= 2
                # Pitstop will invalidate two laps


        self.countable_laps = 0
        self.invalid_lap_percentage = 0
        self.valid_lap_percentage = 0
        if not self.dns:
            if len(self.laps) > 0:
                
                # we are not going to count the first lap
                self.countable_laps = len(self.laps) - 1

                if self.mandatory_pitstops:
                    if self.invalid_laps > 1:
                        # Best way to tell if they had a pitstop.
                        # It was mandatory AND they have at least 2 invalid laps
                        self.countable_laps -= 2

                if self.invalid_laps > 0:
                    self.invalid_lap_percentage = percentage(self.invalid_laps, self.countable_laps)

                if self.valid_laps > 0:
                    self.valid_lap_percentage = percentage(self.valid_laps, self.countable_laps)

        
        


        
        if self.split == None:
            self.split = -1

        self.opponents = extract_opponent_list(data, self.split)



    def json(self):
        output = {
            'session_id': self.session_id,
            'track': self.track,
            'date': self.date,
            'weather': self.weather,
            'split': self.split,
            'car_class': self.car_class,
            'car_name': self.car_name,
            'car_year': self.car_year,
            'start_position': self.start_position,
            'finish_position': self.finish_position,
            'incidents': self.incidents,
            'mandatory_pitstops': self.mandatory_pitstops,
            'best_lap': self.best_lap,
            'total_time': self.total_time,
            'dnf': self.dnf,
            'dns': self.dns,
            'gap': self.gap,
            'chat': self.chat,
            'laps': [],
            'url': self.url,
            'driver_elo': self.driver_elo,
            'driver_safety_rating': self.driver_safety_rating,
            'opponents': self.opponents,
            'invalid_laps': self.invalid_laps,
            'invalid_lap_percentage': self.invalid_lap_percentage,
            'valid_laps': self.valid_laps,
            'valid_lap_percentage': self.valid_lap_percentage,
            'countable_laps': self.countable_laps
        }

        if 'hypothetical' in self.analysis:
            output['hypothetical_best'] = self.analysis['hypothetical'].json(),
        else:
            output['hypothetical_best'] = None

        if 'average' in self.analysis:
            output['averages'] = self.analysis['average'].json(),
        else:
            output['averages'] = None

        for lap in self.laps:
            output['laps'].append(lap.json())

        return output



    def set_start_position(self, position: int):
        self.start_position = position

    def set_finish_position(self, position: int):
        self.finish_position = position

    def print(self):
        print(f"{self.track} | {self.date}")
        print(f'{self.car_year} {self.car_name} ({self.car_class})')
        print(self.url)
        if self.dns:
            print(colored('DID NOT START', 'red'))
            return
        elif self.dnf:
            print(colored('DID NOT FINISH', 'red'))
            if len(self.laps) < 1:
                return

        finish = self.finish_position
        if finish < self.start_position:
            finish = colored(f'P{finish}', 'green')
        elif finish > self.start_position:
            finish = colored(f'P{finish}', 'red')
        else:
            finish = f'P{finish}'
        print(f'P{self.start_position} -> to -> {finish}')

        print(f'{self.incidents} incidents.  {self.mandatory_pitstops} mandatory pitstops.  {self.invalid_lap_percentage}% invalid laps')
        
        print(f'Gap to P1: {self.gap}')
        print(f'Split {self.split}')
        
        

        
        output = []
        for lap in self.laps:

            if lap.valid:
                temp = f'Lap {lap.number}\n'
            else:
                temp = f'Lap {lap.number} (x)\n'

            for sector_number in range(1, 4):
                sector_header = f'Sector {sector_number}'
                sector = lap.return_sector(sector_number)
                temp = f'{temp}{sector_header}: {colored(sector.time, pretty_time(sector.time, self.best[f"{sector_header}"], lap.valid))}\n'
            
            temp = f'{temp}Total: {colored(lap.time, pretty_time(lap.time, self.best["total"], lap.valid))}\n' 

            output.append(temp)

        print_side_by_side(output, line_len=25, dynamic_at_a_time=True)




        print('')
        hypothetical = 'Hypothetical\n' + self.analysis['hypothetical'].text()
        average = 'Average\n' + self.analysis['average'].text()
        consistency = 'Consistency\n\n'
        for key in self.analysis['consistency']:
            consistency = f'{consistency}{key}: +/- {self.analysis["consistency"][key]}\n'

        print_side_by_side([hypothetical, average, consistency], 3, 30)






    def show_opponents(self):
        messages = []
        for opponent in self.opponents:
            
            msg = f"{opponent['name']} ({opponent['id']})\n"
            msg = f"{msg}P{opponent['finish']} ({opponent['fastest']}) in a {opponent['car']}\n"
            messages.append(msg)

        print_side_by_side(messages, 3, 65)

    def compare(self, opponent_id: int):
        """
        Compare my race to this opponent
        """

        race_data = gather_data(self.session_id)

        opponent = return_opponent(self.opponents, opponent_id)
        opponent_lap_data = extract_laps(race_data, opponent_id)


        print('')
        print(f"    COMPARISON vs {opponent['name']}")
        print('')

        driver_best = self.best['total']
        opponent_best = opponent['fastest']
        print('    Fastest Lap')
        print(f'{driver_best}  |  {opponent_best}')

        print('')
        print('    Average Lap Breakdown')
        self.analysis['average'].compare_to(opponent_lap_data['analysis']['average'])

        print('\n\n   COMPARE V2 \n\n')

        
        # Drivers might have a different number of laps
        # Let's find the highest number

        opponent_laps = opponent_lap_data['laps']
        max_laps = len(self.laps)
        if len(opponent_laps) > max_laps:
            max_laps = len(opponent_laps)

        output = []
        separator = '   '

        for lap_index in range(0, max_laps):
            if lap_index < len(self.laps):
                driver_lap = self.laps[lap_index]
            else:
                driver_lap = None

            if lap_index < len(opponent_laps):
                opponent_lap = opponent_laps[lap_index]
            else:
                opponent_lap = None

            temp = f'Lap {1 + lap_index}:\n'
            for sector_number in range(1, 4):
                sector_header = f'Sector {sector_number}'
                


                driver_sector_color = "green"
                opponent_sector_color = "white"
                                
                if driver_lap == None:
                    driver_sector_time = 'N/A'
                    driver_sector_color = "white"
                    opponent_sector_color = "green"
                else:
                    driver_sector_time = driver_lap.return_sector(sector_number).time

                if opponent_lap == None:
                    opponent_sector_time = 'N/A'
                    opponent_sector_color = "white"
                else:
                    opponent_sector_time = opponent_lap.return_sector(sector_number).time
                    if driver_sector_time != "N\A":
                        if compare_times(driver_sector_time, opponent_sector_time) < 0:
                            driver_sector_color = "white"
                            opponent_sector_color = "green"

                temp = f'{temp}{sector_header}: {colored(driver_sector_time, driver_sector_color)}{separator}{colored(opponent_sector_time, opponent_sector_color)}\n'

                            
            
            total_header = f'Total'
            
            if driver_lap == None:
                driver_lap_time = "N\A"
                driver_lap_color = "white"
                opponent_lap_color = "green"
            else:
                driver_lap_time = driver_lap.time
                driver_lap_color = "green"
                opponent_lap_color = "white"

            if opponent_lap == None:
                opponent_lap_time = "N\A"
                opponent_lap_color = "white"
            else:
                opponent_lap_time = opponent_lap.time
                if driver_lap_time != 'N\A':
                    if compare_times(driver_lap_time, opponent_lap_time) < 0:
                        driver_lap_color = "white"
                        opponent_lap_color = "green"


            if driver_lap:
                if driver_lap.valid == False:
                    driver_lap_color = 'red'
            if opponent_lap:
                if opponent_lap.valid == False:
                    opponent_lap_color = 'red'

            temp = f'{temp}{total_header}: {colored(driver_lap_time, driver_lap_color)}{separator}{colored(opponent_lap_time, opponent_lap_color)}\n'
            output.append(temp)

        print_side_by_side(output, line_len=40, dynamic_at_a_time=True)







def return_opponent(opponent_list, opponent_id):
    for opponent in opponent_list:
        if opponent['id'] == opponent_id:
            return opponent

    return None

def extract_opponent_list(data: dict, split: int):
    opponents = []
    for data_split in data['race_results_splits']:
        if type(data_split) == dict:
            for xcar_class in data_split:
                results = data_split[xcar_class]['OVERALL']
                for result in results:
                    if result['split'] == split:
                        driver_id = result['driver_id']
                        driver_name = f"{result['vorname']} {result['nachname']}"
                        opponents.append(
                            {
                                'name': driver_name, 
                                'id': driver_id,
                                'finish': result['position'],
                                'fastest': result['bestlap'],
                                'car': f"{result['year']} {result['car_name']}",
                                'dns': bool(result['dns']),
                                'dnf': bool(result['dnf'])
                                }
                        )
    
    return opponents


def extract_laps(data: dict, driver_id: int):

    best = {}
    analysis = {}
    laps = []


    sector_analysis = {}
    split = None
    best_lap = None
    car_class = None
    car_name = None
    car_year = None
    total_time = None
    dnf = None
    dns = None
    gap = None
    incidents = 0
    name = None
    elo = None
    sr = None



    for data_split in data['race_results_splits']:
        if type(data_split) == dict:
            for xcar_class in data_split:
                results = data_split[xcar_class]['OVERALL']
                for result in results:
                    if result['driver_id'] == driver_id:
                        sr = result['safety_rating']
                        elo = result['rating']
                        if result['ratingGain'] != None:
                            elo += result['ratingGain']
                        data_laps = result['lapDetail']

                        laps_added = []
                        for data_lap in data_laps:
                            
                            lap_number = data_lap['car_lap']
                            if lap_number not in laps_added:
                                laps_added.append(lap_number)
                                lap = Lap(lap_number)
                                if data_lap['lap_valid'] == 0:
                                    lap.invalidate()

                                sector_counter = 1
                                for data_sector in data_lap['splits']:
                                    sector_header = f'Sector {sector_counter}'
                                    if sector_header not in sector_analysis:
                                        sector_analysis[sector_header] = []
                                    if lap.valid:
                                        if lap.number != 1:
                                            try:
                                                sector_analysis[sector_header].append(data_sector)
                                            except:
                                                print('')
                                                print(f'Problem in lap {lap.number}, {sector_header}\n\n')
                                        if sector_header not in best:
                                            best[sector_header] = data_sector

                                        else:
                                            compared = compare_times(best[sector_header], data_sector)
                                            if compared < 0:
                                                best[sector_header] = data_sector

                                    sector = Sector(data_sector, sector_counter)
                                    sector_counter += 1
                                    lap.add_sector(sector)

                                
                                if lap.valid:
                                    if 'total' not in best:
                                        best['total'] = lap.time
                                    else:
                                        compared = compare_times(best['total'], lap.time)
                                        if compared < 0:
                                            best['total'] = lap.time

                                laps.append(lap)


                        hypothetical_lap = Lap(-1)
                        for xbest in best:
                            if 'Sector' in xbest:
                                hypothetical_lap.add_sector(
                                    Sector(
                                        best[xbest], 
                                        int(xbest.replace('Sector ', ''))
                                        )
                                    )
                        analysis['hypothetical'] = hypothetical_lap

                        analysis['consistency'] = {}

                        for key in sector_analysis:
                            minmax = min_max(sector_analysis[key])
                            analysis['consistency'][key] = abs(compare_times(minmax['min'], minmax['max']))
                            sector_analysis[key] = average_time(sector_analysis[key])


                        average_lap = Lap(-2)
                        for sector_number in range(1, 4):
                            sector_key = f'Sector {sector_number}'
                            if sector_key in sector_analysis:
                                avg_sector = Sector(sector_analysis[sector_key], sector_number)
                                average_lap.add_sector(avg_sector)


                        analysis['average'] = average_lap

                        best_lap = result['bestlap']
                        split = result['split']
                        car_class = result['class']
                        car_name = result['car_name']
                        car_year = result['year']
                        total_time = result['time']
                        dnf = bool(result['dnf'])
                        dns = bool(result['dns'])
                        gap = result['gap']
                        incidents = result['incidents']
                        name = f"{result['vorname']} {result['nachname']}"
                        break

    if not split:
        split = -1
    return {
        'best': best,
        'laps': laps,
        'best_lap': best_lap,
        'split': split,
        'car_class': car_class,
        'car_name': car_name,
        'car_year': car_year,
        'total_time': total_time,
        'dnf': dnf,
        'gap': gap,
        'dns': dns,
        'incidents': incidents,
        'name': name,
        'analysis': analysis,
        'elo': elo,
        'safety_rating': sr
    }



def average_time(time_list: list):

    if len(time_list) == 0:
        return '00:00.000'

    minutes = 0
    seconds = 0
    milliseconds = 0

    for t in time_list:
        minutes += int(t[:2])
        seconds += int(t[3:5])
        milliseconds += int(t[6:9])

    milliseconds = float(milliseconds / 1000)

    total_seconds = seconds + (minutes * 60) + milliseconds
    
    m, s = divmod(total_seconds / len(time_list), 60)

    m = int(m)
    if m < 10:
        m = f'0{m}'
    s = round(s, 3)
    if s < 10:
        s = f'0{s}'

    new_milliseconds = str(s).split('.')[1]
    if len(new_milliseconds) == 1:
        s = f'{s}00'
    elif len(new_milliseconds) == 2:
        s = f'{s}0'

    return f'{m}:{s}'
        
def percentage(part, whole):
    return (round(100 * float(part)/float(whole), 1))

def pretty_time(time_value, best_value, valid_lap=True):
    """
    Figure out what color time_value should be when printed
    by comparing it to the best_value.

    Best = Purple
    Within .250 = Green
    .251 - .75 = Yellow
    .751 - 1 = Redorange
    >1 = red
    """

    if valid_lap == False:
        return COLOR_WHITE

    comparison = compare_times(best_value, time_value)

    if comparison > 1:
        return COLOR_RED

    elif comparison > .5:

        return COLOR_YELLOW

    elif comparison > 0:
        return COLOR_GREEN

    else:
       return COLOR_PURPLE

def gather_data(session_id: int):
    replace_print(f'gathering session {session_id}  ')
    cache = load_cache(session_id)
    if cache:
        return cache

    url = f'{BASE_URL}race/{session_id}'

    request = http_request(url)
    data = request.json()
    save_cache(session_id, data)

    return data

def http_request(url: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"
        }
    
    attempts = 0
    while True:
        try:
            attempts += 1
            req = requests.get(url, headers=headers)
            if req.ok:
                return req
        except:
            time.sleep(attempts * 0.5)

        if attempts > 5:
            print(colored(f'    ... problems with http requests on {url}', 'red'))
            print('')


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

def date_to_epoch(date_string: str):
    # "2021-08-28 00:15:00"
    dt = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
    epoch = dt.timestamp()
    return int(epoch)

def min_max(time_list: list): 
    """
    Return min and max times
    """

    if len(time_list) == 0:
        return {
            'min': '00:00.000',
            'max': '00:00.000'
        }

    times = []
    for time in time_list:
        times.append(
            {
                'time': time,
                'epoch': float(datetime.strptime(f'2000 {time}', '%Y %M:%S.%f').timestamp())
            }
        )

    times = sort_array_of_dicts(times, 'epoch')
    return {
        'min': times[-1]['time'],
        'max': times[0]['time']
    }

def json_from_file(file_name):
    with open(file_name) as json_file:
        json_data = json.load(json_file)
    return json_data
    
    
    
def json_to_file(file_name, json_data):
    with open(file_name, 'w') as out_file:
        json.dump(json_data, out_file)



def load_cache(session_id):
    file_name = f'{SESSION_CACHE_DIR}{session_id}.json'
    if not path.exists(file_name):
        return None

    return json_from_file(file_name)


def save_cache(session_id, data):
    file_name = f'{SESSION_CACHE_DIR}{session_id}.json'

    # trim the data
    remove_keys = [
        'broadcaster',
        'entrylist',
        'participants',
        'splits',
        'race_results',
        'quali_results',
        'quali_results_splits'
    ]

    for key in remove_keys:
        data.pop(key, None)

    json_to_file(file_name, data)


def sort_array_of_dicts(array: list, field: str, reverse: bool = True):
    """
    Take an array of dicts and sort the array based on a key:value present in the dicts
    """

    return sorted(array, key=lambda d: d[field], reverse=reverse)