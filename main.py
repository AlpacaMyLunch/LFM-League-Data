import json
import pickle
from tempfile import TemporaryDirectory
import colorama



from itertools import tee
from os import path, listdir
from cmd import Cmd
from termcolor import colored


from classes.driver import Driver
from classes.printing import COLOR_GREEN, print_side_by_side
from classes.race import compare_times, http_request

PICKLE_DIR = './pickles/'



# PRETTY
COLOR_ERROR = 'red'
COLOR_SUCCESS = 'green'
COLOR_PROMPT = 'cyan'
COLOR_YELLOW = 'yellow'
COLOR_ORANGE = 'redorange'
COLOR_PURPLE = 'magenta'

colorama.init()
# / PRETTY

user_ratings_cache = None
user_safety_cache = None

DEFAULT_PROMPT = colored(' [*] LFM >> ', COLOR_PROMPT, attrs=['bold'])

# UTILITY FUNCTIONS

def json_from_file(file_name):
    with open(file_name) as json_file:
        json_data = json.load(json_file)
    return json_data
    
    
    
def json_to_file(file_name, json_data):
    with open(file_name, 'w') as out_file:
        json.dump(json_data, out_file)


def pickle_save(file_name, data):
    pickle.dump(data, open(f'{PICKLE_DIR}{file_name}', 'wb'))

def pickle_load(file_name):
    output = None
    if path.exists(f'{PICKLE_DIR}{file_name}'):
        output = pickle.load(open(f'{PICKLE_DIR}{file_name}', 'rb'))

    return output


def pairwise(iterable):
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def list_saved_drivers():
    """
    Returns an array of pickle files
    """

    return listdir(PICKLE_DIR)


def sort_array_of_dicts(array: list, field: str, reverse: bool = True):
    """
    Take an array of dicts and sort the array based on a key:value present in the dicts
    """

    return sorted(array, key=lambda d: d[field], reverse=reverse)


def grab_all_user_ratings():
    global user_ratings_cache
    if user_ratings_cache:
        return user_ratings_cache

    url = 'https://api2.lowfuelmotorsport.com/api/statistics/rating?country='
    response = http_request(url)
    data = response.json()
    data.reverse()
    user_ratings_cache = data
    return data

def grab_all_user_safety():
    global user_safety_cache
    if user_safety_cache:
        return user_safety_cache

    url = 'https://api2.lowfuelmotorsport.com/api/statistics/safetyrating'
    response = http_request(url)
    data = response.json()
    data.reverse()
    user_safety_cache = data
    return data


# / END UTILITY FUNCTIONS



def main():


    drivers = []


    for file_name in list_saved_drivers():
        driver_id = file_name.replace('.pkl', '')
        drivers.append(
            Driver(driver_id)
            )



    class Terminal(Cmd):
        global DEFAULT_PROMPT
        prompt = DEFAULT_PROMPT
        selected_driver = None

        def default(self, args):
            print(args)

        def do_exit(self, args):
            exit()

        def do_list(self, args):
            """
            List drivers
            """
            driver_outputs = []
            for driver in drivers:
                # driver.print()
                driver_outputs.append(driver.text(colorful=True))

            print_side_by_side(driver_outputs, 4, 75)

        def do_delete(self, args):
            """
            Delete a driver
            """

            if not self.selected_driver:
                print('A driver must be selected')
                return

            
            check = input('Are you sure?  Type "YES" to confirm. ')
            if check != 'YES':
                print(colored('    No confirmation.  Not deleting the driver', 'red'))
                print('')
                return

            
            self.selected_driver.delete()
            drivers.remove(self.selected_driver)
            self.selected_driver = None
            self.prompt = DEFAULT_PROMPT
            print(colored('   Driver was deleted.', 'green'))
            print('')


        def do_find(self, identifier):
            """
            Find drivers based on name, ID or notes.
            """
            output = []
            for driver in drivers:
                if identifier.isnumeric():
                    if driver.id == int(identifier):
                        output.append(driver.text(colorful=True))
                else:
                    if identifier.lower() in driver.name.lower() or identifier.lower() in driver.notes.lower():
                        output.append(driver.text(colorful=True))

            print_side_by_side(output, 3, 95)


        def do_select(self, identifier):
            for driver in drivers:
                if identifier.isnumeric():
                    if driver.id == int(identifier):
                        self.selected_driver = driver
                        break
                else:
                    if identifier.lower() in driver.name.lower():
                        self.selected_driver = driver
                        break

            self.prompt = colored(f' [*] {self.selected_driver.name} >> ', COLOR_PROMPT, attrs=['bold'])
            self.selected_driver.print()
                    
        def do_add(self, id):
            """
            Add a new driver by ID
            """

            for driver in drivers:
                if id == str(driver.id):
                    driver.print()
                    return

            driver = Driver(id)
            driver.gather_sessions()
            drivers.append(driver)

        def do_update(self, all):
            if all:
                for driver in drivers:
                    driver.gather_sessions()

            else:
                if self.selected_driver:
                    self.selected_driver.gather_sessions()
                else:
                    print('Select a driver with the "select" command, or pass the argument "all"')
        
        def do_print(self, args):
            if self.selected_driver:
                self.selected_driver.print()

        def do_json(self, all):
            if all:
                for driver in drivers:
                    driver.json()

            else:
                if self.selected_driver:
                    self.selected_driver.json()
                else:
                    print('Select a driver with the "select" command, or pass the argument "all"')

        def do_note(self, note):
            if self.selected_driver:
                self.selected_driver.update_notes(note)
            else:
                print('No driver selected')

        def do_shared(self, args):
            """
            Does this driver share any sessions with other tracked drivers?
            Optional: Filter by opponent name and/or track name
            """

            if not self.selected_driver:
                print('Please select a driver')
                return

            search_terms = args.strip()
            search_terms = search_terms.split(' ')
            shared = {}
            for session in self.selected_driver.sessions:
                session_id = session.session_id
                split = session.split
                if not session.dns and not session.dnf:
                    for driver in drivers:
                        if driver != self.selected_driver:
                            for check_session in driver.sessions:
                                include = True
                                if check_session.session_id == session_id:
                                    
                                    data = {
                                        'session': session_id,
                                        'track': session.track,
                                        'date': session.date,
                                        'my position': session.finish_position,
                                        'their position': check_session.finish_position,
                                    }


                                    if check_session.split == split and not check_session.dns and not check_session.dnf:
                                        for term in search_terms:
                                            if (term.lower() not in data['track'].lower()) and (term.lower() not in driver.name.lower()):
                                                include = False

                                        if include == True:
                                            if driver.name not in shared:
                                                shared[driver.name] = []
                                            shared[driver.name].append(data)

            output = []
            for driver in shared:
                msg = f'{colored(driver, COLOR_SUCCESS)}\n'
                for session in shared[driver]:
                    if session['my position'] < session['their position']:
                        session['my position'] = colored(f"P{session['my position']}", COLOR_GREEN)
                        session['their position'] = f'P{session["their position"]}'
                    else:
                        session['their position'] = colored(f"P{session['their position']}", COLOR_GREEN)
                        session['my position'] = f'P{session["my position"]}'
                    msg = f'{msg}  {session["date"][0:10]} at {session["track"]} ({session["session"]}) {self.selected_driver.name} {session["my position"]} - {session["their position"]} {driver}\n'
                msg = f'{msg} \n'
                output.append(msg)

            print_side_by_side(output, 2, 140, dynamic_height=True, organize_lengths=True)

        def do_chats(self, args):
            """
            Find chat messages based on user, message or session id
            """

            output = []
            ids = []

            args = args.strip()
            search_terms = args.split(' ')

            for driver in drivers:
                for session in driver.sessions:
                    for chats in session.chat:
                        for chat in chats:
                            chat_id = chat['id']
                            user_name = chat['name']
                            message = chat['message']
                            include = True
                            for term in search_terms:
                                if term.lower() not in user_name.lower():
                                    if term.lower() not in message.lower():
                                        if term not in str(session.session_id):
                                            include = False
                            if include == True:
                                if chat_id not in ids:
                                    ids.append(chat_id)
                                    output.append(
                                        f'Session {session.session_id}\n{colored(user_name, "blue")}: {message}\n'
                                    )

            print_side_by_side(output, 5, 60)


        def do_cars(self, args):
            """
            Print summary of the selected user's car choices
            """

            cars = {}
            if self.selected_driver:
                for session in self.selected_driver.sessions:
                    car = f"{session.car_year} {session.car_name}"
                    if car not in cars:
                        cars[car] = 0
                    cars[car] += 1

            cars = {k: v for k, v in sorted(cars.items(), key=lambda item: item[1], reverse=True)}
            for car in cars:
                print(car, cars[car])

        def do_tracks(self, args):
            """
            Print summary of the selected user's tracks
            """


            if not self.selected_driver:
                print('Please select a driver')
                return
            
            output = []


            for track_name in self.selected_driver.tracks:
                temp_output = f"{colored(track_name, 'green')}\n"
                track_data = self.selected_driver.tracks[track_name]
                
                best_lap = '10:59.999'
                best_average = '10:59.999'
                for car in track_data:
                    compared = compare_times(best_lap, track_data[car]['best'])
                    if compared < 0:
                        best_lap = track_data[car]['best']

                    compared = compare_times(best_average, track_data[car]['average'])
                    if compared < 0:
                        best_average = track_data[car]['average']

                for car in track_data:
                    car_best = track_data[car]['best']
                    car_average = track_data[car]['average']
                    car_races = track_data[car]['races']
                    temp_output = f"{temp_output}   {colored(car, 'blue')}\n"

                    if car_best == best_lap:
                        car_best = colored(car_best, 'magenta')
                    if car_average == best_average:
                        car_average = colored(car_average, 'magenta')

                    temp_output = f"{temp_output}   Races: {car_races}, Best: {car_best}, Average: {car_average}\n\n"

                output.append(temp_output)

            print_side_by_side(output, 4, 70, dynamic_height=True, organize_lengths=True)



        def do_race(self, args):

            if not self.selected_driver:
                print('Please select a driver')
                return

            args = args.strip()
            if args == '':
                print(colored('Recent races', COLOR_PROMPT))
                for race in self.selected_driver.sessions[:10]:
                    outcome = ''
                    if race.dns:
                        outcome = colored('DNS', 'red')
                    elif race.dnf:
                        outcome = colored('DNF', 'red')
                    else:
                        outcome = f'finished {race.finish_position}'
                    
                    
                    print(f" > {race.track} (session {race.session_id}) on {race.date} - {outcome}")

            else:

                args = args.split(' ')
                session_id = int(args[0])

                if len(args) == 1:
                    race = self.selected_driver.return_session(session_id)
                    if race:
                        race.print()
                else:
                    second_arg = args[1]

                    if second_arg == 'opponents':
                        race = self.selected_driver.return_session(session_id)
                        if race:
                            race.show_opponents()

                    if second_arg == 'compare':
                        opponent_id = int(args[2])
                        race = self.selected_driver.return_session(session_id)
                        if race:
                            race.compare(opponent_id)

        def do_common(self, args):
            if not self.selected_driver:
                print('Please select a driver')
                return

            number_of_opponents = 6 # default
            name_filters = []
            name_filter = ''
            args = args.split(' ')
            for arg in args:
                if arg.isnumeric():
                    number_of_opponents = int(arg)
                else:
                    arg = arg.strip()
                    name_filters.append(arg)
                    name_filter = ' '.join(name_filters)
            



            self.selected_driver.common(number_of_opponents, name_filter)

        def do_races(self, args):
            if not self.selected_driver:
                print('Please select a driver')
                return

            args = args.strip()

            races = self.selected_driver.return_sessions_by_term(args)
            printing = []

            bests = {
                'lap': '10:59.999',
                'average lap': '10:59.999',
                'finish position': 99
            }
            for race in races:
                best_lap_comparison = compare_times(bests['lap'], race.best_lap)
                if best_lap_comparison < 0:
                    bests['lap'] = race.best_lap


                avg_lap_comparison = compare_times(bests['average lap'], race.analysis["average"].time)
                if avg_lap_comparison < 0:
                    bests['average lap'] = race.analysis["average"].time

                if race.finish_position < bests['finish position']:
                    bests['finish position'] = race.finish_position


            for race in races:

                p_string = f'P{race.finish_position}'
                lap_string = f'{race.best_lap}'
                avg_lap_string = f'{race.analysis["average"].time}'

                if race.finish_position == bests['finish position']:
                    p_string = f'{colored(p_string, COLOR_PURPLE)}'
                if race.best_lap == bests['lap']:
                    lap_string = f'{colored(lap_string, COLOR_PURPLE)}'
                if race.analysis["average"].time == bests['average lap']:
                    avg_lap_string = f'{colored(avg_lap_string, COLOR_PURPLE)}'



                printing.append(
                    f'{p_string} in session {race.session_id} on {race.date}\n{race.track} - {race.car_year} {race.car_name}\nBest Lap: {lap_string}  |  Average Lap: {avg_lap_string}\n'
                )




            print_side_by_side(printing, 3, 90)



        def do_force_update(self, all):
            if all == 'all':
                for driver in drivers:
                    driver.force_update()

            else:
                if self.selected_driver:
                    self.selected_driver.force_update()
                else:
                   print('Select a driver with the "select" command, or pass the argument "all"') 


        def do_sandbag(self, args):
            
            data = grab_all_user_ratings()
            how_many = 10 # default

            name_filters = []
            name_filter = ''
            args = args.split(' ')
            for arg in args:
                if arg.isnumeric():
                    how_many = int(arg)
                else:
                    arg = arg.strip()
                    name_filters.append(arg)
                    name_filter = ' '.join(name_filters).lower()


            output = []
            for driver in data:
                id = driver['id']
                name = f"{driver['vorname']} {driver['nachname']}"
                elo = driver['rating']

                if name_filter in name.lower():
                    output.append(
                        f'{elo} - {name} ({id})'
                    )
                    if len(output) == how_many:
                        break

            print_side_by_side(output, 4, 50)


        def do_unsafe(self, args):
            data = grab_all_user_safety()
            how_many = 10 # default

            name_filters = []
            name_filter = ''
            args = args.split(' ')
            for arg in args:
                if arg.isnumeric():
                    how_many = int(arg)
                else:
                    arg = arg.strip()
                    name_filters.append(arg)
                    name_filter = ' '.join(name_filters).lower()


            output = []
            for driver in data:
                id = driver['id']
                name = f"{driver['vorname']} {driver['nachname']}"
                sa = driver['safety_rating']

                if name_filter in name.lower():
                    output.append(
                        f'{sa} - {name} ({id})'
                    )
                    if len(output) == how_many:
                        break

            print_side_by_side(output, 4, 50)
    terminal = Terminal(Cmd)

    terminal.cmdloop()


 

if __name__ == '__main__':
    main()