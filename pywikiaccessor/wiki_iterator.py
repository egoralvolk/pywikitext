# -*- coding: utf-8 -*-
from pywikiaccessor.wiki_base_index import WikiBaseIndex
from abc import ABCMeta, abstractmethod

class WikiIterator(metaclass=ABCMeta):
    def __init__(self, accessor, fileCount, docList = None, prefix = ''):
        self.accessor = accessor
        self.fileCount = fileCount
        self.docList = docList
        self.prefix = prefix
        self.wikiIndex = self.accessor.getIndex(WikiBaseIndex)

    def build (self, start=0):
        self.clear()
        self.preProcess()
        articlesCount = 0
        self.prevArticlesCount = 0
        if self.docList:
            indexes = self.docList
        else:  
            indexes = self.wikiIndex.getIds()
        indexes = indexes[start:len(indexes)]
        print("Need to process "+str(len(indexes)) + " docs.")
        for i in indexes:
            articlesCount += 1
            self.processDocument(i)
            if (articlesCount % self.fileCount == 0):
                print("Processed "+str(articlesCount))
                self.save(articlesCount)
                self.clear() 
        print("Processed "+str(articlesCount))
        self.save(articlesCount)
        self.postProcess()
    
    def getFullFileName(self,fileName):
        return self.accessor.directory + self.prefix + fileName            
    def save(self,articlesCount): 
        self.processSave(articlesCount)
        self.prevArticlesCount = articlesCount 
        
    @abstractmethod
    def processSave(self,articlesCount):    
        pass
    @abstractmethod
    def preProcess(self):
        pass
    @abstractmethod
    def postProcess(self):
        pass
    @abstractmethod
    def clear(self):
        pass            
    @abstractmethod
    def processDocument(self, docId):
        pass            
            