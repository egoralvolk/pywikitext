from html.parser import HTMLParser


class ParserDateInLead(HTMLParser):
    def error(self, message):
        pass

    def __init__(self):
        super(ParserDateInLead, self).__init__()
        self.buffer = ''
        self.need_to_catch = False
        self.terminals = {}
        self.fictitious_tag = True

    def handle_starttag(self, tag, attrs):
        if tag == 'y' or tag == 'd' or tag == 't' or tag == 'm' or tag == 'c' or tag == 'i':
            if self.fictitious_tag:
                self.fictitious_tag = False
                return

            self.need_to_catch = True
            for attr in attrs:
                if 'n' in attr[0]:
                    self.buffer = attr[0]

    def handle_endtag(self, tag):
        pass

    def handle_data(self, data):
        if self.need_to_catch:
            self.terminals[self.buffer] = data
            self.need_to_catch = False

    def get_terminals(self, html_text):
        self.feed(html_text)
        return self.terminals
