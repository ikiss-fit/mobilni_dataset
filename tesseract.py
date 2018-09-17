import sys
from lxml import etree
from os import listdir
from os.path import isfile, join, abspath
import re


def parse_arguments():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-file', help='Path to input file.', required=True)
    parser.add_argument('-o', '--output-file', help='Path to output file.', required=True)
    args = parser.parse_args()
    return args


def get_bounding_box(line_tag):
    title = line_tag.attrib["title"]
    title_parts = title.split(";")
    bbox_part = title_parts[0]
    bbox_parts = bbox_part.split()
    bbox = (int(bbox_parts[1]), int(bbox_parts[2]), int(bbox_parts[3]), int(bbox_parts[4]))
    return bbox


def process_line(line_tag, output):
    text_line = etree.SubElement(output, "TextLine")

    bounding_box = get_bounding_box(line_tag)
    text = ""

    for span_tag in line_tag.iter():
        if "class" in span_tag.attrib and span_tag.attrib["class"] == "ocrx_word":
            if span_tag.text is not None:
                text += span_tag.text + " "

    text = text.rstrip()
    
    if len(text) > 0:
        line_coords = etree.SubElement(text_line, "Coords")
        line_coords.set("points", str(bounding_box))

        line_text_equiv = etree.SubElement(text_line, "TextEquiv")
        line_unicode = etree.SubElement(line_text_equiv, "Unicode")
        line_unicode.text = text


def process_paragraph(paragraph_tag, output):
    for span_tag in paragraph_tag.iter():
        if "class" in span_tag.attrib and span_tag.attrib["class"] == "ocr_line":
            process_line(span_tag, output)


def process_area(area_tag, output):
    text_region = etree.SubElement(output, "TextRegion")

    for p_tag in area_tag.iter():
        if "class" in p_tag.attrib and p_tag.attrib["class"] == "ocr_par":
            process_paragraph(p_tag, text_region)


def process(content):
    content = bytes(content.encode(encoding="utf16"))
    root = etree.fromstring(content)


    output_root = etree.Element("PcGts")    
    page = etree.SubElement(output_root, "Page")

    for div_tag in root.iter():
        if "class" in div_tag.attrib and div_tag.attrib["class"] == "ocr_carea":
            process_area(div_tag, page)

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
