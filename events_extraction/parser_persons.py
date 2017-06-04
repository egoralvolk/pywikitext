from xml.dom import minidom
from .components import *


class ParserPerson:
    def __init__(self, path):
        self.xmldoc = minidom.parse(path)

    def get_persons(self):
        persons = []
        for comp in self.xmldoc.getElementsByTagName('Person'):
            persons.append(self.__construct_component(comp))
        return persons

    def __construct_component(self, component_xml):
        person = Person()
        person.surname = self.__extract_component_element(component_xml, 'Name_Surname')
        person.name = self.__extract_component_element(component_xml, 'Name_FirstName')
        person.patron = self.__extract_component_element(component_xml, 'Name_Patronymic')
        return person

    def __extract_component_element(self, component_xml, el_name):
        el = component_xml.getElementsByTagName(el_name)
        if len(el) == 0:
            return ""
        return el[0].attributes['val'].value
