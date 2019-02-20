import sys
from lxml import etree
from os import listdir
from os.path import isfile, join, abspath
import re

from dataset import BoundingBox, Baseline


def parse_arguments():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-file', help='Path to input file.', required=True)
    parser.add_argument('-o', '--output-file', help='Path to output file.', required=True)
    args = parser.parse_args()
    return args


def get_part(name, parts):
    for part in parts:
        if part.strip().startswith(name):
            return part

    return None


def get_bounding_box_and_baseline(line_tag):
    bbox = None
    baseline = None

    title = line_tag.attrib["title"]
    title_parts = title.split(";")

    bbox_part = get_part("bbox", title_parts)
    if bbox_part is not None:
        bbox_parts = bbox_part.split()
        bbox = BoundingBox(start_x=int(bbox_parts[1]), start_y=int(bbox_parts[2]), end_x=int(bbox_parts[3]), end_y=int(bbox_parts[4]))

        baseline_part = get_part("baseline", title_parts)
        if baseline_part is not None:
            baseline_parts = baseline_part.split()

            baseline_slope = float(baseline_parts[1])
            baseline_offset = int(float(baseline_parts[2]))
            bbox_width = bbox.end.x - bbox.start.x

            baseline_y_start = bbox.end.y + baseline_offset
            baseline_y_end = int(bbox.end.y + baseline_offset + bbox_width * baseline_slope)

            baseline = Baseline(start_x=bbox.start.x, start_y=baseline_y_start, end_x=bbox.end.x, end_y=baseline_y_end)

    return bbox, baseline


def process_line(line_tag):
    text_line = etree.Element("TextLine")

    bounding_box, baseline = get_bounding_box_and_baseline(line_tag)
    text = ""

    for span_tag in line_tag.iter():
        if "class" in span_tag.attrib and span_tag.attrib["class"] == "ocrx_word":
            for text_element in span_tag.xpath("descendant-or-self::*/text()"):
                text += text_element + " "

    text = text.strip()
    
    if len(text) > 0:
        if bounding_box is not None:
            line_coords = etree.SubElement(text_line, "Coords")
            line_coords.set("points", bounding_box.get_xml_output())

        if baseline is not None:
            line_baseline = etree.SubElement(text_line, "Baseline")
            line_baseline.set("points", baseline.get_xml_output())

        line_text_equiv = etree.SubElement(text_line, "TextEquiv")
        line_unicode = etree.SubElement(line_text_equiv, "Unicode")
        line_unicode.text = text

        return text_line

    return None


def process_paragraph(paragraph_tag):
    lines = []

    for span_tag in paragraph_tag.iter():
        if "class" in span_tag.attrib and span_tag.attrib["class"] == "ocr_line":
            text_line = process_line(span_tag)
            if text_line is not None:
                lines.append(text_line)

    return lines


def process_area(area_tag):
    text_region = etree.Element("TextRegion")
    append = False

    for p_tag in area_tag.iter():
        if "class" in p_tag.attrib and p_tag.attrib["class"] == "ocr_par":
            lines = process_paragraph(p_tag)
            if len(lines) > 0:
                append = True
                for line in lines:
                    text_region.append(line)

    if append:
        return text_region

    return None


def process(content):
    content = bytes(content.encode(encoding="utf16"))
    root = etree.fromstring(content)

    output_root = etree.Element("PcGts")    
    page = etree.SubElement(output_root, "Page")

    for div_tag in root.iter():
        if "class" in div_tag.attrib and div_tag.attrib["class"] == "ocr_carea":
            text_region = process_area(div_tag)
            if text_region is not None:
                page.append(text_region)

    return output_root


def main():
    args = parse_arguments()

    content = None
    with open(args.input_file, "r") as f:
        content = f.read()

    output = process(content)
    output_xml_string = str(etree.tostring(output, pretty_print=True).decode("utf-8"))

    with open(args.output_file, "w") as f:
         f.write(output_xml_string)

    return 0


if __name__ == "__main__":
    sys.exit(main())
