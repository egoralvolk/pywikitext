# -*- coding: utf-8 -*-
from pytextutils.token_splitter import TokenSplitter, SIGNS, TYPE_SIGN
from pywikiaccessor.wiki_tokenizer import WikiTokenizer
from pywikiaccessor.wiki_accessor import WikiAccessor
from pywikiaccessor.wiki_iterator import WikiIterator
from pywikiaccessor.wiki_file_index import WikiFileIndex
from pywikiaccessor.document_type import DocumentTypeIndex
import numpy as np

POS = ['VERB', 'INFN', 'PRTF', 'PRTS','GRND','NOUN','NPRO','ADJF','ADJS','COMP','ADVB','PRED','PREP','CONJ','PRCL','INTJ','NUMR']
WORD_POS = ['VERB', 'INFN', 'PRTF', 'PRTS','GRND','ADVB','PRED','PREP','CONJ','PRCL','INTJ']
DIAPASONS = {
    'CASE': [0,7],
    'NOM': [8,10],
    'GENDER': [11,14],
    'POS': [15,len(POS)+15],
    'SIGNS': [len(POS)+16,len(POS)+len(SIGNS)+16],
    'WORDS': [len(POS)+len(SIGNS)+17,0],
    }
'''
часть речи 16
падеж 7
число 2
род 3
конкретное слово
конкретный знак
'''  
class MorphBits:
    def __init__(self, words):
        self.arraySize = len(POS)+12+len(words)+len(SIGNS)
        self.words = words
    def getArray(self,tokens):
        res = np.zeros((self.arraySize,len(tokens)),dtype=np.int8)
        for i in range(0,len(tokens)-1):
            res[i] = self.__getOneToken(res[i],tokens[i])
        return res
    def __getOneToken(self,token):
        
        if token.tokenType == TYPE_SIGN:
            ind = SIGNS.index(token.token)
            
import pickle

from pytextutils.formal_grammar import SentenceSplitter
from pytextutils.science_patterns import calcHist    
from math import sqrt            
class Fragmentator:
    def __init__(self,accessor):
        with open(self.accessor.directory+self.prefix+'tfidf.pcl', 'wb') as f:
            self.fragmentTypes = pickle.load(f)
        self.lengths = {}
        for fType in self.fragmentTypes:
            self.lengths[fType] = {}
            for pos in self.fragmentTypes[fType]:
                self.lengths[fType][pos] = sum(map(lambda x:x*x,list(self.fragmentTypes[fType][pos].values())))
                
    def distance (self,textHist,fragmentTypeTfIdf,POS,fLength):
        length = sum(map(lambda x:x*x,list(textHist[POS].values())))
        total = 0 
        for word in textHist[POS]:
            if fragmentTypeTfIdf.get(word,None):
                total += fragmentTypeTfIdf[POS][word] * textHist[POS][word]
        return total/sqrt(length*fLength)     
            
    def mark(self,text):
        fragments = []
        ts = TokenSplitter()
        ts.split(text)
        tokens = ts.getTokenArray()
           
        ss = SentenceSplitter()
        ss.combineTokens(tokens)
        bestDistances = {}
        for sentence in tokens:
            hist = calcHist(sentence.internalTokens)
            for POS in hist 
