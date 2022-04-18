import json
import requests
import time
import pickle
import textwrap
from datetime import datetime

from os import path, remove

from classes.race import Race, compare_times, average_time
from classes.printing import print_side_by_side, replace_print, colored

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
    dnf: int
    dns: int
    races: int
    podiums: int
    incident_points: int
    url: str
    incident_points_per_race: float
    tracks: dict
    elo: int
    safety_rating: float

    def __init__(self, id: int):
        

        self.name = ''
        self.id = int(id)
        self.url = f'https://lowfuelmotorsport.com/profile/{self.id}'
        self.sessions = []
        self.notes = ''
        self.wins = 0
        self.podiums = 0
        self.incident_points = 0
        self.incident_points_per_race = 0.0
        self.dnf = 0
        self.dns = 0
        self.elo = 0
        self.safety_rating = 0.0
        self.tracks = {}

        
        self.save_file = f'{PICKLE_DIR}{self.id}.pkl'
        exists = pickle_load(self.save_file)

        
        

        if exists:
            self.name = exists.name
            self.id = exists.id
            self.sessions = exists.sessions
            self.json_file = f'{JSON_DIR}{self.name}.json'
            self.wins = exists.wins
            self.podiums = exists.podiums
            self.notes = exists.notes
            self.incident_points = exists.incident_points
            self.incident_points_per_race = exists.incident_points_per_race
            self.url = f'https://lowfuelmotorsport.com/profile/{self.id}'
            self.dns = exists.dns
            self.dnf = exists.dnf
            self.tracks = exists.tracks

            try:
                self.elo = exists.elo
                self.safety_rating = exists.safety_rating
            except:
                self.elo = 0
                self.safety_rating = 0.0

        else:
            pickle_save(self.save_file, self)


        self.races = len(self.sessions)

    def update_notes(self, notes: str):
        self.notes = notes
        pickle_save(self.save_file, self)

    def delete(self):
        """
        Deletes the pickle file.  Driver will not be loaded next time.
        """

        remove(self.save_file)


    def force_update(self):
        """
        Force a refresh of all sessions
        """
        self.sessions = []
        self.wins = 0
        self.dns = 0
        self.dnf = 0
        self.podiums = 0
        self.incident_points = 0
        self.incident_points_per_race = 0.0
        self.tracks = {}
        self.gather_sessions()

    def print(self):
        print()
        print(f'{self.name} ({self.elo} elo, {self.safety_rating} sr)')
        print(self.url)
        print(f'{self.races} sessions {self.dns} ({percentage(self.dns, self.races)}) DNS, {self.dnf} ({percentage(self.dnf, self.races)}) DNF')
        print(f'{self.wins} wins, {self.podiums} podiums')
        print(f'{self.incident_points_per_race} incidents per race')
        print(f'Notes: {self.notes}')

        print()

    def text(self, colorful=False):
        """
        Same as print, but returns a string instead of output to console
        """
        if colorful:
            output = f'{colored(self.name, "blue")} ({self.elo} elo, {self.safety_rating} sr)\n'
        else:
            output = f'{self.name} ({self.id})\n'

        output = f'{output}{self.url}\n' 
        output = f'{output}{self.races} sessions {self.dns} ({percentage(self.dns, self.races)}) DNS, {self.dnf} ({percentage(self.dnf, self.races)}) DNF\n'
        output = f'{output}{self.wins} wins, {self.podiums} podiums\n'
        output = f'{output}{self.incident_points_per_race} incidents per race\n'
        output = f'{output}Notes: {textwrap.fill(self.notes, 50)}\n'

        return output
    def gather_sessions(self):
        """
        Pupulate an array of dictionaries containing
        basic info about the session
        """

        at_a_time = 250

        if self.name != '':
            print(f'Updating sessions for {self.name}...')

        start = 0
        data = []
        while True:
            url = f'{BASE_URL}users/getUsersPastRaces/{self.id}?start={start}&limit={at_a_time}'

            request = http_request(url)
            new_results = request.json()
            if len(new_results) == 0:
                break

            data += new_results

            if len(new_results) < at_a_time:
                break


            start += at_a_time - 1
            time.sleep(.5)
            

        added_session_counter = 0
      
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
                added_session_counter += 1



                self.incident_points += new_race.incidents
                

                if finish == 1:
                    self.wins += 1
                if finish <=3:
                    self.podiums += 1

                if new_race.dns:
                    self.dns += 1
                if new_race.dnf:
                    self.dnf += 1

                if not new_race.dns:
                    if len(new_race.laps) > 0:
                        track = new_race.track
                        if track not in self.tracks:
                            self.tracks[track] = {}
                        
                        car = f'{new_race.car_year} {new_race.car_name}'
                        if car not in self.tracks[track]:
                            self.tracks[track][car] = {
                                'races': 0,
                                'best': '10:59.999',
                                'average_laps': [],
                                'average': None
                            }

                        self.tracks[track][car]['races'] += 1
                        compared = compare_times(self.tracks[track][car]['best'], new_race.best_lap)
                        if compared < 0:
                            self.tracks[track][car]['best'] = new_race.best_lap
                        
                        if new_race.analysis['average'].time != '00:00.000':
                            self.tracks[track][car]['average_laps'].append(new_race.analysis['average'].time)
                            self.tracks[track][car]['average'] = average_time(self.tracks[track][car]['average_laps'])


        self.sessions = sort_races(self.sessions)
        self.races = len(self.sessions)


        # Grab ELO and safety from most recent session (first in list)
        most_recent = self.sessions[0]
        self.elo = most_recent.driver_elo
        self.safety_rating = most_recent.driver_safety_rating


        self.incident_points_per_race = round(self.incident_points / self.races, 2)
        pickle_save(self.save_file, self)
        replace_print('')
        print('', end='')
        
        if added_session_counter > 0:
            s = ''
            if added_session_counter > 1:
                s = 's'
            print(
                f'  added {colored(added_session_counter, "blue")} session{s} for {self.name}{" " * 30}'
            )


    def common(self, number_of_opponents: int = 6, name_filter: str = ''):
        """
        Return a list of the most common opponents.
        """

        counter = {}
        holder = []
        for session in self.sessions:
            opponents = session.opponents
            for opponent in opponents:
                if opponent['id'] != self.id:
                    if (name_filter == '') or (name_filter.lower() in opponent['name'].lower()):
                        opponent = {
                            'id': opponent['id'],
                            'name': opponent['name']
                        }
                        if opponent['id'] not in counter:
                            counter[opponent['id']] = 0
                            holder.append(opponent)
                        counter[opponent['id']] += 1




        counter = dict(sorted(counter.items(), key=lambda item: item[1], reverse=True))

        output = []
        for id in list(counter.keys())[0:number_of_opponents]:
            for opponent in holder:
                if opponent['id'] == id:
                    opponent['races'] = counter[id]
                    # output.append(f'{counter[id]} races with {opponent["name"]} ({opponent["id"]})')
                    output.append({
                        'name': opponent['name'],
                        'id': opponent['id'],
                        'races': counter[id]
                    })
                    break

        return output



    def json(self):
        """
        Outputs data to a json file
        """
        
        output = {
                'id': self.id,
                'elo': self.elo,
                'safety_rating': self.safety_rating,
                'name': self.name,
                'sessions': [],
                'notes': self.notes,
                'incidents per race': self.incident_points_per_race,
                'tracks': self.tracks
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

    def return_sessions_by_term(self, term: str):
        """
        Return a list of sessions based on a term
        such as track or car name.
        """

        terms = term.split(' ')
        output = []
        for session in self.sessions:
            include = True
            if session.dnf == False and session.dns == False and len(session.laps) > 0:
                for term in terms:
                    if (term.lower() not in session.track.lower()) and (term.lower() not in session.car_name.lower()):
                        include = False
            else:
                include = False

            if include == True:
                output.append(session)



        
        return output



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



def percentage(part, whole):
    return f'{str(round(100 * float(part)/float(whole), 1))}%'


def sort_array_of_dicts(array: list, field: str, reverse: bool = True):
    """
    Take an array of dicts and sort the array based on a key:value present in the dicts
    """

    return sorted(array, key=lambda d: d[field], reverse=reverse)
# / END UTILITY FUNCTIONS
