import re

import datetime

from EventsExtaction import eventsextractor as evex
from pywikiaccessor import wiki_base_index, title_index
from pywikiaccessor import wiki_accessor
from pywikiaccessor import wiki_plain_text_index
from pywikiaccessor import document_type
from pywikiaccessor import wiki_tokenizer
import psycopg2 as pgsql


# ♥
class HandlerWikiArticle:
    def __init__(self, directory):
        self.event_extractor = evex.EventsExtractor(path_to_tomita='../EventsExtaction/tomita/')
        self.directory = directory
        self.pattern_template = re.compile("{{[^}]+}}")
        self.pattern_date = re.compile("\|[ ]*дата[ ]*=([^\n]*)|"
                                       "\|[ ]*Дата[ ]*=([^\n]*)|"
                                       "\|[ ]*date[ ]*=([^\n]*)|"
                                       "\|[ ]*Date[ ]*=([^\n]*)")
        self.pattern_name = re.compile(
            "\|[ ]*конфликт[ ]*=([^\n\({]+)|"
            "\|[ ]*Конфликт[ ]*=([^\n\({]+)|"
            "\|[ ]*Название[ ]*=([^\n\({]+)|"
            "\|[ ]*название[ ]*=([^\n\({]+)|"
            "\|[ ]*conflict[ ]*=([^\n\({]+)|"
            "\|[ ]*Conflict[ ]*=([^\n\({]+)|"
            "\|[ ]*name[ ]*=([^\n\({]+)|"
            "\|[ ]*Name[ ]*=([^\n\({]+)")
        self.pattern_event_type = re.compile("^[^|{<\(]+")

    def handle_article(self, id):
        accessor = wiki_accessor.WikiAccessor(self.directory)
        text_article = wiki_base_index.WikiBaseIndex(accessor).getTextArticleById(id)
        plain_text_article = wiki_tokenizer.WikiTokenizer().clean(
            re.sub('-', ' - ', wiki_base_index.WikiBaseIndex(accessor).getTextArticleById(id)))
        len_article = len(plain_text_article)
        title, dates, event_type = self.get_info_from_template(text_article)
        processing_article = True
        if not (title and len(re.sub(' ', '', title)) and len(dates)):
            processing_article = False
        else:
            processing_article = not dates[0].date_is_bc()
        if processing_article:
            event_id = self.__save_event_to_database(title, dates[0].get_start_date(), dates[0].get_end_date(),
                                                     None, id, event_type, None)
            if len_article < 40000:
                events = self.event_extractor.extract_events_from_article(plain_text_article)
                print(title)
                for event in events:
                    if event.date_interval[0].year != '' and event.date_interval[1].year != '':
                        processing = True
                        if event.date_interval[0].to_datetime() != dates[0].get_start_date():
                            if difference_dates(event.date_interval[0].to_datetime(),
                                                dates[0].get_start_date()) > 200 * 365:
                                processing = False
                        else:
                            processing = False
                        if event.date_interval[1].to_datetime() != dates[0].get_end_date():
                            if difference_dates(event.date_interval[1].to_datetime(),
                                                dates[0].get_end_date()) > 200 * 365:
                                processing = False
                            else:
                                processing = True
                        if processing:
                            child_event = self.__save_event_to_database('', event.date_interval[0].to_datetime(),
                                                                        event.date_interval[1].to_datetime(), event_id,
                                                                        id, '', event.sentence)
                            relationship = comparing_events(dates[0].get_start_date(),
                                                            dates[0].get_end_date(),
                                                            event.date_interval[0].to_datetime(),
                                                            event.date_interval[1].to_datetime())
                            self.__save_relationship_to_database(child_event, relationship, event_id)
                            for person in event.persons:
                                person_id = self.__save_or_get_person_to_database(person.name, person.surname,
                                                                                  person.patron,
                                                                                  person.link_to_article)
                                self.__save_person_rel_event(child_event, person_id)
                            for toponym in event.toponyms:
                                toponym_id = self.__save_or_get_toponym_to_database(toponym.name)
                                self.__save_toponym_rel_event(child_event, toponym_id)
                                # print(str(date))

    def __save_event_to_database(self, name, start_date, end_date, parent_event_id, article_id, event_type, sentence):
        connection = pgsql.connect(host='localhost', user='postgres',
                                   password='123', database='wikievents')
        cur = connection.cursor()
        insert_event = """INSERT INTO
        rest_server_event(name, start_date, end_date, parent_event_id, article_id, event_type, sentence)
        VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id"""
        cur.execute(insert_event,
                    (name, start_date, end_date, parent_event_id, article_id, event_type, sentence))
        last_id = cur.fetchone()[0]
        connection.commit()
        connection.close()
        return last_id

    def __save_or_get_person_to_database(self, name, surname, patron, link_to_article):
        connection = pgsql.connect(host='localhost', user='postgres',
                                   password='123', database='wikievents')
        cur = connection.cursor()
        select_person = """SELECT id from rest_server_person where 
                              surname=%s and name=%s and patron=%s"""
        cur.execute(select_person, (surname, name, patron))
        if not cur.fetchone():
            insert_event = """INSERT INTO rest_server_person(name, surname, patron, link_to_article)
               VALUES (%s, %s, %s, %s) RETURNING id"""
            cur.execute(insert_event, (name, surname, patron, link_to_article))
            connection.commit()
        cur.execute(select_person, (surname, name, patron))
        person_id = cur.fetchone()[0]
        connection.close()
        return person_id

    def __save_person_rel_event(self, event_id, person_id):
        connection = pgsql.connect(host='localhost', user='postgres',
                                   password='123', database='wikievents')
        cur = connection.cursor()
        check_exist_relation = """SELECT id from rest_server_event_persons 
                                    where event_id=%s and person_id=%s"""
        cur.execute(check_exist_relation, (event_id, person_id))
        if not cur.fetchone():
            insert_person = """INSERT INTO rest_server_event_persons(event_id, person_id)
               VALUES (%s, %s)"""
            cur.execute(insert_person, (event_id, person_id))
            connection.commit()
        connection.close()

    def __save_or_get_toponym_to_database(self, name):
        connection = pgsql.connect(host='localhost', user='postgres',
                                   password='123', database='wikievents')
        cur = connection.cursor()
        select_toponym = "SELECT id from rest_server_toponym where name=%s"
        cur.execute(select_toponym, (name,))
        if not cur.fetchone():
            insert_toponym = """INSERT INTO rest_server_toponym(name)
               VALUES (%s) RETURNING id"""
            cur.execute(insert_toponym, (name,))
            connection.commit()
        cur.execute(select_toponym, (name,))
        toponym_id = cur.fetchone()[0]
        connection.close()
        return toponym_id

    def __save_toponym_rel_event(self, event_id, toponym_id):
        connection = pgsql.connect(host='localhost', user='postgres',
                                   password='123', database='wikievents')
        cur = connection.cursor()
        check_exist_relation = """SELECT id from rest_server_event_toponyms 
                                    where event_id=%s and toponym_id=%s"""
        cur.execute(check_exist_relation, (event_id, toponym_id))
        if not cur.fetchone():
            insert_person = """INSERT INTO rest_server_event_toponyms(event_id, toponym_id)
               VALUES (%s, %s)"""
            cur.execute(insert_person, (event_id, toponym_id))
            connection.commit()
        connection.close()

    def __save_relationship_to_database(self, event_id, relationship, child_event_id):
        connection = pgsql.connect(host='localhost', user='postgres',
                                   password='123', database='wikievents')
        cur = connection.cursor()
        insert_person = """INSERT INTO 
            rest_server_relationshipofevents(child_event_id, relationship_direction, parent_event_id) 
            VALUES (%s, %s, %s)"""
        cur.execute(insert_person, (event_id, relationship, child_event_id))
        connection.commit()
        connection.close()

    def get_templates(self, text):
        templates = []
        curr_t = ""
        g = 0
        contin = False
        for i in range(len(text)):
            if contin:
                if text[i] == '}':
                    continue
                else:
                    contin = False
            if text[i] == '{':
                if text[i + 1] == '{':
                    g += 1
            if text[i] == '}':
                if g == 1:
                    curr_t += text[i]
                    templates.append(wiki_tokenizer.WikiTokenizer().clean(re.sub('^{*|}*$', '', curr_t)))
                    curr_t = ''
                if i + 1 < len(text):
                    if text[i + 1] == '}':
                        g -= 1
                        contin = True
            if g != 0:
                curr_t += text[i]
        return templates

    def get_info_from_template(self, text):
        templates = self.get_templates(text)
        wiki_tkn = wiki_tokenizer.WikiTokenizer()
        template = ""
        dates = ""
        for t in templates:
            if len(self.pattern_date.findall(t)) and len(self.pattern_name.findall(t)):
                template = t
                break
        if template != '':
            processing_date = False
            dates = self.pattern_date.findall(template)
            for d in dates:
                if sum_str_in_tuple(d) != '':
                    dates = re.sub('-', ' - ', wiki_tkn.clean(sum_str_in_tuple(d)))
                    processing_date = True
                    break
            if processing_date:
                dates = re.sub('\([^)]*\)', '', dates)
                dates = re.sub('&nbsp;—&nbsp;', ' — ', dates)
                dates = re.sub(',', '', dates)
                name = self.pattern_name.findall(template)
                event_type = re.sub('[^a-zA-Zа-яА-ЯёЁ ]', '', self.pattern_event_type.search(template).group())
                event_type = re.sub('^ | $', '', event_type.lower())
                if len(name) and len(re.sub(' ', '', dates)):
                    name = wiki_tkn.clean(sum_str_in_tuple(name[0]))
                    name = re.sub('^[^\w]*', '', name)
                    events = self.event_extractor.extract_events_from_article(dates)
                    # print(name, '\n', events[0])
                    return name, events, event_type
        return False, False, False

    def __handle_template(self, template):
        pass


def get_event_on_relationship(relationship, event_id):
    connection = pgsql.connect(host='localhost', user='postgres',
                               password='123', database='wikievents')
    cur = connection.cursor()
    select_events = """SELECT id, sentence, start_date, end_date, parent_event_id, article_id 
                        from rest_server_event 
                        where id in 
                        (select child_event_id from rest_server_relationshipofevents
                          where relationship_direction = %s and parent_event_id = %s)"""
    cur.execute(select_events, (relationship, event_id))
    events = cur.fetchall()
    connection.close()
    return events


def comparing_events(start_base_event, end_base_event, start_event, end_event):
    if start_event <= start_base_event:
        if end_event < start_base_event:
            return "предпосылка"
        elif end_event < end_base_event:
            return "причина"
        else:
            return "основное событие"
    else:
        if start_event > end_base_event:
            return "следствие"
        else:
            if end_event < end_base_event:
                return "часть"
            else:
                return "следствие"


def difference_dates(date1, date2):
    return abs(int(str(date1 - date2).split()[0]))


def sum_str_in_tuple(tpl):
    sum_str = ''
    for s in tpl:
        sum_str += s
    return sum_str


def get_events_for_category(event_type):
    connection = pgsql.connect(host='localhost', user='postgres',
                               password='123', database='wikievents')
    cur = connection.cursor()
    select_events = """SELECT id, name, start_date, end_date, parent_event_id, article_id
                          from rest_server_event where event_type=%s order by start_date"""
    cur.execute(select_events, (event_type,))
    res = cur.fetchall()
    connection.commit()
    connection.close()
    return res


def clean_record_with_event_type_in_database(event_type):
    connection = pgsql.connect(host='localhost', user='postgres',
                               password='123', database='wikievents')
    cur = connection.cursor()
    delete_event_toponyms = """DELETE from rest_server_event_toponyms where event_id 
	                            in (select id from rest_server_event where parent_event_id 
		                        in (select id from rest_server_event where event_type = %s))"""
    delete_event_persons = """DELETE from rest_server_event_persons where event_id 
	                            in (select id from rest_server_event where parent_event_id
		                        in (select id from rest_server_event where event_type = %s))"""
    delete_toponym = """DELETE from rest_server_toponym where 
                          id not in (select toponym_id from rest_server_event_toponyms)"""
    delete_person = """DELETE from rest_server_person 
                          where id not in (select person_id from rest_server_event_persons)"""
    delete_relationship = """DELETE from rest_server_relationshipofevents where child_event_id 
	                            in (select id from rest_server_event where parent_event_id
		                        in (select id from rest_server_event where event_type = %s))"""
    delete_child_events = """DELETE from rest_server_event 
                                where parent_event_id in (select id from rest_server_event where event_type = %s)"""
    delete_events = """DELETE from rest_server_event 
                                where event_type = %s"""
    cur.execute(delete_event_toponyms, (event_type,))
    cur.execute(delete_event_persons, (event_type,))
    cur.execute(delete_toponym)
    cur.execute(delete_person)
    cur.execute(delete_relationship, (event_type,))
    cur.execute(delete_child_events, (event_type,))
    cur.execute(delete_events, (event_type,))
    connection.commit()
    connection.close()


def console_interface():
    gen_menu = "\nДействия:\n" \
               "1. Извлечение\n" \
               "2. Демонстрация\n" \
               "Q. Выход\n" \
               "Выберите действие: "
    extraction = "\nИзвлечение:\n" \
                 "B. Назад\n" \
                 "1. Обновить полностью\n" \
                 "Выберите действие: "
    categories = "\nКатегории:\n" \
                 " B. Назад\n" \
                 " 1. Вооружённые конфликты \n" \
                 " 2. Террористические атаки\n" \
                 " 3. Революции\n" \
                 " 4. Массовые убийства\n" \
                 " 5. Метеориты\n" \
                 " 6. Землетрясения\n" \
                 " 7. Катастрофы\n" \
                 " 8. Кинофестивали\n" \
                 " 9. Конференции\n" \
                 "10. Свободные лицензии\n" \
                 "Выберите категорию: "
    x = input(gen_menu)
    while x.lower() != 'q':
        print(chr(27) + "[2J")
        if x == '1':
            directory = "D:\\Git\\pywikitext-master\\indexes\\"
            hwa = HandlerWikiArticle(directory)
            x = input(extraction)
            while x.lower() != 'b':
                print(chr(27) + "[2J")
                if x == '1':
                    x = input(categories)
                    while x.lower() != 'b':
                        print(chr(27) + "[2J")
                        processing = True
                        articles_ids = set()
                        event_type = ''
                        if x == '1':
                            articles_ids = document_type.DocumentTypeIndex(
                                wiki_accessor.WikiAccessor(directory)).getDocsOfType(
                                "war_event")
                            event_type = 'вооружённый конфликт'
                        elif x == '2':
                            articles_ids = document_type.DocumentTypeIndex(
                                wiki_accessor.WikiAccessor(directory)).getDocsOfType(
                                "terract_event")
                            event_type = 'террористическая атака'
                        elif x == '3':
                            articles_ids = document_type.DocumentTypeIndex(
                                wiki_accessor.WikiAccessor(directory)).getDocsOfType(
                                "revolution")
                            event_type = 'революция'
                        elif x == '4':
                            articles_ids = document_type.DocumentTypeIndex(
                                wiki_accessor.WikiAccessor(directory)).getDocsOfType(
                                "massacres")
                            event_type = 'массовые убийства'
                        elif x == '5':
                            articles_ids = document_type.DocumentTypeIndex(
                                wiki_accessor.WikiAccessor(directory)).getDocsOfType(
                                "meteorite")
                            event_type = 'метеорит'
                        elif x == '6':
                            articles_ids = document_type.DocumentTypeIndex(
                                wiki_accessor.WikiAccessor(directory)).getDocsOfType(
                                "earthquake")
                            event_type = 'землетрясение'
                        elif x == '7':
                            articles_ids = document_type.DocumentTypeIndex(
                                wiki_accessor.WikiAccessor(directory)).getDocsOfType(
                                "catastrophe")
                            event_type = 'катастрофа'
                        # elif x == '8':
                        #     articles_ids = document_type.DocumentTypeIndex(
                        #         wiki_accessor.WikiAccessor(directory)).getDocsOfType(
                        #         "un_document")
                        #     event_type = 'документ оон'
                        elif x == '8':
                            articles_ids = document_type.DocumentTypeIndex(
                                wiki_accessor.WikiAccessor(directory)).getDocsOfType(
                                "film_festival")
                            event_type = 'кинофестиваль'
                        elif x == '9':
                            articles_ids = document_type.DocumentTypeIndex(
                                wiki_accessor.WikiAccessor(directory)).getDocsOfType(
                                "conference")
                            event_type = 'конференция'
                        elif x == '10':
                            articles_ids = document_type.DocumentTypeIndex(
                                wiki_accessor.WikiAccessor(directory)).getDocsOfType(
                                "free_license")
                            event_type = 'карточка свободной лицензии'
                        else:
                            processing = False
                            print('Ошибочный ввод!')
                        if processing:
                            x = int(input('Введите количество событий: '))
                            clean_record_with_event_type_in_database(event_type)
                            i = 0
                            for id in articles_ids:
                                hwa.handle_article(id)
                                i += 1
                                if i >= x:
                                    break
                            break
                elif x == '2':
                    pass
                else:
                    print('Ошибочный ввод!')
                x = input(extraction)
        elif x == '2':
            print('\nДемонстрация.')
            x = input(categories)
            while x.lower() != 'b':
                print(chr(27) + "[2J")
                processing = True
                if x == '1':
                    events = get_events_for_category('вооружённый конфликт')
                elif x == '2':
                    events = get_events_for_category('террористическая атака')
                elif x == '3':
                    events = get_events_for_category('революции')
                elif x == '4':
                    events = get_events_for_category('массовые убийства')
                elif x == '5':
                    events = get_events_for_category('метеорит')
                elif x == '6':
                    events = get_events_for_category('землетрясение')
                elif x == '7':
                    events = get_events_for_category('катастрофа')
                # elif x == '8':
                #     events = get_events_for_category('документ оон')
                elif x == '8':
                    events = get_events_for_category('конференция')
                elif x == '9':
                    events = get_events_for_category('кинофестиваль')
                elif x == '10':
                    events = get_events_for_category('карточка свободной лицензии')
                else:
                    processing = False
                    print('Ошибочный ввод!')
                if processing:
                    if not len(events):
                        print('Нет событий с такой категорией.')
                    else:
                        min_str = 0
                        items_count = 5
                        max_str = int(round(len(events) / items_count, 0))
                        cur_str = 0
                        select_event = '(q - выйти, a - вперёд, b - назад)\nВыберите событие: '
                        select_event_first = '(q - выйти, a - вперёд)\nВыберите событие: '
                        select_event_end = '(q - выйти, b - назад)\nВыберите событие: '
                        while x.lower() != 'q':
                            print('\nСобытия:')
                            for i in range(items_count):
                                if i + cur_str * items_count < len(events):
                                    print('{0}. {1}'.format(i + 1, events[i + cur_str * items_count][1]))
                                else:
                                    break
                            if cur_str == min_str:
                                x = input(select_event_first)
                            elif cur_str == max_str - 1:
                                x = input(select_event_end)
                            else:
                                x = input(select_event)
                            if x == 'a' and cur_str < max_str - 1:
                                cur_str += 1
                            elif x == 'b' and cur_str > min_str:
                                cur_str -= 1
                            elif '1' <= x <= '5':
                                event = events[int(x) - 1 + cur_str * items_count]
                                print('\nНазвание:', event[1])
                                if event[2] == event[3]:
                                    print('Дата:', event[2].strftime("%d.%m.%Y"))
                                else:
                                    print('Дата начала: {0}\nДата окончания: {1}'.format(event[2].strftime("%d.%m.%Y"),
                                                                                         event[3].strftime("%d.%m.%Y")))
                                reasons = get_event_on_relationship('причина', event[0])
                                nested_events = get_event_on_relationship('часть', event[0])
                                major_events = get_event_on_relationship('основное событие', event[0])
                                consequences = get_event_on_relationship('следствие', event[0])
                                if len(reasons):
                                    print('Причины:')
                                    for i in range(len(reasons)):
                                        print('{0}. {1}'.format(i + 1, reasons[i][1][:120]))
                                        if reasons[i][2] == reasons[i][3]:
                                            print('Дата:', reasons[i][2])
                                        else:
                                            print('Дата начала: {0}; Дата окончания: {1}'.format(reasons[i][2].strftime("%d.%m.%Y"),
                                                                                                 reasons[i][3].strftime("%d.%m.%Y")))
                                if len(nested_events):
                                    print('Вложенные события:')
                                    for i in range(len(nested_events)):
                                        print('{0}. {1}'.format(i + 1, nested_events[i][1][:120]))
                                        if nested_events[i][2] == nested_events[i][3]:
                                            print('Дата:', nested_events[i][2])
                                        else:
                                            print('Дата начала: {0}; Дата окончания: {1}'.format(nested_events[i][2].strftime("%d.%m.%Y"),
                                                                                                 nested_events[i][3].strftime("%d.%m.%Y")))
                                if len(consequences):
                                    print('Следствия:')
                                    for i in range(len(consequences)):
                                        print('{0}. {1}'.format(i + 1, consequences[i][1][:120]))
                                        if consequences[i][2] == consequences[i][3]:
                                            print('Дата:', consequences[i][2])
                                        else:
                                            print('Дата начала: {0}; Дата окончания: {1}'.format(consequences[i][2].strftime("%d.%m.%Y"),
                                                                                                 consequences[i][3].strftime("%d.%m.%Y")))
                                if len(major_events):
                                    print('Основные события:')
                                    for i in range(len(major_events)):
                                        print('{0}. {1}'.format(i + 1, major_events[i][1][:120]))
                                        if major_events[i][2] == major_events[i][3]:
                                            print('Дата:', major_events[i][2])
                                        else:
                                            print('Дата начала: {0}; Дата окончания: {1}'.format(major_events[i][2].strftime("%d.%m.%Y"),
                                                                                                 major_events[i][3].strftime("%d.%m.%Y")))
                                print('Нажмите любую клавишу для продолжения...')
                                input()
                            else:
                                print('Ошибка ввода!')
                x = input(categories)
        else:
            print('Ошибочный ввод!')
        x = input(gen_menu)


if __name__ == "__main__":
    console_interface()
    # directory = "D:\\Git\\pywikitext-master\\indexes\\"
    # hwa = HandlerWikiArticle(directory)
    # accessor = wiki_accessor.WikiAccessor(directory)
    # # print(document_type.DocumentTypeIndex(
    # #                             wiki_accessor.WikiAccessor(directory)).getDocsOfType(
    # #                             "catastrophe"))
    # base = wiki_base_index.WikiBaseIndex(accessor)
    # titles = title_index.TitleIndex(accessor)
    # hwa.handle_article(5639375)
    # print(titles.getIdByTitle("Оползень в провинции Бадахшан (2014)"))
    # ids = base.getIds()
    # for id in ids:
    #     text_article = base.getTextArticleById(id)
    #     if text_article:
    #         name, date, event_type = hwa.get_info_from_template(text_article)
    #         if name and date:
    #             print(event_type)
    #             print(titles.getTitleArticleById(id))
    # print('\n')
    print('Successful!')
