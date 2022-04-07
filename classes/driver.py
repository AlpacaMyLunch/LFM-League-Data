import json
import requests
import pickle
import textwrap
from datetime import datetime

from os import path

from classes.race import Race

PICKLE_DIR = './pickles/'
JSON_DIR = './json/'
BASE_URL = 'https://api2.lowfuelmotorsport.com/api/'
#  https://api2.lowfuelmotorsport.com/api/users/getUsersPastRaces/8507?start=0&limit=1

class Driver:
    id: int
    name: str
    sessions: list
    save_file: str
    json_file: str
    notes: str
    wins: int
    races: int
    podiums: int

    def __init__(self, id: int):
        

        self.name = ''
        self.id = int(id)
        self.sessions = []
        self.notes = ''
        self.wins = 0
        self.podiums = 0


        
        self.save_file = f'{PICKLE_DIR}{self.id}.pkl'
        exists = pickle_load(self.save_file)

        
        

        if exists:
            self.name = exists.name
            self.id = exists.id
            self.sessions = exists.sessions
            self.json_file = f'{JSON_DIR}{self.name}.json'
            try:
                self.notes = exists.notes
            except:
                self.notes = ''

        else:
            pickle_save(self.save_file, self)


        self.races = len(self.sessions)

    def update_notes(self, notes: str):
        self.notes = notes
        pickle_save(self.save_file, self)


    def force_update(self):
        """
        Force a refresh of all sessions
        """
        self.sessions = []
        self.wins = 0
        self.podiums = 0
        self.gather_sessions()

    def print(self):
        print()
        print(f'{self.name} (id: {self.id})')
        
        print(f'{self.races} sessions')
        print(f'{self.wins} wins, {self.podiums} podiums')

        print(f'Notes: {self.notes}')

        print()

    def text(self):
        """
        Same as print, but returns a string instead of output to console
        """
        output = f'{self.name} (id: {self.id})\n'
        output = f'{output}{self.races} sessions\n'
        output = f'{output}{self.wins} wins, {self.podiums} podiums\n'
        output = f'{output}Notes: {textwrap.fill(self.notes, 50)}\n'

        return output
    def gather_sessions(self):
        """
        Pupulate an array of dictionaries containing
        basic info about the session
        """

        if self.name != '':
            print(f'Updating sessions for {self.name}...')
        url = f'{BASE_URL}users/getUsersPastRaces/{self.id}?start=0&limit=99999'

        request = http_request(url)
        data = request.json()

        
      
        for race in data:
            if self.name == '':
                driver_data = json.loads(race['driver_data'])
                self.name = f"{driver_data['vorname']} {driver_data['nachname']}"
                print(f'Updating sessions for {self.name}...')
                self.json_file = f'{JSON_DIR}{self.name}.json'

            if not self.session_exists(race['race_id']):
                start = race['start_pos']
                finish = race['finishing_pos']

                new_race = Race(race['race_id'], self.id)

                new_race.set_start_position(start)
                new_race.set_finish_position(finish)
                self.sessions.append(new_race)

                if finish == 1:
                    self.wins += 1
                if finish <=3:
                    self.podiums += 1


        self.sessions = sort_races(self.sessions)
        self.races = len(self.sessions)
        pickle_save(self.save_file, self)





    def json(self):
        """
        Outputs data to a json file
        """
        
        output = {
                'id': self.id,
                'name': self.name,
                'sessions': [],
                'notes': self.notes
            }
        
        for session in self.sessions:
            session_data = session.json()
            output['sessions'].append(session_data)

        json_to_file(self.json_file, output)

    def session_exists(self, session_id: int):
        """
        Check to see if a session id has alredy been added
        """

        for session in self.sessions:
            if session.session_id == session_id:
                return True

        return False


    def return_session(self, session_id: int):
        """
        If found, returns a Race based on session id
        """

        for session in self.sessions:
            if session.session_id == session_id:
                return session

        return None





# UTILITY FUNCTIONS

def json_from_file(file_name):
    with open(file_name) as json_file:
        json_data = json.load(json_file)
    return json_data
    

    
def json_to_file(file_name, json_data):
    with open(file_name, 'w') as out_file:
        json.dump(json_data, out_file)

def pickle_save(file_name, data):
    pickle.dump(data, open(file_name, 'wb'))

def pickle_load(file_name):
    output = None
    if path.exists(file_name):
        output = pickle.load(open(file_name, 'rb'))

    return output


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

def http_request(url: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"
        }
    return requests.get(url, headers=headers)


def sort_races(races):

    temp = []
    for race in races:
        temp.append(
            {
                'session id': race.session_id,
                'epoch': race.epoch
            }
        )

    temp = sort_array_of_dicts(temp, 'epoch')

    sorted_races = []

    for item in temp:
        sesh = item['session id']
        for race in races:
            if race.session_id == sesh:
                sorted_races.append(race)
                break
    
    return sorted_races






def sort_array_of_dicts(array: list, field: str, reverse: bool = True):
    """
    Take an array of dicts and sort the array based on a key:value present in the dicts
    """

    return sorted(array, key=lambda d: d[field], reverse=reverse)
# / END UTILITY FUNCTIONS