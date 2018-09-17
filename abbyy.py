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


def process_line(text, output):
    text_line = etree.SubElement(output, "TextLine")

    line_coords = etree.SubElement(text_line, "Coords")
    line_coords.set("points", "None")

    line_text_equiv = etree.SubElement(text_line, "TextEquiv")
    line_unicode = etree.SubElement(line_text_equiv, "Unicode")
    line_unicode.text = text


def process_paragraph(lines, output):
    region = etree.SubElement(output, "TextRegion")

    for line in lines:
        process_line(line, region)


def process(original_content):
    html_tag_position = original_content.find("<html")
    if html_tag_position < 0:
        return None

    content = original_content[html_tag_position:]
    content = re.sub("&.*?;", "", content)

    content = bytes(content.encode(encoding="utf16"))

    parser = etree.XMLParser(recover=True)

    try:
        root = etree.fromstring(content, parser)
    except Exception as e:
        print(e)
        sys.exit(1)

    output_root = etree.Element("PcGts")    
    page = etree.SubElement(output_root, "Page")
    
    for element in root.iter():
        if element.tag == "p":
            lines = element.xpath("descendant-or-self::*/text()")
            process_paragraph(lines, page)

    return output_root


def main():
    args = parse_arguments()

    content = None
    with open(args.input_file, "r") as f:
        content = f.read()

    output = process(content)

    if output is not None:
        output_xml_string = str(etree.tostring(output, pretty_print=True).decode("utf-8"))

        with open(args.output_file, "w") as f:
            f.write(output_xml_string)

    return 0


if __name__ == "__main__":
    sys.exit(main())
