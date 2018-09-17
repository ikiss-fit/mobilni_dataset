from lxml import etree
from os import listdir
from os.path import isfile, join, abspath
import re
from typing import List, Dict


class Line():
    def __init__(self, text, bounding_box, confidence):
        self.text = text.strip()
        self.bounding_box = bounding_box
        self.confidence = confidence

    def __str__(self):
        return self.text

    def __eq__(self, other):
        if isinstance(other, Line):
            return self.text == other.text

        return False

    def __ne__(self, other):
        return not self.__eq__(other)


class Page():
    def __init__(self, id: str, lines: List[Line]):
        self.id = id
        self.lines = lines


class Dataset():
    def __init__(self, path: str = None):
        # self.pages: Dict[str, Page] = {}
        self.pages = {} # type: Dict[str, Page]

        if path is not None:
            page_list = self._load_pages(path)

            for page in page_list:
                self.add_page(page)


    def add_page(self, page: Page):
        self.pages[page.id] = page


    def _load_lines(self, content):
        lines = []
        content = bytes(content.encode(encoding="utf16"))

        parser = etree.XMLParser(recover=True)

        try:
            root = etree.fromstring(content, parser)
        except Exception as e:
            print(e)
            return None
        
        for element in root.iter():
            if element.tag == "TextLine":
                text = element.xpath("TextEquiv/Unicode/text()")
                coords = element.xpath("Coords/@points")

                if len(text) > 0 and len(coords) > 0:
                    lines.append(Line(text[0], coords[0], None))

        return lines

    
    def _load_page(self, path, filename):
        id = filename[:filename.rindex(".xml")]

        content = None
        with open(join(path, filename), "r") as f:
            content = f.read()

        lines = self._load_lines(content)

        return Page(id, lines)


    def _load_pages(self, path):
        files = [f for f in listdir(path) if isfile(join(path, f)) and f.endswith(".xml")]
        pages = []

        for filename in files:
            pages.append(self._load_page(path, filename))

        return pages

    
    def __str__(self):
        output = ""

        output += "Pages: " + str(len(self.pages)) + "\n"
        output += "Lines: " + str(sum([len(page.lines) for page in self.pages.values()]))

        return output
        
