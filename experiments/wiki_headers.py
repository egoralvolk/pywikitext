# -*- coding: utf-8 -*-
import pymysql
from pytextutils.token_splitter import ALL_CYR_LETTERS
from pywikiaccessor.wiki_tokenizer import WikiTokenizer
from pywikiaccessor.wiki_accessor import WikiAccessor
from pywikiaccessor.wiki_iterator import WikiIterator
from pywikiaccessor.wiki_file_index import WikiFileIndex
from pywikiaccessor.document_type import DocumentTypeIndex
from pywikiaccessor.redirects_index import RedirectsIndex
import re
import pickle

# Класс для выделения markdown-заголовков в тексте
class HeadersExtractor:
    def __init__(self,headerRenumerer):
        self.cleaner = WikiTokenizer()
        self.headerRenumerer = headerRenumerer
        self.headerTemplates = [
                re.compile('\n[ \t]*======([^=]*)======[ \t\r]*\n'),
                re.compile('\n[ \t]*=====([^=]*)=====[ \t\r]*\n'),
                re.compile('\n[ \t]*====([^=]*)====[ \t\r]*\n'),
                re.compile('\n[ \t]*===([^=]*)===[ \t\r]*\n'),
                re.compile('\n[ \t]*==([^=]*)==[ \t\r]*\n'),
                re.compile('\n[ \t]*=([^=]*)=[ \t\r]*\n'),
            ]
    
    def getHeadersForDoc(self, docId, text):        
        text = text.lower()
        headers = []
        htype = 6
        for template in self.headerTemplates:
            for match in template.finditer(text):
                header = self.cleaner.clean(match.group(1))
                if any(ch in ALL_CYR_LETTERS for ch in header):
                    header_id = self.headerRenumerer(header)
                    if header_id: 
                        headers.append({'header':header_id,'type':htype,'position_start':match.end(),'position_match':match.start()})
            htype -= 1
        headers.sort(key=lambda header: header['position_match'])
        return headers

# Билдер файлового индекса заголовков
class HeadersFileBuilder (WikiIterator):
    def __init__(self, accessor, docIds = None, prefix =''):
        super(HeadersFileBuilder, self).__init__(accessor, 1000, docIds, prefix)

    def processSave(self,articlesCount):
        pass
   
    def preProcess(self):
        self.redirects = self.accessor.getIndex(RedirectsIndex) 
        self.doctypeIndex = DocumentTypeIndex(self.accessor)
        self.headersExtractor = HeadersExtractor(self.getHeaderId)
 
        self.clear()
        self.headersToIds = {}
        self.idsToHeaders = []
        self.headerDocuments = {}
        self.documentHeaders = {}
    
    def postProcess(self):
        with open(self.getFullFileName('HeadersToIds.pcl'), 'wb') as f:
            pickle.dump(self.headersToIds, f, pickle.HIGHEST_PROTOCOL)
        with open(self.getFullFileName('IdsToHeaders.pcl'), 'wb') as f:
            pickle.dump(self.idsToHeaders, f, pickle.HIGHEST_PROTOCOL)
        with open(self.getFullFileName('HeaderDocuments.pcl'), 'wb') as f:
            pickle.dump(self.headerDocuments, f, pickle.HIGHEST_PROTOCOL)
        with open(self.getFullFileName('DocumentHeaders.pcl'), 'wb') as f:
            pickle.dump(self.documentHeaders, f, pickle.HIGHEST_PROTOCOL)
           
    def clear(self):
        pass

    def getHeaderId(self,header):
        header = header.replace("ё","е")
        header = header.replace("\\","").strip()
        if not self.headersToIds.get(header,None):
            self.headersToIds[header] = len(self.idsToHeaders)  
            self.idsToHeaders.append(header)
        return self.headersToIds[header]    
        
    def processDocument(self, docId):
        if self.redirects.isRedirect(docId):
            return
        if self.doctypeIndex.isDocType(docId,'wiki_stuff'):
            return
        headers = self.headersExtractor.getHeadersForDoc(docId,self.wikiIndex.getTextArticleById(docId))
        self.documentHeaders[docId] = headers 
        for h in headers:
            if not self.headerDocuments.get(h['header'],None):
                self.headerDocuments[h['header']] = []
            self.headerDocuments[h['header']].append(docId)

# Файловый индекс заголовков             
class HeadersFileIndex(WikiFileIndex):
    def __init__(self, wikiAccessor,prefix =''):
        super(HeadersFileIndex, self).__init__(wikiAccessor,prefix)

    def getDictionaryFiles(self): 
        return ['HeadersToIds','IdsToHeaders','HeaderDocuments','DocumentHeaders']
    def getAllStat(self):
        sortedHeaders = sorted(self.dictionaries['HeaderDocuments'],key=lambda header: len(self.dictionaries['HeaderDocuments'][header]),reverse=True)
        res = []
        for element in sortedHeaders:
            res.append ({'id': element,'text': self.dictionaries['IdsToHeaders'][element],'cnt': len(self.dictionaries['HeaderDocuments'][element])})
        return res
    def headerId(self,header):
        return self.dictionaries['HeadersToIds'].get(header.strip().lower(),None)
    def documentsByHeader(self,header):
        headerId = self.dictionaries['HeadersToIds'].get(header.strip().lower(),None)
        if not headerId:
            return []
        return self.dictionaries['HeaderDocuments'].get(headerId,None)                      
    def headersByDoc(self,docId):
        return self.dictionaries['DocumentHeaders'].get(docId,None)   
    def getBuilder(self):
        return HeadersFileBuilder(self.accessor,self.prefix)
    def getName(self):
        return "headers"            

'''
Билдер индекса заголовков, хранящийся в базе

Требует:
+ базовый индекс сырых текстов Википедии
+ индекс типов документов
+ индекс редиректов

Схема:

DROP TABLE IF EXISTS `verbs`;
CREATE TABLE IF NOT EXISTS `verbs` (
`id` int(11) NOT NULL,
  `stem` varchar(200) CHARACTER SET utf8 NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

DROP TABLE IF EXISTS `verb_to_doc`;
CREATE TABLE IF NOT EXISTS `verb_to_doc` (
`id` int(11) NOT NULL,
  `doc_id` int(11) NOT NULL,
  `verb_id` int(11) NOT NULL,
  `is_ambig` tinyint(1) NOT NULL,
  `position` mediumint(9) NOT NULL,
  `score` float NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

ALTER TABLE `verbs`
 ADD PRIMARY KEY (`id`), ADD UNIQUE KEY `id` (`id`);

ALTER TABLE `verb_to_doc`
 ADD PRIMARY KEY (`id`), ADD KEY `doc_id` (`doc_id`), ADD KEY `verb_id` (`verb_id`);

ALTER TABLE `verbs`
MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `verb_to_doc`
MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
'''

class HeadersDBBuilder (WikiIterator):
    def __init__(self, accessor, docIds = None):
        super(HeadersDBBuilder, self).__init__(accessor, 1000, docIds)

    def processSave(self,articlesCount):
        pass
   
    def preProcess(self):
        self.dbConnection = pymysql.connect(host='localhost', port=3306, user='root', passwd='',charset='utf8', db='wikiparse')
        self.dbCursor = self.dbConnection.cursor()
        self.redirects = self.accessor.getIndex(RedirectsIndex) 
        self.doctypeIndex = DocumentTypeIndex(self.accessor)
        self.headersExtractor = HeadersExtractor(self.getHeaderId)
 
        self.clear()
        self.headers = {}
        self.addHeaderQuery = "INSERT INTO headers(text) VALUES (%s)"
        self.getHeaderIdQuery = "SELECT id FROM headers WHERE text LIKE %s"
        self.insertHeaderToDocQuery = "INSERT INTO header_to_doc(doc_id,header_id,pos_start,pos_end,type) VALUES "
        self.isDocAlreadySaveQuery = "SELECT count(id) as cnt FROM `header_to_doc` WHERE doc_id = %s group by doc_id"

        self.queryElement = "(%s, %s, %s, %s, %s)"
        
        self.dbCursor.execute("SELECT * FROM headers ORDER BY id")
        for element in self.dbCursor.fetchall():
            self.headers[element[1]] = element[0] 
    
    def postProcess(self):
        pass
           
    def clear(self):
        pass
    
    # Проверяем, был ли документ обработан ранее
    def isDocAlreadySave(self,docId):
        self.dbCursor.execute(self.isDocAlreadySaveQuery,(docId))
        count = self.dbCursor.fetchone()
        if not count:
            return False
        return count[0] > 0
    
    # Определяет или генерирует идентификатор заголовка
    def getHeaderId(self,header):
        header = header.replace("ё","е")
        header = header.replace("\\","").strip()
        header_id = self.headers.get(header,None)
        if not header_id:
            self.dbCursor.execute(self.addHeaderQuery,(header))
            self.dbConnection.commit()
            self.dbCursor.execute(self.getHeaderIdQuery,(header))
            header_id = self.dbCursor.fetchone()
            if not header_id:
                print(header)
            else:
                self.headers[header] = header_id[0]
        return header_id    
    
    # Обработка документа    
    def processDocument(self, docId):
        #страницы-редиректы не обрабатываем
        if self.redirects.isRedirect(docId):
            return
        # служебные страницы не обрабатываем
        if self.doctypeIndex.isDocType(docId,'wiki_stuff'):
            return
        # уже сохраненные не обрабатываем
        if self.isDocAlreadySave(docId):
            return
        # получаем текст статьи
        text = self.wikiIndex.getTextArticleById(docId)
        # получаем из текста заголовки в виде структурок
        headers = self.headersExtractor.getHeadersForDoc(docId,text)
        
        # формируем запрос    
        query = []
        params = []            
        for header_id in range(0,len(headers)-1):
            query.append(self.queryElement)
            params.append(docId)
            params.append(headers[header_id]["header"])
            params.append(headers[header_id]["position_start"])
            if header_id != len(headers)-1:
                params.append(headers[header_id+1]["position_match"])
            else:
                params.append(len(text))
            params.append(headers[header_id]["type"])
        # Выполняем запрос    
        if len(query)>0 :
            self.dbCursor.execute(self.insertHeaderToDocQuery+",".join(query),params)
            self.dbConnection.commit()
        #else:
            # print (docId)

class HeadersDBIndex:
    def __init__(self,accessor):
        self.dbConnection = pymysql.connect(host='localhost', port=3306, user='root', passwd='',charset='utf8', db='wikiparse')
        self.dbCursor = self.dbConnection.cursor()         
        self.getAllStatQuery = '''
            SELECT headers.id as id, headers.text as text, count(`header_to_doc`.id) as cnt 
            FROM `header_to_doc`, headers 
            WHERE `header_to_doc`.header_id = headers.id 
            GROUP BY headers.id 
            ORDER BY cnt desc
            '''
        self.countHeadersForDocQuery = '''
            SELECT `header_to_doc`.doc_id, count(`header_to_doc`.id) as cnt 
            FROM `header_to_doc` 
            GROUP BY `header_to_doc`.doc_id 
            ORDER BY cnt desc
            LIMIT 200
            '''
    def getCountHeadersForDoc(self, docIds):
        #.format(','.join(str(x) for x in docIds)
        self.dbCursor.execute(self.countHeadersForDocQuery)
        res = []
        for element in self.dbCursor.fetchall():
            res.append ({'id': element[0],'cnt': element[1]})
        return res                
    def getAllStat(self, docIds):
        self.dbCursor.execute(self.getAllStatQuery)
        res = []
        for element in self.dbCursor.fetchall():
            res.append ({'id': element[0],'text': element[1],'cnt': element[2]})
        return res    
  
      
#regex1 = re.compile('\n[ \t]*==([^=]*)==[ \t\r]*\n')
#text = " kdkd\n == kdkd==\n"
#match = regex1.search(text)
#print(match.end())
#directory = "C:\\WORK\\science\\onpositive_data\\python\\"
#accessor = WikiAccessor(directory)
#docTypesIndex = DocumentTypeIndex(accessor)
#docIds = docTypesIndex.getDocsOfType("sciense")
#titleIndex = accessor.titleIndex
#doc_id = titleIndex.getIdByTitle("Пушкин, Александр Сергеевич")
#hb = HeadersDBBuilder(accessor,list(docIds))
#hb.build()
#hb.preProcess()
#hb.processDocument(doc_id)
#hi = HeadersDBIndex(accessor)
#hi.getCountHeadersForDoc(docIds)
#stat = hi.getAllStat(docIds)
#for s in stat:
#    print (s['text']+": "+str(s['cnt']))
   
  
 