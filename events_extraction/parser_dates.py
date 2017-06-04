import codecs
from xml.dom import minidom

import re

from .dates_from_text import *
from .components import *


class ParserWikiDate:
    def __init__(self, path, path_to_text):
        self.path_to_text = path_to_text
        self.date_interval = []
        self.interval_processing = False
        self.xmldoc = minidom.parse(path)

    def get_events(self):
        events = []
        for comp in self.xmldoc.getElementsByTagName('Date'):
            ev = self.__construct_event(comp)
            if not self.interval_processing and ev.date_interval[0].year != '' and ev.date_interval[1].year != '':
                events.append(ev)
                self.date_interval.clear()
        return events

    def __construct_event(self, event_xml):
        date = Date()
        # date.designation = self.__extract_date_element(event_xml, 'Designation')
        # date.time_of_day = self.__extract_date_element(event_xml, 'TimeOfDay')
        # date.century = self.__extract_date_element(event_xml, 'Century')
        # date.millenium = self.__extract_date_element(event_xml, 'Millenium')
        date.day = self.__extract_date_element(event_xml, 'Day')
        date.month = self.__extract_date_element(event_xml, 'Month')
        date.year = self.__extract_date_element(event_xml, 'Year')
        date.is_bc = self.__extract_date_element(event_xml, 'IsBC')
        date_pos = int(self.__extract_date_attribute(event_xml, 'pos'))
        date_len = int(self.__extract_date_attribute(event_xml, 'len'))
        date.in_text = self.__extract_date_in_text(date_pos, date_len)
        if self.interval_processing:
            self.interval_processing = False
            self.date_interval.append(date)
        elif self.__extract_date_element(event_xml, 'IsInterval') != '':
            self.date_interval.append(date)
            self.interval_processing = True
        else:
            self.date_interval.append(date)
            self.date_interval.append(date.copy())
        return Event(self.date_interval.copy(), re.sub('донэ', 'до н.э.', self.__extract_sentence_from_lead(event_xml)))

    def __extract_date_attribute(self, event_xml, attr_name):
        return event_xml.attributes[attr_name].value

    def __extract_date_element(self, event_xml, el_name):
        el = event_xml.getElementsByTagName(el_name)
        if len(el) == 0:
            return ""
        return el[0].attributes['val'].value

    def __extract_sentence_from_lead(self, event_xml):
        lead_id_needed = self.__extract_date_attribute(event_xml, 'LeadID')
        leads = self.xmldoc.getElementsByTagName('Lead')

        html_text = ''
        for lead in leads:
            lead_id = self.__extract_date_attribute(lead, 'id')
            if lead_id == lead_id_needed:
                html_text = self.__extract_date_attribute(lead, 'text')
                break
        length = len(html_text)
        res = ''
        pop_s = False
        h = False
        i = -1
        while i < length - 1:
            i += 1
            if html_text[i] == 'h':
                if html_text[i + 1] == '>' and h:
                    h = False
            if h:
                continue
            elif not pop_s:
                if html_text[i] == '<':
                    pop_s = True
                    if html_text[i + 1] == 'h':
                        h = True
                else:
                    res += html_text[i]
            else:
                if html_text[i] == '>':
                    pop_s = False
        return res

    def __extract_date_in_text(self, pos, len):
        file = codecs.open(self.path_to_text, 'r', 'utf-8')
        text = file.read()
        file.close()
        return text[pos:pos + len]

    def __extract_date_in_text_lead(self, event_xml):
        lead_id_needed = self.__extract_date_attribute(event_xml, 'LeadID')
        leads = self.xmldoc.getElementsByTagName('Lead')

        html_text = ''
        for lead in leads:
            lead_id = self.__extract_date_attribute(lead, 'id')
            if lead_id == lead_id_needed:
                html_text = self.__extract_date_attribute(lead, 'text')
                break

        if html_text == '':
            return ''

        html_parser = ParserDateInLead()
        lead_terminals = html_parser.get_terminals(html_text)

        event_terminals = self.__extract_date_attribute(event_xml, 'FieldsInfo')
        event_terminals = event_terminals.split(';')[:-1]

        result = ''
        for term in event_terminals:
            result += lead_terminals[term] + ' '
        return result
