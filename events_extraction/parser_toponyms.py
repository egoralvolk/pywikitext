from xml.dom import minidom
from .components import *


class ParserToponym:
    def __init__(self, path):
        self.xmldoc = minidom.parse(path)

    def get_toponyms(self):
        toponyms = []
        for comp in self.xmldoc.getElementsByTagName('Toponym'):
            toponyms.append(self.__construct_component(comp))
        return toponyms

    def __construct_component(self, component_xml):
        toponym = Toponym()
        toponym.name = self.__extract_component_element(component_xml, 'Name')
        return toponym

    def __extract_component_element(self, component_xml, el_name):
        el = component_xml.getElementsByTagName(el_name)
        if len(el) == 0:
            return ""
        return el[0].attributes['val'].value
