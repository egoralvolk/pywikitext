import subprocess
import os
import codecs
from .parser_dates import *
from .parser_toponyms import ParserToponym
from .parser_persons import ParserPerson


class EventsExtractor:
    def __init__(self, session_name='default', path_to_tomita='./tomita/'):
        self.__path_to_tomita = os.path.abspath(path_to_tomita)
        self.__date_config = 'encoding "utf8";' \
                             'TTextMinerConfig {' \
                             '    Dictionary = "dic.gzt";' \
                             '    Input = {File =  "date.txt" }' \
                             '    Output = {File = "date.xml" }' \
                             '    Articles = [' \
                             '        {Name = "дата"}' \
                             '    ]' \
                             '    Facts = [' \
                             '        {Name = "Date"}' \
                             '    ]' \
                             '}'
        self.__toponym_config = 'encoding "utf8";' \
                                'TTextMinerConfig {' \
                                '    Dictionary = "dic.gzt";' \
                                '    Input = {File =  "toponym.txt" }' \
                                '    Output = {File = "toponym.xml" }' \
                                '    Articles = [' \
                                '        {Name = "топоним"}' \
                                '    ]' \
                                '    Facts = [' \
                                '        {Name = "Toponym"}' \
                                '    ]' \
                                '}'
        self.__fio_config = 'encoding "utf8";' \
                            'TTextMinerConfig {' \
                            '    Dictionary = "dic.gzt";' \
                            '    Input = {File =  "fio.txt" }' \
                            '    Output = {File = "fio.xml" }' \
                            '    Articles = [' \
                            '        {Name = "person"}' \
                            '    ]' \
                            '    Facts = [' \
                            '        {Name = "Person"}' \
                            '    ]' \
                            '}'
        self.__events = []

    def extract_date_and_sentence(self, text):
        f = codecs.open(self.__path_to_tomita + '\\date.txt', 'w', 'utf-8')
        f.write(text)
        f.close()

        f = codecs.open(self.__path_to_tomita + '\\date.proto', 'w', 'utf-8')
        f.write(self.__date_config)
        f.close()

        p = subprocess.Popen([self.__path_to_tomita + '\\' + 'tomitaparser.exe',
                          'date.proto'], cwd=self.__path_to_tomita, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
        out, err = p.communicate()

        parser = ParserWikiDate(self.__path_to_tomita + '\\date.xml', self.__path_to_tomita + '\\date.txt')

        return parser.get_events()

    def extract_toponym(self, text):
        f = codecs.open(self.__path_to_tomita + '\\toponym.txt', 'w', 'utf-8')
        f.write(text)
        f.close()

        f = codecs.open(self.__path_to_tomita + '\\toponym.proto', 'w', 'utf-8')
        f.write(self.__toponym_config)
        f.close()

        p = subprocess.Popen([self.__path_to_tomita + '\\' + 'tomitaparser.exe',
                              'toponym.proto'], cwd=self.__path_to_tomita, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate()

        parser = ParserToponym(self.__path_to_tomita + '\\toponym.xml')
        toponyms = parser.get_toponyms()
        tops = []
        for t in toponyms:
            if t not in tops:
                tops.append(t)
        return tops

    def extract_person(self, text):
        f = codecs.open(self.__path_to_tomita + '\\fio.txt', 'w', 'utf-8')
        f.write(text)
        f.close()

        f = codecs.open(self.__path_to_tomita + '\\fio.proto', 'w', 'utf-8')
        f.write(self.__fio_config)
        f.close()

        p = subprocess.Popen([self.__path_to_tomita + '\\' + 'tomitaparser.exe',
                              'fio.proto'], cwd=self.__path_to_tomita, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate()

        parser = ParserPerson(self.__path_to_tomita + '\\fio.xml')
        return parser.get_persons()

    def extract_events_from_article(self, text, clear=True):
        self.__events = self.extract_date_and_sentence(text)
        self.additionally_event_processing()
        for event in self.__events:
            event.toponyms = self.extract_toponym(event.sentence)
            event.persons = self.extract_person(event.sentence)

        if clear:
            os.remove(self.__path_to_tomita + '\\date.txt')
            os.remove(self.__path_to_tomita + '\\date.proto')
            os.remove(self.__path_to_tomita + '\\date.xml')
            if os.path.exists(self.__path_to_tomita + '\\toponym.proto'):
                os.remove(self.__path_to_tomita + '\\toponym.txt')
                os.remove(self.__path_to_tomita + '\\toponym.proto')
                os.remove(self.__path_to_tomita + '\\toponym.xml')
            if os.path.exists(self.__path_to_tomita + '\\fio.proto'):
                os.remove(self.__path_to_tomita + '\\fio.txt')
                os.remove(self.__path_to_tomita + '\\fio.proto')
                os.remove(self.__path_to_tomita + '\\fio.xml')

        return self.__events

    def additionally_event_processing(self):
        for event in self.__events:
            event.date_interval[0].year = event.date_interval[0].year.split(' ')[0]
            event.date_interval[1].year = event.date_interval[1].year.split(' ')[0]
            if event.date_interval[0].year.find('-ЫЙ') != -1:
                event.date_interval[0].day = '1'
                event.date_interval[0].month = 'ЯНВАРЬ'
                event.date_interval[0].year = event.date_interval[0].year[0:4]
            if event.date_interval[1].year.find('-ЫЙ') != -1:
                event.date_interval[1].day = '31'
                event.date_interval[1].month = 'ДЕКАБРЬ'
                event.date_interval[1].year = event.date_interval[1].year[0:3] + '9'

            if event.date_interval[0].day == '':
                event.date_interval[0].day = '1'
            if event.date_interval[0].month == '':
                event.date_interval[0].month = 'ЯНВАРЬ'
            if event.date_interval[1].month == '':
                event.date_interval[1].month = 'ДЕКАБРЬ'
                event.date_interval[1].day = '31'
            elif event.date_interval[1].day == '':
                if event.date_interval[1].month == 'ДЕКАБРЬ' or \
                                event.date_interval[1].month == 'ОКТЯБРЬ' or \
                                event.date_interval[1].month == 'АВГУСТ' or \
                                event.date_interval[1].month == 'ИЮЛЬ' or \
                                event.date_interval[1].month == 'МАЙ' or \
                                event.date_interval[1].month == 'МАРТ' or \
                                event.date_interval[1].month == 'ЯНВАРЬ':
                    event.date_interval[1].day = '31'
                elif event.date_interval[1].month == 'ФЕВРАЛЬ':
                    event.date_interval[1].day = '28'
                else:
                    event.date_interval[1].day = '30'


if __name__ == '__main__':
    tm = EventsExtractor()
    # events = tm.extract_date_and_sentence("28 июля 1914 — 11 ноября 1918")
    f = codecs.open('WOV', 'r', 'utf-8')
    text = f.read()
    f.close()
    events = tm.extract_events_from_article(text)
    for event in events:
        print(event)
