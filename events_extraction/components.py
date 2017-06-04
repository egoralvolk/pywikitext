import datetime

months = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь', 'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь',
          'декабрь']


class Date:
    def __init__(self):
        self.day_of_week = ""
        self.designation = ""
        self.time_of_day = ""
        self.day = ""
        self.month = ""
        self.year = ""
        self.century = ""
        self.millenium = ""
        self.is_bc = ""
        self.in_text = ""

    def copy(self):
        d = Date()
        d.day = self.day
        d.day_of_week = self.day_of_week
        d.designation = self.designation
        d.month = self.month
        d.year = self.year
        d.century = self.century
        d.millenium = self.millenium
        d.in_text = self.in_text
        return d

    def date_is_bc(self):
        if len(self.is_bc):
            return True
        return False

    def to_datetime(self):
        # print(self.year)
        return datetime.datetime(int(self.year), months.index(self.month.lower()) + 1, int(self.day))

    def __str__(self):
        return "{0} {1} {2} {3} {4} {5} {6} {7}\n {8}".format(self.day_of_week, self.designation, self.time_of_day,
                                                              self.day,
                                                              self.month, self.year, self.century, self.millenium,
                                                              self.in_text)


class Toponym:
    def __init__(self):
        self.name = ""
        self.latitude = None
        self.longitude = None
        self.link_to_article = None

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return other.name == self.name


class Person:
    def __init__(self):
        self.name = ""
        self.surname = ""
        self.patron = ""
        self.link_to_article = None

    def __str__(self):
        return self.name + ' ' + self.surname + ' ' + self.patron


class Event:
    def __init__(self, date_interval, sentence):
        self.date_interval = date_interval
        self.sentence = sentence
        self.toponyms = []
        self.persons = []

    def __str__(self):
        out = '----------\nEvent\nStart Date: ' + str(self.date_interval[0]) + '\nEnd Date: ' + str(
            self.date_interval[1]) + '\nToponyms:'
        for t in self.toponyms:
            out += '\n' + str(t)
        out += '\nPersons:'
        for p in self.persons:
            out += '\n' + str(p)
        return out + "\nSentence: " + self.sentence

    def get_start_date(self):
        return self.date_interval[0].to_datetime()

    def get_end_date(self):
        return self.date_interval[1].to_datetime()

    def date_is_bc(self):
        if self.date_interval[0].date_is_bc() or self.date_interval[1].date_is_bc():
            return True
        return False