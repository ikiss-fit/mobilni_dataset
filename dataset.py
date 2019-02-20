from os import listdir
from os.path import isfile, join
from typing import List, Dict, Optional
from numbers import Number
from lxml import etree


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        if isinstance(other, Point):
            return self.x == other.x and self.y == other.y

        return False

    def __str__(self):
        return "[x: " + str(self.x) + "; y: " + str(self.y) + "]"

    def get_tuple(self, offset_top=0, offset_left=0):
        return self.x + offset_left, self.y + offset_top

    def get_tuple_inverted(self):
        return (self.y, self.x)


class Rectangle:
    def __init__(self, **kwargs):
        self.start = None  # type: Point
        self.end = None  # type: Point
        self.inner_points = []  # type: List[Point]

        if "xml_string" in kwargs:
            if isinstance(kwargs["xml_string"], str):
                points = kwargs["xml_string"].split(" ")
                start_point = points[0].split(",")
                end_point = points[-1].split(",")
                inner_points = points[1:-1]

                if len(start_point) >= 2:
                    self.start = Point(int(start_point[0]), int(start_point[1]))
                else:
                    raise ValueError("Could not get 'start' point from string " + kwargs["xml_string"])

                if len(start_point) >= 2:
                    self.end = Point(int(end_point[0]), int(end_point[1]))
                else:
                    raise ValueError("Could not get 'end' point from string " + kwargs["xml_string"])

                for inner_point in inner_points:
                    x, y = inner_point.split(",")
                    self.inner_points.append(Point(int(x), int(y)))
        else:
            if "start" in kwargs:
                if isinstance(kwargs["start"], Point):
                    self.start = kwargs["start"]
                else:
                    raise ValueError("kwargs contains key 'start', but it is not of type 'Point'.")

            elif "start_x" in kwargs and "start_y" in kwargs:
                if isinstance(kwargs["start_x"], Number) and isinstance(kwargs["start_y"], Number):
                    self.start = Point(kwargs["start_x"], kwargs["start_y"])
                else:
                    raise ValueError("kwargs contains keys 'start_x' and 'start_y', but at least one of these is not of type 'Number'.")

            else:
                raise ValueError("kwargs does not contain neither key 'start' nor keys 'start_x' and 'start_y'.")

            if "end" in kwargs:
                if isinstance(kwargs["end"], Point):
                    self.end = kwargs["end"]
                else:
                    raise ValueError("kwargs contains key 'end', but it is not of type 'Point'.")

            elif "end_x" in kwargs and "end_y" in kwargs:
                if isinstance(kwargs["end_x"], Number) and isinstance(kwargs["end_y"], Number):
                    self.end = Point(kwargs["end_x"], kwargs["end_y"])
                else:
                    raise ValueError("kwargs contains keys 'end_x' and 'end_y', but at least one of these is not of type 'Number'.")

            elif "width" in kwargs and "height" in kwargs:
                if isinstance(kwargs["width"], Number) and isinstance(kwargs["height"], Number):
                    self.end = Point(self.start.x + kwargs["width"], self.start.y + kwargs["height"])
                else:
                    raise ValueError("kwargs contains keys 'width' and 'height', but at least one of these is not of type 'Number'.")

            else:
                raise ValueError("kwargs does not contain neither key 'end' nor keys 'end_x' and 'end_y' nor keys 'width' and 'height'.")

    def __str__(self):
        return "Start: " + str(self.start) + ", End: " + str(self.end)


class BoundingBox(Rectangle):
    def get_xml_output(self) -> str:
        if len(self.inner_points) > 0:
            inner_points_string = " ".join(["{x},{y}".format(x=p.x, y=p.y) for p in self.inner_points])
            return "{x1},{y1} {inner_points} {x2},{y2}".format(x1=self.start.x, y1=self.start.y, x2=self.end.x, y2=self.end.y, inner_points=inner_points_string)

        return "{x1},{y1} {x2},{y2}".format(x1=self.start.x, y1=self.start.y, x2=self.end.x, y2=self.end.y)

class Baseline(Rectangle):
    def get_xml_output(self) -> str:
        return str(self.start.x) + "," + str(self.start.y) + " " + str(self.end.x) + "," + str(self.end.y)

class Line:
    def __init__(self, text: str, bounding_box: Optional[BoundingBox], baseline: Optional[Baseline], confidence: Optional[Number]):
        self.text = text.strip()
        self.bounding_box = bounding_box
        self.baseline = baseline
        self.confidence = confidence

    def __str__(self):
        return self.text

    def __eq__(self, other):
        if isinstance(other, Line):
            return self.text == other.text

        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def get_xml_output(self) -> etree.ElementTree:
        text_line = etree.Element("TextLine")

        if self.confidence is not None:
            text_line.set("custom", "confidence:" + str(self.confidence) + ";")

        if self.bounding_box is not None:
            line_coords = etree.SubElement(text_line, "Coords")
            line_coords.set("points", self.bounding_box.get_xml_output())

        if self.baseline is not None:
            line_baseline = etree.SubElement(text_line, "Baseline")
            line_baseline.set("points", self.baseline.get_xml_output())

        line_text_equiv = etree.SubElement(text_line, "TextEquiv")
        line_unicode = etree.SubElement(line_text_equiv, "Unicode")
        line_unicode.text = self.text

        return text_line


class Page:
    def __init__(self, id: str, lines: List[Line]):
        self.id = id
        self.lines = lines

    def get_xml_output(self) -> etree.ElementTree:
        output = etree.Element("PcGts")
        page = etree.SubElement(output, "Page")

        for line in self.lines:
            text_region = etree.SubElement(page, "TextRegion")
            line_xml = line.get_xml_output()

            text_region.append(line_xml)

        return output

    def save(self, path: str) -> None:
        xml_output = self.get_xml_output()
        string_output = str(etree.tostring(xml_output, pretty_print=True).decode("utf-8"))

        filepath = join(path, self.id + ".xml")
        with open(filepath, "w") as f:
            f.write(string_output)


class Dataset:
    def __init__(self, path: str = None, lazy: bool = False):
        # self.pages: Dict[str, Page] = {}
        self.pages = {}  # type: Dict[str, Page]
        self.lazy = lazy # type: bool
        self.path = path # type: str

        if self.path is not None:
            if not self.lazy:
                page_list = self._load_pages()

                for page in page_list:
                    self.add_page(page)
            else:
                for page in self._get_dataset_files():
                    self.pages[page.split(".")[0]] = None

    def add_page(self, page: Page):
        self.pages[page.id] = page

    def get_page(self, id: str):
        if self.lazy:
            files = self._get_dataset_files(id)
            if len(files) > 0:
                return self._load_page(files[0])

            return None

        page = None

        try:
            page = self.pages[id]
        except:
            pass

        return page

    def _load_lines(self, content):
        lines = []
        content = bytes(content.encode(encoding="utf16"))

        parser = etree.XMLParser(recover=True)

        try:
            root = etree.fromstring(content, parser)
        except Exception as e:
            print(e)
            return None

        namespaces = root.nsmap
        namespace = ""

        try:
            namespace = namespaces[None]
        except:
            pass

        for element in root.iter():
            if element.tag == "TextLine" or element.tag == "{" + namespace + "}TextLine":
                text = element.xpath('*[local-name()="TextEquiv"]/Unicode/text()')
                coords = element.xpath('*[local-name()="Coords"]/@points')
                baseline = element.xpath('*[local-name()="Baseline"]/@points')

                try:
                    bounding_box = BoundingBox(xml_string=coords[0])
                except (ValueError, IndexError):
                    bounding_box = None

                try:
                    baseline = Baseline(xml_string=baseline[0])
                except (ValueError, IndexError):
                    baseline = None

                line_text = ""

                if len(text) > 0:
                    line_text = text[0]

                lines.append(Line(line_text, bounding_box, baseline, None))

        return lines

    def _load_page(self, filename):
        id = filename[:filename.rindex(".xml")]

        content = None
        with open(join(self.path, filename), "r") as f:
            content = f.read()

        lines = self._load_lines(content)

        return Page(id, lines)

    def _get_dataset_files(self, prefix=""):
        return [f for f in listdir(self.path) if isfile(join(self.path, f)) and f.startswith(prefix) and f.endswith(".xml")]

    def _load_pages(self):
        files = self._get_dataset_files()
        pages = []

        for filename in files:
            pages.append(self._load_page(filename))

        return pages

    def __str__(self):
        output = ""

        output += "Pages: " + str(len(self.pages)) + "\n"
        output += "Lines: " + str(sum([len(page.lines) for page in self.pages.values() if page is not None]))

        if self.lazy:
            output += " (LAZY LOADED)"

        output += "\nID samples: " + str(list(self.pages.keys())[:4])

        return output

    def save(self, path: str) -> None:
        for page_id, page in self.pages.items():
            page.save(path)

    def get_lengths(self) -> List[int]:
        lengths = []

        for page_id, _ in self.pages.items():
            lengths.append(len(self.get_page(page_id).lines))

        return lengths

    def get_statistics(self) -> Dict[str, object]:
        statistics = {"lengths": self.get_lengths()}

        return statistics

    def count_lines(self):
        number_of_lines = 0

        if self.lazy:
            number_of_lines = sum([len(self.get_page(page).lines) for page in self.pages.keys()])
        else:
            number_of_lines = sum([len(page.lines) for page in self.pages.values() if page is not None])

        return number_of_lines
