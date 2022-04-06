
class Sector:
    time: str
    number: int

    def __init__(self, time: str, number: int):
        self.time = time
        self.number = number

    def print(self):
        print(
            self.text()
        )

    def text(self):
        """
        Same as print, but returns a string instead of print to console
        """
        return f'Sector {self.number}: {self.time}'

    def json(self):
        return {
            'time': self.time,
            'number': self.number
        }