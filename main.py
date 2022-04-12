import json
import pickle
import colorama



from itertools import tee
from os import path, listdir
from cmd import Cmd
from termcolor import colored


from classes.driver import Driver
from classes.printing import COLOR_GREEN, print_side_by_side
from classes.race import compare_times

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


# / END UTILITY FUNCTIONS



def main():


    drivers = []


    for file_name in list_saved_drivers():
        driver_id = file_name.replace('.pkl', '')
        drivers.append(
            Driver(driver_id)
            )



    class Terminal(Cmd):
        prompt = colored(' [*] LFM >> ', COLOR_PROMPT, attrs=['bold'])
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
                driver_outputs.append(driver.text())

            print_side_by_side(driver_outputs, 3, 95)

        def do_find(self, identifier):
            """
            Find drivers based on name or ID
            """
            output = []
            for driver in drivers:
                if identifier.isnumeric():
                    if driver.id == int(identifier):
                        output.append(driver.text())
                else:
                    if identifier.lower() in driver.name.lower():
                        output.append(driver.text())

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
                                    'their position': check_session.finish_position
                                }

                                if check_session.split == split:
                                    for term in search_terms:
                                        if (term.lower() not in data['track'].lower()) and (term.lower() not in driver.name.lower()):
                                            include = False

                                    if include == True:
                                        if driver.name not in shared:
                                            shared[driver.name] = []
                                        shared[driver.name].append(data)


            temp = {}
            # shared in a dict containing arrays.  want to sort by aray len
            sorted_drivers = sorted( shared, key = lambda x: (len( shared[ x ] ), x), reverse = True )
            for driver in sorted_drivers:
                temp[driver] = shared[driver]

            shared = temp


            output = []
            for driver in shared:
                msg = f'{colored(driver, COLOR_SUCCESS)}\n'
                for session in shared[driver]:
                    if session['my position'] < session['their position']:
                        session['my position'] = colored(f"P{session['my position']}", COLOR_GREEN)
                        session['their position'] = f'P{session["their position"]}'
                    else:
                        session['their position'] = colored(f"P{session['my position']}", COLOR_GREEN)
                        session['my position'] = f'P{session["my position"]}'
                    msg = f'{msg}  {session["date"][0:10]} at {session["track"]} ({session["session"]}) {self.selected_driver.name} {session["my position"]} - {session["their position"]} {driver}\n'
                msg = f'{msg} \n'
                output.append(msg)

            print_side_by_side(output, 2, 140, dynamic_height=True)


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

            tracks = {}
            if self.selected_driver:
                for session in self.selected_driver.sessions:
                    track = session.track
                    if track not in tracks:
                        tracks[track] = 0
                    tracks[track] += 1

            tracks = {k: v for k, v in sorted(tracks.items(), key=lambda item: item[1], reverse=True)}
            for track in tracks:
                print(track, tracks[track])

        def do_race(self, args):

            if not self.selected_driver:
                print('Please select a driver')
                return

            args = args.strip()
            if args == '':
                print(colored('Recent races', COLOR_PROMPT))
                for race in self.selected_driver.sessions[:10]:
                    print(f" > {race.track} (session {race.session_id}) on {race.date} - finished {race.finish_position}")

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
            if args:
                try:
                    number_of_opponents = int(args)
                except:
                    pass
            self.selected_driver.common(number_of_opponents)

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



    terminal = Terminal(Cmd)

    terminal.cmdloop()


 

if __name__ == '__main__':
    main()