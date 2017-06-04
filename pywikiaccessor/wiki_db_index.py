# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod


# import pymysql

class myWikiDBdriver:
    def __init__(self, dbConfig):
        self.config = dbConfig
        # self.dbConnection = pymysql.connect(
        #     host=self.config.host,
        #     port=self.config.port,
        #     user=self.config.user,
        #     passwd=self.config.password,
        #     charset='utf8',
        #     db=self.config.database)

    def containsTable(self, table):
        True or False


class postgreWikiDBdriver:


class WikiStore(metaclass=ABCMeta):
    def __init__(self, wikiAccessor):
        self.accessor = wikiAccessor
        self.directory = wikiAccessor.directory
        self.dictionaries = {}
        self.loadOrBuild()

    @abstractmethod
    def save(self):
        pass

    @abstractmethod
    def load(self):
        pass
