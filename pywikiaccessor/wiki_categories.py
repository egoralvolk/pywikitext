# -*- coding: utf-8 -*-
import pickle
import re

from pywikiaccessor import wiki_iterator, wiki_file_index, wiki_base_index, wiki_sql_loader

class CategoryIndex (wiki_file_index.WikiFileIndex):
    def __init__(self, wikiAccessor):
        super(CategoryIndex, self).__init__(wikiAccessor)

    def getDictionaryFiles(self): 
        return [
            'cat_TitleToIdIndex',
            'cat_IdToTitleIndex',
            'cat_IdToChildrenIndex',
            'cat_IdToParentIndex',
            'cat_IdToPagesIndex',
            'cat_PagesToCatIndex']
                        
    def getTitleById(self, ident):
        if len(self.dictionaries['cat_IdToTitleIndex']) <= ident:
            return None
        return self.dictionaries['cat_IdToTitleIndex'][ident]
    
    def getIdByTitle(self, title):
        key = title.lower().replace("_"," ")
        return self.dictionaries['cat_TitleToIdIndex'].get(key, None)

    def getSubCatAsSet(self,catId):
        res = set()
        subCats = self.dictionaries['cat_IdToChildrenIndex'][catId]
        res.update(subCats)
        for cat in subCats:
            res.update(self.getSubCatAsSet(cat))
        return res

    def getAllParentsAsSet(self,catId):
        res = set()
        parCats = self.dictionaries['cat_IdToParentIndex'][catId]
        res.update(parCats)
        for cat in parCats:
            res.update(self.getAllParentsAsSet(cat))
        return res
    
    def getAllPagesAsSet(self,catId):
        res = set()
        res.update(self.getDirectPages(catId))
        subCats = self.getSubCatAsSet(catId)
        for cat in subCats:
            res.update(self.getDirectPages(cat))
        return res      
    def getPageDirectCategories(self,docId):
        return self.dictionaries['cat_PagesToCatIndex'].get(docId,[])    
    def getDirectPages(self,catId):
        return self.dictionaries['cat_IdToPagesIndex'][catId]    
    def getBuilder(self):
        return CategoryIndexBuilder(self.accessor)
    def getName(self):
        return "categories"
    
class CategoryIndexBuilder:
    def __init__(self, accessor):
        self.fromPagesBuilder = CategoryFromPagesBuilder(accessor)
        self.fromCatlinksBuilder = CategoryFromCatlinksBuilder(accessor)
    def build(self):
        self.fromPagesBuilder.build()
        self.fromCatlinksBuilder.build(self.fromPagesBuilder)
        
class CategoryFromCatlinksBuilder:
    def __init__(self, accessor):
        self.accessor = accessor
    def build(self, dictionaries = None):
        wl = wiki_sql_loader.WikiSqlLoader()
        if dictionaries:
            self.toTitleDict = dictionaries.toTitleDict
            self.toIdDict = dictionaries.toIdDict
            self.toParentDict = dictionaries.toParentDict
            self.toChildrenDict = dictionaries.toChildrenDict
            self.toPagesDict = dictionaries.toPagesDict
            self.toPageCatDict = dictionaries.toPageCatDict
            self.catPagesRenumerer = dictionaries.catPagesRenumerer
        else:
            self.toTitleDict = []
            self.toIdDict = {}
            self.toParentDict = []
            self.toChildrenDict = []
            self.toPagesDict = []
            self.toPageCatDict = {}
            self.catPagesRenumerer = {}
        self.count = 0
        wl.parse(self.accessor.directory+"categorylinks.sql",self)
        saveDictionaries(self)
    def getOrAdd(self,title):
        clearTitle = title.lower().replace("_"," ")
        catId = self.toIdDict.get(clearTitle,None)
        if not catId:
            catId = len(self.toIdDict)
            self.toIdDict[clearTitle] = catId
            self.toTitleDict.append(clearTitle)
            self.toParentDict.append([])
            self.toChildrenDict.append([])
            self.toPagesDict.append([])
        return catId     
    def consume(self,data):    
        docId = data[0];
        parentCatId = self.getOrAdd(data[1])
        if data[1] in ['page','file']:
            self.toPagesDict[parentCatId].append(docId)
            self.toPageCatDict[docId].append(parentCatId)
        else:
            catId = self.catPagesRenumerer.get(docId,None)
            if catId:
                self.toParentDict[catId].append(parentCatId)
                self.toChildrenDict[parentCatId].append(catId)
        self.count+=1
        if self.count%10000 == 0:
            print("Processed "+str(self.count)+" categories")        
    def getFullFileName(self,fileName):
        return self.accessor.directory + fileName     
        
def saveDictionaries(dictionaries):
    with open(dictionaries.getFullFileName('cat_TitleToIdIndex.pcl'), 'wb') as f:
        pickle.dump(dictionaries.toIdDict, f, pickle.HIGHEST_PROTOCOL)
    with open(dictionaries.getFullFileName('cat_IdToTitleIndex.pcl'), 'wb') as f:
        pickle.dump(dictionaries.toTitleDict, f, pickle.HIGHEST_PROTOCOL)
    with open(dictionaries.getFullFileName('cat_IdToChildrenIndex.pcl'), 'wb') as f:
        pickle.dump(dictionaries.toChildrenDict, f, pickle.HIGHEST_PROTOCOL)
    with open(dictionaries.getFullFileName('cat_IdToParentIndex.pcl'), 'wb') as f:
        pickle.dump(dictionaries.toParentDict, f, pickle.HIGHEST_PROTOCOL)
    with open(dictionaries.getFullFileName('cat_IdToPagesIndex.pcl'), 'wb') as f:
        pickle.dump(dictionaries.toPagesDict, f, pickle.HIGHEST_PROTOCOL)
    with open(dictionaries.getFullFileName('cat_PagesToCatIndex.pcl'), 'wb') as f:
        pickle.dump(dictionaries.toPageCatDict, f, pickle.HIGHEST_PROTOCOL)
                
class CategoryFromPagesBuilder (wiki_iterator.WikiIterator):
    def __init__(self, accessor):
        self.CODE = 'utf-8'
        super(CategoryFromPagesBuilder, self).__init__(accessor, 1000000)

    def processSave(self,articlesCount):
        return

    def postProcess(self):
        saveDictionaries(self)
        with open(self.getFullFileName('cat_CategoryPages.pcl'), 'wb') as f:
            pickle.dump(self.catPagesRenumerer, f, pickle.HIGHEST_PROTOCOL)

    def preProcess(self):
        self.toTitleDict = []
        self.toIdDict = {}
        self.toParentDict = []
        self.toChildrenDict = []
        self.toPagesDict = []
        self.toPageCatDict = {}
        self.catPagesRenumerer = {}
        self.categoryPattern = re.compile("\[\[[ \t]*категория:([^\]\|]*)\]\]")
        self.titleIndex = self.accessor.getIndex(wiki_base_index.WikiTitleBaseIndex)
            
    def clear(self):
        return 

    def getOrAdd(self,title):
        clearTitle = title.lower().replace("_"," ")
        catId = self.toIdDict.get(clearTitle,None)
        if not catId:
            catId = len(self.toIdDict)
            self.toIdDict[clearTitle] = catId
            self.toTitleDict.append(clearTitle)
            self.toParentDict.append([])
            self.toChildrenDict.append([])
            self.toPagesDict.append([])
        return catId 
          
    def processDocument(self, docId):
        title = self.titleIndex.getTitleArticleById(docId).lower()
        catId = None
        if title.startswith("категория:"):
            catId = self.getOrAdd(title[10:])
            self.catPagesRenumerer[docId] = catId
            
        text = self.wikiIndex.getTextArticleById(docId).lower()
        
        for match in self.categoryPattern.finditer(text):
            if not self.toPageCatDict.get(docId,None):
                self.toPageCatDict[docId] = []
            parentCatId = self.getOrAdd(match.group(1))
            if catId:
                self.toParentDict[catId].append(parentCatId)
                self.toChildrenDict[parentCatId].append(catId)
            self.toPagesDict[parentCatId].append(docId)
            self.toPageCatDict[docId].append(parentCatId)

if __name__ == "__main__":
    from pywikiaccessor import wiki_accessor
    from pywikiaccessor import title_index
    directory = "D:\\Git\\pywikitext-master\\indexes\\"
    accessor =  wiki_accessor.WikiAccessor(directory)
    catsIndex = CategoryIndex(accessor)
    titleIndex = title_index.TitleIndex(accessor)
    print(titleIndex.getTitleById(4820996))
# artics = catsIndex.getAllPagesAsSet(catsIndex.getIdByTitle("Революции в России"))
# for a in artics:
#     print(titleIndex.getTitleById(a))
#titleIndex = accessor.getIndex(title_index.TitleIndex)
#docId = titleIndex.getIdByTitle('Ван Боксхорн, Маркус')
#bld = CategoryIndexBuilder(accessor)
#bld.preProcess()
#bld.processDocument(docId)
#print(bld.toPagesDict)
#print(bld.toTitleDict)
#bld.build()

