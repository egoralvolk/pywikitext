# -*- coding: utf-8 -*-
import codecs
import xml.sax

from pywikiaccessor import wiki_accessor
from pywikiaccessor.wiki_file_index import WikiFileIndex

class WikiBaseIndex (WikiFileIndex):
    def __init__(self, wikiAccessor):
        super(WikiBaseIndex, self).__init__(wikiAccessor)
        self.textDict = self.dictionaries['textIndex']
    
    def getDictionaryFiles(self): 
        return ['textIndex']
    def getOtherFiles(self):    
        return ["text.dat"]
    
    def loadOtherFiles(self):    
        self.textFile = open(self.directory+"text.dat", 'rb')
                                
    def getBuilder(self):
        return WikiBaseIndexBuilder(self.directory,"articles.xml")
    def getName(self):
        return "base"
    def getTextArticleById(self, ident):
        if not self.textDict.get(ident, None):
            return None
        else:
            self.textFile.seek(self.textDict[ident],0)
            lenBytes = self.textFile.read(4)
            length = int.from_bytes(lenBytes, byteorder='big')
            return self.textFile.read(length).decode("utf-8") 
    def getCount(self):
        return len(self.textDict)
    def getIds(self):
        return list(self.textDict.keys()) 
    
class WikiTitleBaseIndex (WikiFileIndex):
    def __init__(self, wikiAccessor):
        super(WikiTitleBaseIndex, self).__init__(wikiAccessor)
        self.titleDict = self.dictionaries['title_RawTitleIndex']
    def getDictionaryFiles(self): 
        return ['title_RawTitleIndex']
    def getOtherFiles(self):    
        return []
    def loadOtherFiles(self):    
        pass
    def getBuilder(self):
        return WikiBaseIndexBuilder(self.directory,"articles.xml")
    def getName(self):
        return "baseTitle"
    def getTitleArticleById(self, ident):
        return self.titleDict.get(ident, None) 
    def getCount(self):
        return len(self.textDict)
    def getIds(self):
        return list(self.textDict.keys())     
    
class WikiBaseIndexBuilder:     
    def __init__(self, directory,wikiDumpFile):
        self.directory = directory
        self.wikiDumpFile = wikiDumpFile       
    def build(self):
        inputXml = codecs.open(self.directory+self.wikiDumpFile, 'r', 'utf-8')
        from pywikiaccessor import xml_wiki_parser
        xml.sax.parse(inputXml, xml_wiki_parser.XMLWikiParser(self.directory))

# directory = "D:\\Git\\pywikitext-master\\indexes\\"
# base = WikiBaseIndexBuilder(directory, "articles.xml")
# base.build()