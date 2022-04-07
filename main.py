import json
import pickle
import colorama



from itertools import tee
from os import path, listdir
from cmd import Cmd
from termcolor import colored


from classes.driver import Driver
from classes.printing import print_side_by_side

PICKLE_DIR = './pickles/'



# PRETTY
COLOR_ERROR = 'red'
COLOR_SUCCESS = 'green'
COLOR_PROMPT = 'cyan'
COLOR_YELLOW = 'yellow'
COLOR_ORANGE = 'redorange'
PROMPT_ARROW = colored(' ->> ', COLOR_PROMPT)
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
            driver_outputs = []
            for driver in drivers:
                # driver.print()
                driver_outputs.append(driver.text())

            print_side_by_side(driver_outputs, 2, 100)

        def do_find(self, identifier):
            for driver in drivers:
                if identifier.isnumeric():
                    if driver.id == int(identifier):
                        driver.print()
                else:
                    if identifier.lower() in driver.name.lower():
                        driver.print()


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
            """

            if not self.selected_driver:
                print('Please select a driver')
                return


            shared = {}
            for session in self.selected_driver.sessions:
                session_id = session.session_id
                split = session.split
                for driver in drivers:
                    if driver != self.selected_driver:
                        for check_session in driver.sessions:
                            if check_session.session_id == session_id:
                                
                                data = {
                                    'session': session_id,
                                    'track': session.track,
                                    'date': session.date,
                                    'my position': session.finish_position,
                                    'their position': check_session.finish_position
                                }
                                if check_session.split == split:
                                    if driver.name not in shared:
                                        shared[driver.name] = []
                                    shared[driver.name].append(data)

            
            for driver in shared:
                print(colored(driver, COLOR_SUCCESS))
                for session in shared[driver]:
                    print(' {} at {} ({})  {} finished {} and {} finished {}'.format(
                        session['date'],
                        session['track'],
                        session['session'],
                        self.selected_driver.name,
                        session['my position'],
                        driver,
                        session['their position']
                    ))
                print('')


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